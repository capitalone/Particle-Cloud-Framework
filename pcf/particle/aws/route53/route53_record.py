# Copyright 2018 Capital One Services, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pcf.core.aws_resource import AWSResource
from pcf.core import State
from pcf.particle.aws.ec2.ec2_instance import EC2Instance
from pcf.util import pcf_util
import logging
import json
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)


class Route53Record(AWSResource):
    """
    Particle that maps to AWS route53 record set. Before using this particle make sure that you have created a hosted zone in AWS.

    Required Parameters:

    :param Name: the name of your record set
    :param HostedZoneId: the  hosted zone you want you record set to be in
    :param ResourceRecords: list of your resource records
    :param Type: type of your resource records
    :type Name: string
    :type HostedZoneId: string
    :type ResourceRecords: object list
    :type Type: string
    """
    flavor='route53_record'

    REMOVE_PARAM_CONVERSIONS = {
        "HostedZoneId": "",
    }

    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0,
    }

    UNIQUE_KEYS = ["aws_resource.Name"]

    def __init__(self,particle_definition, session=None):
        """
        :param particle_definition:
        """
        super().__init__(particle_definition, 'route53', session=session)
        if not self.desired_state_definition.get('Name').endswith('.'):
            self.desired_state_definition['Name'] = self.desired_state_definition['Name'] + '.'
        self.record_name = self.desired_state_definition['Name']
        self.hosted_zone = self.desired_state_definition['HostedZoneId']

        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the Route53 Record

        """
        self.unique_keys = Route53Record.UNIQUE_KEYS

    def get_status(self):
        """
        Get the current status of your route 53 record set

        :return: list of record sets sorted by record name
        """
        try:
            service_status_resp = self.client.list_resource_record_sets(HostedZoneId=self.hosted_zone,StartRecordName=self.record_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == 'NoSuchHostedZone':
                return []
        else:
            return service_status_resp.get('ResourceRecordSets', [])

    def sync_state(self):
        """
        Sync state calls get_status to determines and set the state of the route53 record set particle.
        """
        full_status = self.get_status()
        if len(full_status) == 0:
            self.state = State.terminated
            self.current_state_definition = {}
        else:
            self.current_state_definition = full_status[0] ##returns first item in ResourceRecordSets, if record_name exists then it would be in index 0
            if full_status[0].get('Name') == self.record_name:
                self.state = State.running
            else:
                self.state = State.terminated

    def _terminate(self):
        """
        Deletes the route53 record set that matches current state definition

        :return: response of boto3 change resource record set with action DELETE
        """
        change_entry = {
            'Action':'DELETE',
            'ResourceRecordSet':self.current_state_definition,
        }
        change_batch = {
            'Changes':[change_entry],
        }
        return self.client.change_resource_record_sets(HostedZoneId=self.hosted_zone,ChangeBatch=change_batch)

    def _start(self):
        """
        Creates the route53 record set that matches current state definition

        :return: response of boto3 change resource record set with action CREATE
        """
        desired_state_def = self.get_desired_state_definition()

        if not list(desired_state_def.get("ResourceRecords")):
            return None

        start_definition = pcf_util.keep_and_remove_keys(desired_state_def, Route53Record.REMOVE_PARAM_CONVERSIONS)

        change_entry = {
            'Action':'CREATE',
            'ResourceRecordSet':start_definition,
        }

        #TTL, Name including zone ending, type required
        change_batch = {
            'Changes':[change_entry],
        }
        return self.client.change_resource_record_sets(HostedZoneId=self.hosted_zone,ChangeBatch=change_batch)


    def _stop(self):
        """
        Route53 record set does not have a stopped state so it calls terminate
        :return: terminate()
        """
        return self._terminate()

    def _update(self):
        """
        Updates the route53 record set that matches current state definition

        :return: response of boto3 change resource record set with action UPSERT
        """
        desired_state_def = self.get_desired_state_definition()

        if not list(desired_state_def.get("ResourceRecords")):
            return None

        update_definition = pcf_util.keep_and_remove_keys(desired_state_def, Route53Record.REMOVE_PARAM_CONVERSIONS)

        change_entry = {
            'Action':'UPSERT',
            'ResourceRecordSet':update_definition,
        }
        change_batch = {
            'Changes':[change_entry],
        }
        return self.client.change_resource_record_sets(HostedZoneId=self.hosted_zone,ChangeBatch=change_batch)

    def is_state_equivalent(self, state1, state2):
        """
        Determines if states are equivalent
        :param state1:
        :param state2:
        :type: state1: State
        :type: state2: State

        :return: bool
        """
        return Route53Record.equivalent_states.get(state1) == Route53Record.equivalent_states.get(state2)

    def is_state_definition_equivalent(self):
        """
        Determines if the current state definition matches the current state definition. Uses keep and remove function from pcf util to remove extra params in desired state that are not
        in the current state.

        :return: bool
        """
        self.get_state()
        diff = pcf_util.diff_dict(self.current_state_definition, pcf_util.keep_and_remove_keys(self.get_desired_state_definition(), Route53Record.REMOVE_PARAM_CONVERSIONS))

        if not diff or len(diff) == 0:
            return True
        elif self.state == State.terminated:
            return True
        else:
            logger.debug("State is not equivalent for {0} with diff: {1}".format(self.get_pcf_id(), json.dumps(diff)))
            return False

    def get_desired_state_definition(self):
        """
        Returns the desires state definition. If Route53 Record has parents that are EC2 instances then ip addresses of those instances are automatically added to the resource_records in the
        desired state definition.

        :return: desired_state_definition
        """
        record_type = self.desired_state_definition.get("Type")
        if record_type == "A" and len(self.parents) > 0:
            ec2_instance_parents = list(filter(lambda x: isinstance(x, EC2Instance), self.parents))

            if len(ec2_instance_parents) > 0:
                resource_records = list(self.desired_state_definition.get("ResourceRecords"))
                existing_records = set(x["Value"] for x in resource_records)

                for ec2_instance in ec2_instance_parents:
                    ec2_instance.sync_state()
                    ec2_ip = ec2_instance.get_attribute_value("PrivateIpAddress")
                    if ec2_ip not in existing_records:
                        resource_records.append({"Value": ec2_ip})

                return {**self.desired_state_definition, "ResourceRecords": resource_records}
            else:
                return self.desired_state_definition

        else:
            return self.desired_state_definition

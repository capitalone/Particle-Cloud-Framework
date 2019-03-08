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
from pcf.util import pcf_util
from jinja2 import Template
from pcf.core.pcf_exceptions import *
import base64
import logging
import pkg_resources
from pcf.util.aws.tag_specifications import EC2InstanceTagSpecifications

logger = logging.getLogger(__name__)


class EC2Instance(AWSResource):
    """This is the EC2 particle. There are a variety of possible states for this particle which can be seen in the
    state lookup dictionary. There are also specific input requirements for the various commands which can be seen
    in the different PARAM_CONVERSIONS. """
    flavor = "ec2_instance"
    state_lookup = {
        "running": State.running,
        "terminated": State.terminated,
        "stopped": State.stopped,
        "missing": State.terminated,
        "stopping": State.pending,
        "shutting-down": State.pending,
        "pending": State.pending
    }
    equivalent_states = {}

    START_PARAM_FILTER = {
        "BlockDeviceMappings",
        "ImageId",
        "InstanceType",
        "KeyName",
        "MaxCount",
        "MinCount",
        "UserData",
        "SecurityGroupIds",
        "SubnetId",
        "IamInstanceProfile",
        "InstanceInitiatedShutdownBehavior",
        "TagSpecifications"
    }

    STATE_PARAM_FILTER = {
        #"BlockDeviceMappings",
        "ImageId",
        "InstanceType",
        "KeyName",
        #"MaxCount",
        #"MinCount",
        "UserData",
        "SecurityGroupIds",
        "SubnetId",
        "IamInstanceProfile",
        "InstanceInitiatedShutdownBehavior",
        "TagSpecifications"
    }

    EBS_PARAM_CONVERSIONS = {
        "DeleteOnTermination": "",
        "SnapshotId": "",
        "VolumeSize": "Size",
        "VolumeType": "",
        "Iops": ""
    }

    UNIQUE_KEYS = ["aws_resource.custom_config.instance_name"]

    def __init__(self, particle_definition):
        super(EC2Instance, self).__init__(particle_definition, "ec2")

        self.instance_name = self.desired_state_definition.get("custom_config").get("instance_name")

        if not self.instance_name:
            tags = self.desired_state_definition.get("custom_config").get("tags")
            self.instance_name = tags.get("PCFName")

        if not self.instance_name: raise Exception("EC2Instance must have 'instance_name' defined")

        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the EC2 instance

        """
        self.unique_keys = EC2Instance.UNIQUE_KEYS

    def render_desired_user_data(self):
        """
        Opens the userdata template file and renders the file with userdata parameters.

        Returns:
            userdate
        """
        userData = self.desired_state_definition.get("UserData", None)
        if userData:
            return userData
        else:
            template_filename = self.desired_state_definition.get("custom_config").get("userdata_template_file", None)

            if template_filename:
                context = self.desired_state_definition.get("custom_config").get("userdata_params", {})
                template = Template(
                    open(template_filename, 'r').read()
                )

                userdata = template.render(context)
                return userdata
            else:
                return "#No userdata provided"

    def _get_instance_reservations(self):
        """
        Uses instance_name as a filter for boto3 describe_instances()

        Returns:
             boto3 describe_instances() response
        """
        filters = [{
            'Name': 'tag:PCFName',
            'Values': [self.instance_name]
        },
            {
                'Name': 'instance-state-name',
                'Values': ['pending','running','shutting-down','stopping','stopped']
            }
        ]
        return self.client.describe_instances(Filters=filters)['Reservations']

    def get_instance_id(self):
        """
        Returns:
             get_identifier()
        """
        return self.get_identifier()

    def get_label(self):
        """
        Returns:
             instance_name
        """
        return self.instance_name

    def get_identifier(self):
        """
        Uses arn to return instance id.

        Returns:
             instance_id
        """
        return _get_instance_id_from_arn(self.arn)

    def _get_arn(self):
        """
        Calls _get_instance_reservations() to get ecs reservations. Parses reservations and returns inputs for
        _construct_arn() which returns the EC2 arn.

        Returns:
             _construct_arn()
        """
        reservations = self._get_instance_reservations()
        instances = sum([r.get('Instances', []) for r in reservations], [])
        if len(instances) == 1:
            instance_id = instances[0]['InstanceId']
            instance_reservation = [r
                                    for r
                                    in reservations
                                    if r['Instances'] and r['Instances'][0]['InstanceId'] == instance_id
                                    ][0]

            return _construct_arn(
                region_name=self.client.meta.region_name,
                owner_id=instance_reservation['OwnerId'],
                instance_id=instance_id,
            )

        elif len(instances) < 1:
            raise NoResourceException
        else:
            raise TooManyResourceException

    def get_current_definition(self):
        """
        Calls boto3 describe_instances. Adds some fields that are required for matching desired state such as Userdata hash,
        TagSpecifications, and InstanceInitiatedShutdownBehavior

        Returns:
            state definition
        """
        definition = self.client.describe_instances(
            InstanceIds=[self.get_instance_id()]
        )['Reservations'][0]['Instances'][0]
        user_data_resp = self.client.describe_instance_attribute(InstanceId=self.get_instance_id(), Attribute='userData')
        if not user_data_resp["UserData"]["Value"]=='None': #for moto
                definition['UserData'] = base64.b64decode(user_data_resp["UserData"]["Value"]).decode(encoding='utf-8')
        definition['TagSpecifications'] = [{'ResourceType': 'instance','Tags':self.resource.Instance(self.get_instance_id()).tags}]

        # for moto tests to work
        try:
            definition['InstanceInitiatedShutdownBehavior'] = self.resource.Instance(self.get_instance_id()).describe_attribute(Attribute='instanceInitiatedShutdownBehavior')['InstanceInitiatedShutdownBehavior']['Value']
        except Exception as e:
            definition['InstanceInitiatedShutdownBehavior'] = self.desired_state_definition.get('InstanceInitiatedShutdownBehavior','')

        security_group_ids = []
        for security_group in self.resource.Instance(self.get_instance_id()).security_groups:
            security_group_ids.append(security_group['GroupId'])
        definition['SecurityGroupIds'] = security_group_ids

        return definition

    def get_desired_state_definition(self):
        """
        Adds some custom field to the user given desired_state_file. These are UserData (rendered version)
        and TagSpecifications

        Returns:
           desired_state_definition
        """
        self.desired_state_definition["UserData"] = self.render_desired_user_data()

        userdata_bash = self.desired_state_definition.get("custom_config").get("userdata_bash")
        userdata_wait = self.desired_state_definition.get("custom_config").get("userdata_wait")

        if userdata_wait:
            self.desired_state_definition["UserData"] = "#!/bin/bash\n" + \
                                                        self.desired_state_definition["UserData"] + \
                                                        "\naws ec2 create-tags --region $(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | grep region | cut -d\\\" -f4) --resources $(curl -s http://169.254.169.254/latest/meta-data/instance-id) --tags Key=UserdataFinished,Value=True\n"

        if userdata_bash and not userdata_wait:
            self.desired_state_definition["UserData"] = "#!/bin/bash\n" + \
                                                        self.desired_state_definition["UserData"]

        tags = self.desired_state_definition["custom_config"].get("tags", {})
        tag_spec = EC2InstanceTagSpecifications(PCFName=self.get_label(), **tags)

        self.desired_state_definition["TagSpecifications"] = tag_spec.render()

        return self.desired_state_definition

    def _terminate(self):
        """
        Calls boto3 delete_tags() and terminate_instances

        Returns:
           boto3 terminate_instances() response
        """
        self.client.delete_tags(
            Resources=[self.get_instance_id()], Tags=[{'Key': 'PCFName'}]
        )
        resp = self.client.terminate_instances(InstanceIds=[self.get_instance_id()])
        return resp

    def create(self):
        """
        Calls boto3 create_instances(). This is called for terminated to running state transition.

        Returns:
           boto3 create_instances() response
        """
        create_definition = pcf_util.param_filter(self.get_desired_state_definition(), EC2Instance.START_PARAM_FILTER)
        return self.resource.create_instances(**create_definition)

    def _start(self):
        """
        Calls boto3 start_instances(). This is called for stopped to running state transition.

        Returns:
           boto3 start_instances() response
        """
        try:
            instance_id = self.get_instance_id()
        except TooManyResourceException:
            raise TooManyResourceException()
        except NoResourceException:
            return self.create()

        if self.state == State.stopped:
            return self.client.start_instances(InstanceIds=[instance_id])

    def _stop(self):
        """
        Calls boto3 stop_instances().

        Returns:
           boto3 stop_instances() response
        """
        return self.client.stop_instances(InstanceIds=[self.get_instance_id()])

    def sync_state(self):
        """
        Calls get_current_definition() and updates the current_state_definition and the state.
        """
        try:
            self.current_state_definition = self.get_current_definition()
        except NoResourceException:
            self.state = EC2Instance.state_lookup.get('missing')
        else:
            if self.desired_state_definition["custom_config"].get("userdata_wait"):
                tags = self.client.describe_tags(
                    Filters=[
                        {
                            'Name': 'resource-id',
                            'Values': [
                                self.get_instance_id(),
                            ]
                        },
                    ],
                )

                userdata_finished = None
                for tag in tags["Tags"]:
                    if tag["Key"] == 'UserdataFinished':
                        userdata_finished = tag["Value"]
                        break

                if userdata_finished:
                    self.state = EC2Instance.state_lookup[self.current_state_definition['State']['Name']]
                else:
                    self.state = EC2Instance.state_lookup['pending']

            else:
                self.state = EC2Instance.state_lookup[self.current_state_definition['State']['Name']]

    def _update(self):
       #TODO: This needs to be implemented
        raise NotImplementedError

    def is_state_definition_equivalent(self):
        logger.debug("is_state_definition_equivalent and _update are not implemented for {0}".format(self.get_pcf_id()))
        return True
        #TODO: This needs to be updated along with the _update implementation
        # self.sync_state()
        # filtered_current_state_definition = pcf_util.param_filter(self.current_state_definition,
        #                                                             EC2Instance.STATE_PARAM_FILTER)
        # filtered_desired_state_definition = pcf_util.param_filter(self.desired_state_definition,
        #                                                             EC2Instance.STATE_PARAM_FILTER)
        # diff = pcf_util.diff_dict(filtered_current_state_definition, filtered_desired_state_definition)
        #
        # if not diff or len(diff) == 0:
        #     return True
        # else:
        #     logger.debug("State is not equivalent for {0} with diff: {1}".format(self.get_pcf_id(), json.dumps(diff)))
        #     return False

def _construct_arn(owner_id, region_name, instance_id):
    """
    Args:
        owner_id (str): owner id
        region_name (str) : region that EC2 is deployed
        instance_id (str) : instance on of the EC2

    Returns:
        EC2 arn
    """
    return 'arn:aws:ec2:{region}:{owner}:instance/instance-id/{instance_id}'.format(
        region=region_name,
        owner=owner_id,
        instance_id=instance_id,
    )

def _get_instance_id_from_arn(arn):
    """
    Parses the arn to return only the instance id

    Args:
        arn (str) : EC2 arn

    Returns:
        EC2 Instance id
    """
    return arn.split('/')[-1]

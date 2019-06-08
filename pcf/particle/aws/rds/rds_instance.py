import logging
import json
import time

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


from pcf.core import State
from pcf.core.aws_resource import AWSResource
from pcf.util import pcf_util

from botocore.errorfactory import ClientError

logger = logging.getLogger(__name__)

class RDS(AWSResource):

    """
    Particle that maps to AWS RDS Instance.

    Required Parameters:

    :param DBInstanceIdentifier: The DB instance identifier.
    :param DBInstanceClass: The compute and memory capacity of the DB instance, for example, db.m4.large .
    :param Engine: The name of the database engine to be used for this instance.
    :type DBInstanceIdentifier: string
    :type DBInstanceClass: string
    :type Engine: string

    """
    flavor = "rds_instance"
    state_lookup = {
        "available": State.running,
        "starting": State.pending,
        "creating": State.pending,
        "deleting": State.pending,
        "backing-up": State.pending,
        "modifying": State.pending,
        "renaming": State.pending,
        "rebooting": State.pending,
        "maintenance": State.pending,
        "upgrading": State.pending,
        "resetting-master-credentials": State.pending,
        "stopping": State.pending,
        "stopped": State.stopped,
        "missing": State.terminated,
    }
    START_PARAM_FILTER = {
        "DBInstanceIdentifier",
        "DBName",
        "AllocatedStorage",
        "DBInstanceClass",
        "MasterUsername",
        "MasterUserPassword",
        "Engine",
        "EngineVersion",
        "VpcSecurityGroupIds",
        "AvailabilityZone",
        "DBSubnetGroupName",
        "Port",
        "BackupRetentionPeriod",
        "KmsKeyId",
        "StorageEncrypted",
        "MultiAZ",
        "DBParameterGroupName",
        "Tags",
    }

    UPDATE_PARAM_FILTER = {
        "DBInstanceIdentifier",
        "AllocatedStorage",
        "DBInstanceClass",
        "EngineVersion",
        "BackupRetentionPeriod",
        "ApplyImmediately",
        # "SkipFinalSnapshot",
        # "DBParameterGroupName",
    }

    UNIQUE_KEYS = ["aws_resource.DBInstanceIdentifier"]

    def __init__(self, particle_definition, session=None):
        """
        :param particle_definition:
        """
        super().__init__(particle_definition, 'rds', session=session)
        self.db_instance_identifier = self.desired_state_definition['DBInstanceIdentifier']

        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the RDS Instance

        """
        self.unique_keys = RDS.UNIQUE_KEYS

    def get_status(self):
        """
        Get the current status of your rds instance.

        :return: status of rds instance.
        """
        try:
            rds_statuses = self.client.describe_db_instances(DBInstanceIdentifier=self.db_instance_identifier)['DBInstances']
        except ClientError as e:
            error_code = e.response.get('ResponseMetadata', {}).get('HTTPStatusCode')

            if error_code == 404 or error_code == 400:
                return {"DBInstanceStatus":"missing"}
            else:
                raise e
        else:
            return rds_statuses[0]

    def _terminate(self):
        """
        Deletes the rds instance that matches current state definition

        :return: response of boto3 terminate resource rds instance with action delete_db_instance.
        """
        return self.client.delete_db_instance(DBInstanceIdentifier=self.db_instance_identifier, SkipFinalSnapshot=True)

    def create(self):
        """
        Creates the rds instance that matches current state definition

        :return: response of boto3 create rds instance with action create_db_instance.
        """
        create_def = pcf_util.param_filter(self.desired_state_definition, RDS.START_PARAM_FILTER)
        return self.client.create_db_instance(**create_def)

    def _start(self):
        """
        starts the stopped rds instance that matches current state definition

        :return: response of boto3 start rds instance with action start_db_instance.
        """
        try:
            return self.client.start_db_instance(DBInstanceIdentifier=self.db_instance_identifier)
        except Exception as e:
            self.create()

    def _stop(self):
        """
        Stops the rds instance that matches current state definition

        :return: response of boto3 stop rds instance with action stop_db_instance.
        """
        return self.client.stop_db_instance(DBInstanceIdentifier=self.db_instance_identifier)

    def sync_state(self):
        """
        Sync state calls get_status to determines and set the state of the rds instance particle.
        """
        full_status = self.get_status()
        if full_status:
            status = full_status.get('DBInstanceStatus').lower()
            self.state = RDS.state_lookup.get(status)
            self.current_state_definition = full_status

    def _update(self):
        """
        Updates the rds instance that matches current state definition

        :return: response of boto3 change rds instance with modify_db_instance.
        """
        update_def = pcf_util.param_filter(self.desired_state_definition, RDS.UPDATE_PARAM_FILTER)
        return self.client.modify_db_instance(**update_def)

    def is_state_definition_equivalent(self):
        """
        Determines if the current state definition matches the desired state definition.

        :return: bool
        """
        self.sync_state()
        filtered_current_state_definition = pcf_util.param_filter(self.current_state_definition, RDS.UPDATE_PARAM_FILTER)
        filtered_desired_state_definition = pcf_util.param_filter(self.desired_state_definition, RDS.UPDATE_PARAM_FILTER)
        filtered_current_state_definition['ApplyImmediately'] = self.desired_state_definition['ApplyImmediately']
        filtered_current_state_definition['SkipFinalSnapshot'] = self.desired_state_definition['SkipFinalSnapshot']

        diff = pcf_util.diff_dict(filtered_current_state_definition, filtered_desired_state_definition)

        if not diff or len(diff) == 0:
            return True
        else:
            logger.debug("State is not equivalent for {0} with diff: {1}".format(self.get_pcf_id(), json.dumps(diff)))
        return False

    # def wait(self):
    #     time.sleep(30)



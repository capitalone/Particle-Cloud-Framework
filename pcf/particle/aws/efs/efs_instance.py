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
from pcf.util import pcf_util
from pcf.core.aws_resource import AWSResource
from pcf.core.pcf_exceptions import *
import logging

logger = logging.getLogger(__name__)

class EFSInstance(AWSResource):
    """
    This is the implementation of Amazon's Elastic File System.
    """

    flavor = "efs_instance"

    state_lookup = {
        "creating": State.pending,
        "deleting": State.pending,
        "available": State.running,
        "deleted": State.terminated
    }

    START_PARAM_FILTER = {
        "CreationToken",
        "PerformanceMode",
        "Encrypted",
        "KmsKeyId",
    }

    RETURN_PARAM_FILTER = {
        "OwnerId",
        "CreationToken",
        "FileSystemId",
        "Name",
        "PerformanceMode",
        "Encrypted",
        "KmsKeyId"
    }

    UNIQUE_KEYS = ["aws_resource.custom_config.instance_name"]

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition, "efs", session=session)
        self.instance_name = self.desired_state_definition.get('custom_config').get('instance_name')
        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the S3 Bucket
        """
        self.unique_keys = EFSInstance.UNIQUE_KEYS

    def get_status(self):
        """
        Gets current status of the EFS instance
        Returns:
             status (dict)
        """
        try:
            current_definition = self._describe_file_systems()
        except NoResourceException:
            logger.info("File System {} was not Found. State is terminated".format(self.instance_name))
            return {"status": "missing"}
        except TooManyResourceException as e:
            raise e
        return current_definition

    def sync_state(self):
        """
        Elastic File System implementation of sync state. Calls get status and sets the current state
        """
        status_def = self.get_status()
        if status_def.get("status") == "missing":
            self.state = State.terminated
            return
        self.current_state_definition = status_def
        self.state = self.state_lookup[self.current_state_definition["LifeCycleState"]]

    def _terminate(self):
        """
        Calls boto3 delete_file_system

        Returns:
            response of boto3 delete_file_system
        """
        return self.client.delete_file_system(FileSystemId=self.current_state_definition['FileSystemId'])

    def _start(self):
        """
        Calls boto3 create_file_system https://boto3.readthedocs.io/en/latest/reference/services/efs.html#EFS.Client.create_file_system
        Returns:
           boto3 create_file_system() response
        """
        new_desired_state_def, diff_dict = pcf_util.update_dict(
            self.current_state_definition,
            self.get_desired_state_definition()
        )
        create_definition = pcf_util.param_filter(new_desired_state_def, EFSInstance.START_PARAM_FILTER)

        res = self.client.create_file_system(**create_definition)
        self.client.create_tags(FileSystemId=res['FileSystemId'], Tags=[{'Key': 'Name', 'Value': self.instance_name}])
        return res

    def _stop(self):
        """
        Elastic File System does not have a stopped state so calls terminate
        """
        return self._terminate()

    def _update(self):
        if self.is_state_definition_equivalent() is False:
            raise InvalidUpdateParamException()

    def is_state_definition_equivalent(self):
        """
        Compares the desired state and current state definitions.

        Returns:
            bool
        """
        self.get_state()
        desired_definition = pcf_util.param_filter(self.desired_state_definition, EFSInstance.RETURN_PARAM_FILTER)
        new_desired_state_def, diff_dict = pcf_util.update_dict(self.current_state_definition, desired_definition)
        return diff_dict == {}

    def _describe_file_systems(self):
        """
        Uses instance_name as a filter for boto3 describe_file_systems()

        Returns:
             boto3 describe_file_systems() response
        """
        counter = 0
        dict = {}
        for fileSystem in self.client.describe_file_systems().get("FileSystems", []):
            if fileSystem["Name"] == self.instance_name:
                dict = fileSystem
                counter += 1

        if counter == 0:
            raise NoResourceException
        elif counter > 1:
            raise TooManyResourceException
        else:
            return dict

    def create_tags(self, fs_tags):
        """
        Creates or overwrites tags associated with file system
        Args:
            fs_tags (list): Array of Tag objects to add, each object is a key-value pair
        """
        self.client.create_tags(FileSystemId=self.current_state_definition['FileSystemId'], Tags=fs_tags)

    def describe_tags(self):
        """
        Returns the tags associated with the file system

        Returns:
            boto3 describe_tags() response
        """
        return self.client.describe_tags(FileSystemId=self.current_state_definition['FileSystemId'])['Tags']

    def delete_tags(self, tag_keys):
        """
        Deletes the specified tags from a file system

        Args:
            tag_keys(list): List of tag keys to delete
        """
        self.client.delete_tags(FileSystemId=self.current_state_definition['FileSystemId'], TagKeys=tag_keys)

    def create_mount_target(self, subnet_id, **kwargs):
        """
        Creates a mount target for a file system

        Args:
            subnet_id (string): ID of the subnet to add the mount target in
            **kwargs: options for boto3 create_mount target

        Returns:
            response of boto3 create_mount_target
        """
        return self.client.create_mount_target(FileSystemId=self.current_state_definition['FileSystemId'], SubnetId=subnet_id, **kwargs)

    def delete_mount_target(self, mount_target_id):
        """
        Deletes the specified mount target

        Args:
             mount_target_id (string): ID of the mount target to delete
        Returns:
            response of boto3 delete_mount_target
        """
        return self.client.delete_mount_target(MountTargetId=mount_target_id)

    def describe_mount_targets(self):
        """
        Returns the descriptions of all the current mount targets, or a specific mount target, for the file system

        Args:
            mount_target_id(string): ID of the mount target that you want to have described
            **kwargs: options for boto3 describe_mount_targets
        Returns:
            response of boto3 describe_mount_targets
        """
        return self.client.describe_mount_targets(FileSystemId=self.current_state_definition['FileSystemId'])['MountTargets']

    def modify_mount_target_security_groups(self, mount_target_id, security_groups):
        """
        Modifies the set of security groups in effect for a mount target

        Args:
            mount_target_id(string): ID of the mount target whose security groups you want to modify
            security_groups(list): Array of VPC security group IDs
        Returns:
            reponse of boto3 modify_mount_target_security_groups
        """
        return self.client.modify_mount_target_security_groups(MountTargetId=mount_target_id, SecurityGroups=security_groups)

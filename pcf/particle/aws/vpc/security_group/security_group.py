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
from pcf.core.pcf_exceptions import InvalidConfigException


class SecurityGroup(AWSResource):
    """
    This is the implementation of Amazon's Security Groups
    """

    flavor = "security_group"

    state_lookup = {
        "available": State.running,
        "pending": State.pending,
        "missing": State.terminated
    }
    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0
    }

    START_PARAMS = {
        "Description",
        "GroupName",
        "VpcId",
        "DryRun"
    }

    DEFINITION_FILTER = {
        "Description",
        "GroupName",
        "VpcId",
        "DryRun",
        "custom_config"
    }

    UNIQUE_KEYS = ["aws_resource.GroupName"]

    def __init__(self, particle_definition):
        super().__init__(particle_definition, "ec2")
        self._set_unique_keys()
        self._group_name = self.desired_state_definition.get("GroupName")
        self._vpc_id = self.desired_state_definition.get("VpcId")
        if not self._vpc_id:
            raise InvalidConfigException("Please specify VPC ID")
        self._sg_resource = None
        self._group_id = ""

    @property
    def security_group_resource(self):
        """
        The security group resource. Creates Boto Security Group resource for the given group id
        Returns:
             boto security group resource
        """
        if not self._sg_resource:
            self._sg_resource = self.resource.SecurityGroup(self._group_id)
        return self._sg_resource

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the security group
        """
        self.unique_keys = SecurityGroup.UNIQUE_KEYS

    def _start(self):
        """
        Creates vpc and adds tag for PCFName
        Returns:
           boto3 create_security_group response (groud id)
        """
        resp = self.client.create_security_group(**pcf_util.param_filter(self.desired_state_definition, SecurityGroup.START_PARAMS))
        self._group_id = resp.get("GroupId")
        tags = self.custom_config.get("Tags",[])
        if tags:
            self.security_group_resource.create_tags(
                DryRun=False,
                Tags=tags
            )
        outbound = self.custom_config.get("Outbound", {})
        inbound = self.custom_config.get("Inbound", {})
        if outbound:
            self.security_group_resource.authorize_egress(
                DryRun=False,
                IpPermissions=outbound
            )
        if inbound:
            self.security_group_resource.authorize_ingress(
                DryRun=False,
                IpPermissions=inbound
            )
        return resp

    def _terminate(self):
        """
        Calls boto3 delete_security_group()
        Returns:
            boto3 delete_vpc() response
        """
        resp = self.client.delete_security_group(GroupId=self._group_id)
        return resp

    def _stop(self):
        """
        Calls _terminate()
        """
        return self._terminate()

    def _update(self):
        """
        No updates available
        """
        raise NotImplemented

    def get_current_definition(self):
        """
        Calls boto3 describe_security_groups to return current definition.
        Returns missing if the security group doesn't exist
        Returns:
             status or {"status":"missing"}
        """
        security_group_list = self.client.describe_security_groups(
            Filters=[
                {
                    "Name": "vpc-id",
                    "Values": [
                        self._vpc_id
                    ]
                },
                {
                    "Name": "group-name",
                    "Values": [
                        self._group_name
                    ]
                }
            ]
        ).get("SecurityGroups", [])
        # Need to make sure the group name matches exactly, since it is just a filter
        for sg in security_group_list:
            if sg.get("GroupName") == self._group_name:
                return sg
        return {"status": "missing"}

    def sync_state(self):
        """
        Uses get_current_definition to determine whether the queue exists or not and sets the state

        Returns:
            void
        """
        # get the current definition. if it exists, running; if missing, terminated.
        self.current_state_definition = self.get_current_definition()
        if self.current_state_definition:
            self.state = State.running
        else:
            self.state = State.terminated

    def is_state_definition_equivalent(self):
        """
        Compared the desired state and current state definition

        Returns:
            bool
        """
        self.sync_state()
        # use filters to remove any extra information
        self.current_state_definition = {key: self.current_state_definition[key] for key in SecurityGroup.DEFINITION_FILTER
                                         if key in self.current_state_definition.keys()}
        self.desired_state_definition = {key: self.desired_state_definition[key] for key in SecurityGroup.DEFINITION_FILTER
                                         if key in self.desired_state_definition.keys()}
        diff_dict = pcf_util.diff_dict(self.current_state_definition, self.desired_state_definition)
        return diff_dict == {}

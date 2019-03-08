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
from pcf.particle.aws.vpc.vpc_instance import VPCInstance
from deepdiff import DeepDiff


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
        "IpPermissionsEgress",
        "IpPermissions"
    }

    UNIQUE_KEYS = ["aws_resource.GroupName"]

    def __init__(self, particle_definition):
        super().__init__(particle_definition, "ec2")
        self._set_unique_keys()
        self._group_name = self.desired_state_definition.get("GroupName")
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

    def _set_vpc_id(self):
        """
        Checks to see if user specified a vpc_id in the particle definition.
        If not the vpc_id is retrieved from it's parent using the get_vpc_id util
        """
        if not self.desired_state_definition.get("VpcId"):
            # need it defined in the definition for _start()
            self.desired_state_definition["VpcId"] = pcf_util.get_value_from_particles(self.parents, VPCInstance, "vpc_id")
        self._vpc_id = self.desired_state_definition.get("VpcId")

    def _start(self):
        """
        Creates security group and adds the tags and rules
        Returns:
           boto3 create_security_group response (groud id)
        """
        resp = self.client.create_security_group(**pcf_util.param_filter(self.desired_state_definition,
                                                                         SecurityGroup.START_PARAMS))
        self._group_id = resp.get("GroupId")
        tags = self.custom_config.get("Tags", [])
        if tags:
            self.security_group_resource.create_tags(
                Tags=tags
            )
        outbound = self.custom_config.get("IpPermissionsEgress", {})
        inbound = self.custom_config.get("IpPermissions", {})
        if outbound:
            self.security_group_resource.authorize_egress(
                IpPermissions=outbound
            )
        if inbound:
            self.security_group_resource.authorize_ingress(
                IpPermissions=inbound
            )
        return resp

    def _terminate(self):
        """
        Calls boto3 delete_security_group()
        Returns:
            boto3 delete_security_group() response
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
        removes and adds security group rules based on the new desired definition using boto3 revoke and authorize
        """
        # no boto command for removing tags. create_tags both creates and updates existing tags
        new_tags = DeepDiff(self.current_state_definition.get("Tags", []),
                            self.custom_config.get("Tags", []))
        new_tags.pop("iterable_item_removed", None)
        if new_tags:
            self.security_group_resource.create_tags(
                Tags=self.custom_config.get("Tags")
            )
        dd_egress = DeepDiff(self.current_state_definition.get("IpPermissionsEgress", {}),
                             self.custom_config.get("IpPermissionsEgress"))
        dd_ingress = DeepDiff(self.current_state_definition.get("IpPermissions", {}),
                              self.custom_config.get("IpPermissions"))

        if dd_ingress:
            if dd_ingress.get("iterable_item_removed") or dd_ingress.get("values_changed"):
                self.security_group_resource.revoke_ingress(
                    IpPermissions=self.current_state_definition.get("IpPermissions")
                )
            if dd_ingress.get("iterable_item_added") or dd_ingress.get("values_changed"):
                self.security_group_resource.authorize_ingress(
                    IpPermissions=self.custom_config.get("IpPermissions")
                )
        if dd_egress:
            if dd_egress.get("iterable_item_removed") or dd_egress.get("values_changed"):
                self.security_group_resource.revoke_egress(
                    IpPermissions=self.current_state_definition.get("IpPermissionsEgress")
                )
            if dd_egress.get("iterable_item_added") or dd_egress.get("values_changed"):
                self.security_group_resource.authorize_egress(
                    IpPermissions=self.custom_config.get("IpPermissionsEgress")
                )

    def get_current_definition(self):
        """
        Calls boto3 describe_security_groups to return current definition.
        Returns missing if the security group doesn't exist
        Returns:
             status or None
        """
        self._set_vpc_id()
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
                self._group_id = sg.get("GroupId")
                return sg

    def sync_state(self):
        """
        Uses get_current_definition to determine whether the group exists or not and sets the state

        Returns:
            void
        """
        # get the current definition. if it exists, running; if missing, terminated.
        current_definition = self.get_current_definition()
        if current_definition:
            self.state = State.running
            self.current_state_definition = current_definition
        else:
            self.state = State.terminated

    def is_state_definition_equivalent(self):
        """
        Compares the desired state and current state definition and returns whether they are equivalent
        Only considers fields defined in the desired definition
        All fields not specified are left alone in the current state (excluding rules)
        Both rules lists must be defined even when empty

        Returns:
            bool
        """
        self.sync_state()
        # use filters to remove any extra information
        desired_config = pcf_util.param_filter(self.desired_state_definition.get("custom_config", {}),
                                               SecurityGroup.DEFINITION_FILTER)
        current_config = pcf_util.param_filter(self.get_current_state_definition(), desired_config.keys())
        diff = DeepDiff(current_config, desired_config, ignore_order=True)
        return diff == {}

    def is_state_equivalent(self, state1, state2):
        """
        Looks up state equivalents and checks if the two inputs map to the same state

        Returns:
            bool
        """
        return SecurityGroup.equivalent_states.get(state1) == SecurityGroup.equivalent_states.get(state2)

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


class VPCInstance(AWSResource):
    """
    This is the implementation of Amazon's VPC resource.
    """

    flavor = "vpc_instance"
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
        "CidrBlock",
        "AmazonProvidedIpv6CidrBlock",
        "InstanceTenancy"
    }

    UNIQUE_KEYS = ["aws_resource.custom_config.vpc_name"]

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition, "ec2", session)
        self._set_unique_keys()
        self.vpc_name = self.custom_config.get("vpc_name")
        self._vpc_client = None

    @property
    def vpc_client(self):
        """
        The VPC client. Calls _get_vpc_client to create a new client if needed

        Returns:
             vpc_client
        """
        if not self._vpc_client:
            self._vpc_client = self._get_vpc_client()
        return self._vpc_client

    def _get_vpc_client(self):
        """
        Creates a new vpc_client

        Returns:
             vpc_client
        """
        return self.resource.Vpc(self.vpc_id)

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the VPC

        """
        self.unique_keys = VPCInstance.UNIQUE_KEYS

    def get_status(self):
        """
        Calls boto3 describe_vpc using describe_vpcs().

        Returns:
             status or {"status":"missing"}
        """
        vpc = self.client.describe_vpcs(Filters=[{"Name":"tag:PCFName","Values":[self.vpc_name]}])
        if len(vpc["Vpcs"]) == 1:
            return vpc["Vpcs"][0]

    def _terminate(self):
        """
        Calls boto3 delete_vpc()

        Returns:
            boto3 delete_vpc() response
        """
        resp = self.client.delete_vpc(VpcId=self.vpc_id)
        return resp

    def _start(self):
        """
        Creates vpc and adds tag for PCFName

        Returns:
           boto3 create_vpc() response
        """
        resp = self.client.create_vpc(**pcf_util.param_filter(self.desired_state_definition,VPCInstance.START_PARAMS))
        self.vpc_id = resp['Vpc'].get("VpcId")
        self.current_state_definition = resp
        tags = self.custom_config.get("Tags",[])
        tags.append({"Key":"PCFName","Value":self.vpc_name})
        self.vpc_client.create_tags(Tags=tags)
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

    def sync_state(self):
        """
        Calls get_status() and updates the current_state_definition and the state.
        """
        full_status = self.get_status()
        if full_status is None:
            self.state = State.terminated
        else:
            self.state = VPCInstance.state_lookup.get(full_status["State"])
            self.current_state_definition = full_status
            self.vpc_id = full_status.get("VpcId")

    def is_state_equivalent(self, state1, state2):
            """
            Args:
                state1 (State):
                state2 (State):

            Returns:
                bool
            """
            return VPCInstance.equivalent_states.get(state1) == VPCInstance.equivalent_states.get(state2)

    def is_state_definition_equivalent(self):
        """
        Since there is no update available for vpc this always returns True

        Returns:
             bool
        """
        return True


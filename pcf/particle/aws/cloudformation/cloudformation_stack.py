# Copyright 2019 Capital One Services, LLC
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
from pcf.core.pcf_exceptions import NoResourceException

class CloudFormationStack(AWSResource):
    """
    Particle that maps to Cloudformation Stack
    """

    flavor = 'cloudformation'

    START_PARAM_FILER = {

    }

    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0,
    }

    UNIQUE_KEYS = ["aws_resource.Comment"]

    def __init__(self, particle_definition, session=None):
        """
        Args:
            particle_definition (definition): desired configuration of the particle
        """
        super(CloudFormationStack, self).__init__(particle_definition, 'cloudformation', session=session)
        self.stack_name = self.desired_state_definition["StackName"]

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the distribution
        """
        self.unique_keys = CloudFormationStack.UNIQUE_KEYS

    def _start(self):
        """
        Creates the distribution according to the particle definition and adds tags if necessary

        Returns:
            hosted_zone: boto3 response
        """
        start_definition = pcf_util.param_filter(self.desired_state_definition, CloudFormationStack.START_PARAM_FILER)
        response = self.client.create_stack(self.desired_state_definition)

        return response

    def _terminate(self):
        """
        Deletes the distribution using its id

        Returns:
            boto3 response
        """
        return self.client.delete_stack(StackName=self.stack_name)

    def _stop(self):
        """
        Calls _terminate()
        """
        return self.terminate()

    def _update(self):
        """
        Not implemented
        """
        pass

    def get_status(self):
        
        try:
            cloudformation_resp = self.client.describe_stacks(StackName=self.stack_name)
        except NoResourceException:
            return {"status": "missing"}
        
        return cloudformation_resp

    def sync_state(self):
        """
        Sync state calls get_status to determines and set the state of the distribution
        """
        full_status = self.get_status()
        if not full_status:
            self.state = State.terminated
        else:
            self.current_state_definition = full_status

    def is_state_equivalent(self, state1, state2):
        """
        Determines if states are equivalent
        Args:
            state1 (state): first state
            state2 (state): second state
        Returns:
            bool: whether the two states are equivalent
        """
        return CloudFormationStack.equivalent_states.get(state1) == CloudFormationStack.equivalent_states.get(state2)

    def is_state_definition_equivalent(self):
        """
        Since there is no update available, always return True
        Returns:
             bool: True
        """
        return True

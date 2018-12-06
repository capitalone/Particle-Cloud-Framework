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
from botocore.errorfactory import ClientError
import boto3

class IAMPolicy(AWSResource):
    """
    This is the implementation of Amazon's IAM Policy.
    """
    flavor = "iam_policy"
    state_lookup = {
        "missing": State.terminated,
        "active": State.running,
        "inactive": State.terminated
    }
    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0
    }

    START_PARAMS_FILTER = {
        "PolicyName",
        "PolicyDocument",
    }
    UPDATE_PARAM_CONVERSIONS = {
        "PolicyDocument",
    }

    UNIQUE_KEYS = ["aws_resource.PolicyName"]

    def __init__(self, particle_definition):
        super(IAMPolicy, self).__init__(
            particle_definition=particle_definition,
            resource_name="iam",
        )
        self.policy_name = self.desired_state_definition.get('PolicyName')
        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the S3 Bucket
        """
        self.unique_keys = IAMPolicy.UNIQUE_KEYS

    def get_status(self):
        """
        Determines if the iam policy exists
        Returns:
             status (dict)
        """

        try:
            policy_status = self.client.list_policies(Scope="All")
        except ClientError as e:
            if e.response['Error']['Code'] == 'PolicyNotFoundException':
                logger.warning("Policy {} was not found. Defaulting state for {} to terminated".format(self.policy_name, self.policy_name))
                return {"status": "missing"}
            else:
                raise e

        policy = [x for x in policy_status.get('Policies') if x.get("PolicyName") == self.policy_name]
        self.current_state_definition = policy[0]

        if policy:
            if policy[0].get('Arn'):
                self.policy_arn = policy[0].get('Arn')
            return {"status":"active"}
        else:
            return {"status": "missing"} 

    def _terminate(self):
        """
        Deletes the IAM Policy
        Returns:
             response of boto3 delete_policy
        """
        return self.client.delete_policy(PolicyArn=self.policy_arn)

    def _start(self):
        """
        Creates the IAM Policy
        Returns:
             response of boto3 create_policy
        """
        create_definition = pcf_util.param_filter(self.get_desired_state_definition(), IAMPolicy.START_PARAMS_FILTER)
        return self.client.create_policy(**create_definition)

    def _stop(self):
        """
        IAM Policy does not have a stopped state so it calls terminate.
        """
        return self.terminate()

    def sync_state(self):
        """
        Calls get status and then sets the current state.
        """
        full_status = self.get_status()

        if full_status:
            status = full_status.get("status", "missing").lower()
            self.state = IAMPolicy.state_lookup.get(status)


            # need way to determine current state definition without making so many api calls
            # self.current_state_definition = self.desired_state_definition

    def _update(self):
        """
        
        """
        desired_def = self.get_desired_state_definition()

        new_policy = desired_def.get('PolicyDocument')
        policy = self.resource.Policy(self.policy_arn)

        return policy.create_version(PolicyDocument=new_policy, SetAsDefault=True)


    def is_state_equivalent(self, state1, state2):
        """
        Determines if states are equivalent. Uses equivalent_states defined in the S3Bucket class.
        Args:
            state1 (State):
            state1 (State):
        Returns:
            bool
        """

        return IAMPolicy.equivalent_states.get(state1) == IAMPolicy.equivalent_states.get(state2)

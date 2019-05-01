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
import json
from deepdiff import DeepDiff
from pprint import pprint

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
        "Path"
    }

    UNIQUE_KEYS = ["aws_resource.PolicyName"]

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition=particle_definition, resource_name="iam", session=session)
        self.policy_name = self.desired_state_definition.get('PolicyName')
        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify IAM Policies
        """
        self.unique_keys = IAMPolicy.UNIQUE_KEYS

    def get_status(self):
        """
        Determines if the IAM Policy exists
        Returns:
             status (dict)
        """

        try:
            policy_status = self.client.list_policies(Scope="Local")
        except ClientError as e:
            if e.response['Error']['Code'] == 'PolicyNotFoundException':
                logger.warning("Policy {} was not found. Defaulting state for {} to terminated".format(self.policy_name, self.policy_name))
                return {"status": "missing"}
            else:
                raise e

        policy = [x for x in policy_status.get('Policies') if x.get("PolicyName") == self.policy_name]

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
        policy_versions = self.client.list_policy_versions(
            PolicyArn=self.policy_arn,
        )

        # All policy versions must be deleted before default policy can be deleted. 
        if policy_versions:
            for v in policy_versions.get('Versions'):
                if(not v.get('IsDefaultVersion') and len(policy_versions.get('Versions')) != 1):
                    self.client.delete_policy_version(PolicyArn=self.policy_arn, VersionId=v.get('VersionId'))

        return self.client.delete_policy(PolicyArn=self.policy_arn)

    def _start(self):
        """
        Creates the IAM Policy
        Returns:
             response of boto3 create_policy
        """
        create_definition = pcf_util.param_filter(self.get_desired_state_definition(), IAMPolicy.START_PARAMS_FILTER)

        try:
            return self.client.create_policy(**create_definition)
        except ClientError as e:
            raise e

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

        if full_status.get('status') != 'missing':
            policy = self.client.get_policy(
                PolicyArn = self.policy_arn
            )

            policy_version = self.client.get_policy_version(
                PolicyArn=self.policy_arn,
                VersionId= policy['Policy']['DefaultVersionId']
            )

            self.current_state_definition['PolicyDocument'] = json.dumps(policy_version.get('PolicyVersion').get('Document'))
            self.current_state_definition['Path'] = policy.get('Path')
            self.current_state_definition['PolicyName'] = self.policy_name
            self.current_state_definition['custom_config'] = self.custom_config


    def _update(self):
        """
            Updates the IAM Policy to match desired state definition. 
        """

        new_desired_def = self.get_desired_state_definition().get('PolicyDocument')
 
        return self.client.create_policy_version(PolicyArn=self.policy_arn, PolicyDocument=new_desired_def, SetAsDefault=True)


    def is_state_equivalent(self, state1, state2):
        """
        Determines if states are equivalent. Uses equivalent_states defined in the IAMPolicy class.
        Args:
            state1 (State):
            state1 (State):
        Returns:
            bool
        """

        return IAMPolicy.equivalent_states.get(state1) == IAMPolicy.equivalent_states.get(state2)



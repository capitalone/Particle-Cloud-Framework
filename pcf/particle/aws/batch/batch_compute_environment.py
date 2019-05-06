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

from pcf.core import State
from pcf.core.aws_resource import AWSResource
from pcf.util import pcf_util


class BatchComputeEnvironment(AWSResource):
    """
    This is the implementation of Amazon's Batch Compute Environment.
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.create_compute_environment
    """

    flavor = "batch_compute_environment"

    UPDATE_PARAM_FILTER = {
        "state",
        "computeResources",
    }

    state_lookup = {
        "CREATING": State.pending,
        "UPDATING": State.pending,
        "DELETING": State.pending,
        "DELETED": State.terminated,
        "VALID": State.running,
        "INVALID": State.terminated,
    }

    UNIQUE_KEYS = ['aws_resource.computeEnvironmentName']

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition, "batch", session=session)
        self._set_unique_keys()
        self.name = self.desired_state_definition['computeEnvironmentName']

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the BatchComputeEnvironment
        """
        self.unique_keys = BatchComputeEnvironment.UNIQUE_KEYS

    def get_status(self):
        """
        Calls boto3 describe_compute_environments.

        Returns:
             status or {}
        """
        res = self.client.describe_compute_environments(
            computeEnvironments=[self.name],
        )

        if len(res["computeEnvironments"]) != 1:
            return {}

        return res["computeEnvironments"][0]

    def _terminate(self):
        """
        Sets state DISABLED then calls boto3 delete_compute_environment() to terminate

        Returns:
            boto3 delete_compute_environment() response
        """
        # need to disable before terminating
        if self.state != State.stopped:
            return self._stop()

        return self.client.delete_compute_environment(
            computeEnvironment=self.name
        )

    def _start(self):
        """
        Calls boto3 create_compute_environment() and sets the status to ENABLED by default.

        Returns:
            boto3 create_compute_environment() response
        """
        # calls enable if transitioning from stopped state
        if self.current_state_definition:
            return self.enable()
        return self.client.create_compute_environment(**self.desired_state_definition)

    def enable(self):
        """
        Calls boto3 update_compute_environment() and sets state to ENABLED

        Returns:
            boto3 update_compute_environment() response
        """
        return self.client.update_compute_environment(
            computeEnvironment=self.name,
            state='ENABLED'
        )

    def _stop(self):
        """
        Calls boto3 update_compute_environment() and sets state to DISABLED

        Returns:
            boto3 update_compute_environment() response
        """
        return self.client.update_compute_environment(
            computeEnvironment=self.name,
            state='DISABLED'
        )

    def sync_state(self):
        """
        Calls get_status() and updates the current_state_definition and the state.
        """
        # set the default desired state to ENABLED
        if not self.desired_state_definition.get("state"):
            self.desired_state_definition["state"] = "ENABLED"

        full_status = self.get_status()
        self.current_state_definition = full_status
        if full_status:
            status = self.state_lookup[full_status.get('status')]
            state_type = full_status['state']

            if status == State.running and state_type =="DISABLED":
                self.state = State.stopped
            else:
                self.state = status
        else:
            self.state = State.terminated

    def _update(self):
        """
        Calls boto3 update_compute_environment(). Can only update fields in UPDATE_PARAM_FILTER.

        Returns:
            boto3 put_attributes() response
        """
        filtered_desired_state_definition = pcf_util.param_filter(
            self.desired_state_definition,
            BatchComputeEnvironment.UPDATE_PARAM_FILTER)

        return self.client.update_compute_environment(
                            computeEnvironment=self.name,
                            **filtered_desired_state_definition
                            )

    def is_state_definition_equivalent(self):
        """
        Checks if the current state definition and desired state definitions are equivalent including
        attributes.

        Returns:
            bool
        """
        filtered_current_state_definition = pcf_util.param_filter(
            self.current_state_definition,
            BatchComputeEnvironment.UPDATE_PARAM_FILTER)
        filtered_desired_state_definition = pcf_util.param_filter(
            self.desired_state_definition,
            BatchComputeEnvironment.UPDATE_PARAM_FILTER)

        diff = pcf_util.diff_dict(filtered_desired_state_definition,filtered_current_state_definition)

        # TODO might need more comp logic here
        if not self.desired_state_definition["serviceRole"] in self.current_state_definition["serviceRole"]:
            return False

        if diff or len(diff) != 0:
            return False

        return True


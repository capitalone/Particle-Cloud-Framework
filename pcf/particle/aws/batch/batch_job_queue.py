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


class BatchJobQueue(AWSResource):
    """
    This is the implementation of Amazon's Batch Job Queue.
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.create_job_queue
    """

    flavor = "batch_job_queue"

    state_lookup = {
        "CREATING": State.pending,
        "UPDATING": State.pending,
        "DELETING": State.pending,
        "DELETED": State.terminated,
        "VALID": State.running,
        "INVALID": State.terminated,
    }

    UPDATE_PARAM_FILTER = {
        "state",
        "priority",
        "computeEnvironmentOrder",
    }

    UNIQUE_KEYS = ['aws_resource.jobQueueName']

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition, "batch", session=session)
        self._set_unique_keys()
        self.name = self.desired_state_definition['jobQueueName']

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the BatchJobQueue
        """
        self.unique_keys = BatchJobQueue.UNIQUE_KEYS

    def get_status(self):
        """
        Calls boto3 describe_job_queues.

        Returns:
             status or {}
        """
        res = self.client.describe_job_queues(
            jobQueues=[self.name],
        )

        if len(res["jobQueues"]) != 1:
            return {}

        return res["jobQueues"][0]

    def _terminate(self):
        """
        Sets state DISABLED then calls boto3 delete_job_queue() to terminate

        Returns:
            boto3 delete_job_queue() response
        """
        # need to disable before terminating
        if self.state != State.stopped:
            return self._stop()

        return self.client.delete_job_queue(
            jobQueue=self.name
        )

    def _start(self):
        """
        Calls boto3 create_job_queue() and sets the status to ENABLED by default.

        Returns:
            boto3 create_job_queue() response
        """
        # calls enable if transitioning from stopped state
        if self.current_state_definition:
            return self.enable()
        return self.client.create_job_queue(**self.desired_state_definition)

    def enable(self):
        """
        Calls boto3 update_job_queue() and sets state to ENABLED

        Returns:
            boto3 update_job_queue() response
        """
        return self.client.update_job_queue(
            jobQueue=self.name,
            state='ENABLED'
        )

    def _stop(self):
        """
        Calls boto3 update_job_queue() and sets state to DISABLED

        Returns:
            boto3 update_compute_environment() response
        """
        return self.client.update_job_queue(
            jobQueue=self.name,
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

            if status == State.running and state_type == "DISABLED":
                self.state = State.stopped
            else:
                self.state = status
        else:
            self.state = State.terminated

    def _update(self):
        """
        Calls boto3 update_job_queue(). Can only update fields in UPDATE_PARAM_FILTER.

        Returns:
            boto3 put_attributes() response
        """
        filtered_definition = pcf_util.param_filter(self.desired_state_definition, self.UPDATE_PARAM_FILTER)
        return self.client.update_job_queue(
            jobQueue=self.name,
            **filtered_definition
        )

    def is_state_definition_equivalent(self):
        """
        Checks if the current state definition and desired state definitions are equivalent including
        attributes.

        Returns:
            bool
        """
        filtered_desired_def = pcf_util.param_filter(self.desired_state_definition, self.UPDATE_PARAM_FILTER)
        filtered_current_def = pcf_util.param_filter(self.current_state_definition, self.UPDATE_PARAM_FILTER)

        diff = pcf_util.diff_dict(filtered_desired_def, filtered_current_def)

        if diff or len(diff) != 0:
            return False

        return True


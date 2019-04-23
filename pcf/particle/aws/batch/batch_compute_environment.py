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

    START_PARAM_FILTER = {
        "attributes",
    }

    UPDATE_PARAM_FILTER = {
        "attributes",
    }

    state_lookup = {
        "CREATING": State.pending,
        "UPDATING": State.pending,
        "DELETING": State.pending,
        "DELETED": State.terminated,
        "VALID": State.running,
        "INVALID": State.terminated,
    }

    UNIQUE_KEYS = ['computeEnvironmentName']

    def __init__(self, particle_definition):
        super(BatchComputeEnvironment, self).__init__(particle_definition, "batch")
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
            maxResults=1
        )

        if len(res["computeEnvironments"]) != 1:
            return {}

        return res["computeEnvironments"][0]

    def _terminate(self):
        """
        Calls boto3 delete_compute_environment()

        Returns:
            boto3 delete_compute_environment() response
        """
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
        # set the default state to ENABLED
        if not self.desired_state_definition.get("state"):
            self.desired_state_definition["state"] = "ENABLED"
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
        full_status = self.get_status()
        self.current_state_definition = full_status
        if full_status:
            status = BatchComputeEnvironment.state_lookup(full_status['status'])
            state_type = full_status['state']

            if status == State.running and state_type =="DISABLED"
                self.state = State.stopped
            else:
                self.state = status
        else:
            self.state = State.terminated

    def _update(self):
        """
        Calls boto3 put_attributes() to update ECS Instance attributes. Does not allow for attributes that start
        with com.amazonaws.ecs. or instance-id to be updated.

        Returns:
            boto3 put_attributes() response
        """
        new_desired_state_def, diff_dict = pcf_util.update_dict(self.current_state_definition,
                                                                self.get_desired_state_definition())
        update_definition = pcf_util.param_filter(new_desired_state_def, ECSInstance.UPDATE_PARAM_FILTER)
        attributes = []
        for a in update_definition['attributes']:
            if (not a['name'].startswith('ecs.')
                and not a['name'].startswith('com.amazonaws.ecs.')
                and a['name'] not in ECSInstance.PROTECTED_ATTRIBUTES):
                attributes.append({
                    'name': a['name'],
                    'value': a['value'],
                    'targetType': 'container-instance',
                    'targetId': self.get_ecs_instance_id(),
                })

        return self.client.put_attributes(
            cluster=self.get_cluster_name(),
            attributes=attributes,
        )

    def is_state_definition_equivalent(self):
        """
        Checks if the current state definition and desired state definitions are equivalent including
        attributes.

        Returns:
            bool
        """
        existing_attributes = self.current_state_definition.get('attributes', [])
        desired_attributes = self.get_desired_state_definition().get('attributes', [])

        d = dict()
        for a in existing_attributes:
            d[a['name']] = a.get('value')

        if isinstance(desired_attributes, list):
            for a in desired_attributes:
                # print('checking id %s in %s' % (a['name'], d))
                if (not a['name'].startswith('ecs.')
                    and not a['name'].startswith('com.amazonaws.ecs.')
                    and a['name'] not in ECSInstance.PROTECTED_ATTRIBUTES):
                    if a['name'] not in d or d.get(a['name']) != a.get('value'):
                        return False

        elif isinstance(desired_attributes, dict):
            for a in desired_attributes:
                # print('checking id %s in %s' % (a['name'], d))
                if (not a.startswith('ecs.')
                    and not a.startswith('com.amazonaws.ecs.')
                    and a not in ECSInstance.PROTECTED_ATTRIBUTES):
                    if a not in d or d.get(a) != desired_attributes.get(a):
                        return False

        return True

    def is_state_equivalent(self, state1, state2):
        """
        Args:
          state1 (State):
          state2 (State):

        Returns:
          bool
        """
        return ECSInstance.equivalent_states.get(state1) == ECSInstance.equivalent_states.get(state2)

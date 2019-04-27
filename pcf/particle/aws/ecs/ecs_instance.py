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
from pcf.core.aws_resource import AWSResource
from pcf.particle.aws.ecs.ecs_cluster import ECSCluster
from pcf.core.pcf_exceptions import NoResourceException
from pcf.util import pcf_util

class ECSInstance(AWSResource):
    """
    This is the implementation of Amazon's ECS Service. This particle requires task definition and ecs cluster
    particles as parents.
    """

    flavor = "ecs_instance"

    START_PARAM_FILTER = {
        "attributes",
    }

    UPDATE_PARAM_FILTER = {
        "attributes",
    }

    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0
    }

    PROTECTED_ATTRIBUTES = ('instance-id')

    UNIQUE_KEYS = []

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition, "ecs", session=session)

        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the ECS Instance

        """
        self.unique_keys = ECSInstance.UNIQUE_KEYS

    def _get_arn(self):
        """
        Looks for the parrent ec2 particle and uses the ec2 instance id as the key in boto3 list_attributes(). The response
        of list_attributes() is then parsed for the targetId which is used

        Returns:
            ECS Instance arn
        """
        if len(self.parents) > 0:
            # TODO - this is a hack to make up for the lack of particle families
            ec2_instance_parents = list(filter(lambda x: 'ec2_instance' in x.flavor, self.parents))

            if len(ec2_instance_parents) == 1:
                ec2_instance_particle = ec2_instance_parents[0]
                ec2_instance_particle.sync_state()
                try:
                    ec2_instance_id = ec2_instance_particle.get_instance_id()
                except NoResourceException:
                    ec2_instance_id = None
            else:
                raise Exception("ecs_instance requires exactly 1 ec2_instance as the parent")

        if not ec2_instance_id:
            return None

        ecs_instance_attributes = pcf_util.get_item_from_dicts("attributes", self.current_state_definition, self.desired_state_definition)

        attributes_resp = self.client.list_attributes(
            cluster=self.get_cluster_name(),
            targetType='container-instance',
            attributeName='instance-id',
            attributeValue=ec2_instance_id,
        )['attributes']

        if len(attributes_resp) == 0:
            return None
        elif len(attributes_resp) == 1:
            return attributes_resp[0]['targetId']
        else:
            error_msg = "found more than one instance with the same attribute: {}".format(attributes_resp)
            raise Exception(error_msg)

    def get_ecs_instance_id(self):
        """
        Returns:
             get_identifier()
        """
        return self.get_identifier()

    def get_cluster_name(self):
        """
        Gets the cluster name from the ecs parent otherwise returns an exception if there is no parent ecs
        cluster particle.

        Returns:
            ECS Cluster name
        """
        if len(self.parents) > 0:
            parent_clusters = [p for p in self.parents if p.flavor == ECSCluster.flavor]

            if len(parent_clusters) == 1:
                self.desired_state_definition["clusterName"] = parent_clusters[0].get_label()
                return parent_clusters[0].get_label()
            else:
                raise Exception("ecs_instance requires exactly 1 ecs_cluster as the parent")


    def get_status(self):
        """
        Calls boto3 describe_container_instances using arn.

        Returns:
             status or {}
        """
        ecs_cluster_name = self.get_cluster_name()
        ecs_instance_id = self.get_ecs_instance_id()

        if not ecs_instance_id or not ecs_cluster_name:
            return {}

        res = self.client.describe_container_instances(
            cluster=ecs_cluster_name,
            containerInstances=[ecs_instance_id],
        )

        failures = res.get('failures')
        container_instances = res.get('containerInstances')

        if container_instances and len(container_instances) == 1:
            container_instance = container_instances[0]
            self.container_instance_arn = container_instance['containerInstanceArn']
            return container_instance
        else:
            error_msg = "cluster instance status returned unexpected results: {}".format(failures or container_instances)
            raise Exception(error_msg)


    def _terminate(self):
        """
        Calls boto3 update_container_instances_state() and sets the status to DRAINING.

        Returns:
            boto3 update_container_instances_state() response
        """
        return self.client.update_container_instances_state(
            cluster=self.get_cluster_name(),
            containerInstances=[self.get_ecs_instance_id()],
            status='DRAINING',
        )

    def _start(self):
        """
        Calls boto3 update_container_instances_state() and sets the status to ACTIVE.

        Returns:
            boto3 update_container_instances_state() response
        """
        ecs_instance_id = self.get_ecs_instance_id()

        if ecs_instance_id:
            return self.client.update_container_instances_state(
                cluster=self.get_cluster_name(),
                containerInstances=[ecs_instance_id],
                status='ACTIVE',
            )

    def _stop(self):
        """
        Calls _terminate()
        """
        return self._terminate()

    def sync_state(self):
        """
        Calls get_status() and updates the current_state_definition and the state.
        """
        full_status = self.get_status()
        if full_status:
            self.current_state_definition = full_status
            status = full_status['status']
            agent_connected = full_status['agentConnected']

            if agent_connected and status == 'ACTIVE':
                self.state = State.running
                return

            if status == 'DRAINING':
                self.state = State.stopped
                return

            if not agent_connected:
                self.state = State.stopped
                return

            raise Exception('Reached an unexpected state: {}'.format(full_status))
        self.state = State.terminated
        self.current_state_definition = {}

    def _update(self):
        """
        Calls boto3 put_attributes() to update ECS Instance attributes. Does not allow for attributes that start
        with com.amazonaws.ecs. or instance-id to be updated.

        Returns:
            boto3 put_attributes() response
        """
        new_desired_state_def, diff_dict = pcf_util.update_dict(self.current_state_definition, self.get_desired_state_definition())
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

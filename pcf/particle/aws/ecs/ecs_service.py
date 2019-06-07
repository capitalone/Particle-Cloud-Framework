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
from pcf.particle.aws.ecs.ecs_task_definition import ECSTaskDefinition
from pcf.util import pcf_util

from botocore.errorfactory import ClientError

import logging
logger = logging.getLogger(__name__)


class ECSService(AWSResource):
    """
    This is the implementation of Amazon's ECS Service. This particle requires task definition and ecs cluster either
    to be included in the initial state definition or have those particles as parents.
    """
    flavor = "ecs_service"

    state_lookup = {
        "missing": State.terminated,
        "active": State.running,
        "pending":State.pending,
        "inactive": State.terminated,
        "draining": State.pending
    }

    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0
    }

    START_PARAM_CONVERSIONS = {
        "clusterName": "cluster",
        "serviceName": "",
        "taskDefinition": "",
        "loadBalancers": "",
        "serviceRegistries": "",
        "desiredCount": "",
        "launchType": "",
        "platformVersion": "",
        "placementConstraints": "",
        "clientToken": "",
        "roleArn": "role",
        "deploymentConfiguration": "",
        "placementStrategy": "",
        "networkConfiguration": "",
        "healthCheckGracePeriodSeconds": "",
        "schedulingStrategy": "",
        "deploymentController": "",
        "tags": "",
        "enableECSManagedTags": "",
        "propagateTags": "",
    }

    UPDATE_PARAM_CONVERSIONS = {
        "clusterName": "cluster",
        "serviceName": "service",
        "taskDefinition": "",
        "desiredCount": "",
        "deploymentConfiguration": "",
    }

    UNIQUE_KEYS = ["aws_resource.serviceName"]

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition, "ecs", session=session)

        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the ECS Service

        """
        self.unique_keys = ECSService.UNIQUE_KEYS

    def get_service_name(self):
        service_name = pcf_util.get_item_from_dicts("serviceName", self.current_state_definition, self.desired_state_definition)
        return service_name

    def get_task_definition(self):
        """
        Check for a task definition parent and returns the task definition id

        Returns:
            task_definition_id
        """
        if len(self.parents) > 0:
            ecs_task_def_parents = list(filter(lambda x: x.flavor == ECSTaskDefinition.flavor, self.parents))

            if len(ecs_task_def_parents) == 1:
                task_definition_particle = ecs_task_def_parents[0]
                task_definition_particle.sync_state()
                task_definition_id = task_definition_particle.get_task_definition_id()

                return task_definition_id
            else:
                raise Exception("ecs_service requires exactly 1 task definition as the parent")

    def get_cluster_name(self):
        """
        Checks for a ecs service parent and returns the cluster names.

        Returns:
           cluster_name
        """
        if len(self.parents) > 0:
            ecs_cluster_parents = list(filter(lambda x: x.flavor == ECSCluster.flavor, self.parents))

            if len(ecs_cluster_parents) == 1:
                self.desired_state_definition["clusterName"] = ecs_cluster_parents[0].cluster_name
                return ecs_cluster_parents[0].cluster_name
            else:
                raise Exception("ecs_service requires exactly 1 ecs_cluster as the parent")


    def get_status(self):
        """
        Calls boto3 describe_services using get_service_name() and ecs_cluster_name.

        Returns:
            status or {"status":"missing"}
        """
        ecs_cluster_name = self.get_cluster_name()
        try:
            service_status_resp = self.client.describe_services(cluster=ecs_cluster_name, services=[self.get_service_name()])
        except ClientError as e:
            if e.response['Error']['Code'] == 'ClusterNotFoundException':
                logger.warning("Cluster {} was not found. Defaulting state for {} to terminated".format(ecs_cluster_name, self.get_service_name()))
                return {"status": "missing"}
            else:
                raise e

        service_statuses = service_status_resp.get("services", []) + service_status_resp.get("failures", [])

        if len(service_statuses) == 1:
            service_arn = service_statuses[0].get("serviceArn")

            if service_arn:
                self.service_arn = service_arn

            running_count = service_statuses[0].get('runningCount', 0)
            desired_count = self.particle_definition['aws_resource'].get('desiredCount')

            if service_statuses[0].get('status') == 'ACTIVE' and self.desired_state != State.terminated and desired_count != running_count:
                    return {"status": "pending"}
            return service_statuses[0]

        else:
            error_msg = "cluster status returned unexpected results: {}".format(service_status_resp)
            raise Exception(error_msg)

    def _terminate(self):
        """
        Calls boto3 delete_service()

        Returns:
            boto3 delete_service() response
        """
        if self.get_state() == State.running:
            self.get_desired_state_definition()["desiredCount"] = 0
            self.update()

        resp = self.client.delete_service(cluster=self.get_cluster_name(), service=self.get_service_name())
        return resp

    def _start(self):
        """
        Calls boto3 create_service()

        Returns:
            boto3 create_service() response
        """
        new_desired_state_def, diff_dict = pcf_util.update_dict(self.current_state_definition, self.get_desired_state_definition())
        start_definition = pcf_util.keep_and_replace_keys(new_desired_state_def, ECSService.START_PARAM_CONVERSIONS)

        return self.client.create_service(**start_definition)

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
            status = full_status.get("status", "missing").lower()
            self.state = ECSService.state_lookup.get(status)
            self.current_state_definition = full_status
            if "clusterName" not in self.current_state_definition:
                self.current_state_definition["clusterName"] = self.get_cluster_name()
            if "taskDefinition" not in self.current_state_definition:
                self.current_state_definition["taskDefinition"] = self.get_task_definition()
            else:
                self.current_state_definition["taskDefinition"] = self.current_state_definition["taskDefinition"].split("/")[1]

    def _update(self):
        """
        Calls boto3 update_service()

        Returns:
           boto3 update_service() response
        """
        new_desired_state_def, diff_dict = pcf_util.update_dict(self.current_state_definition, self.get_desired_state_definition())
        update_definition = pcf_util.keep_and_replace_keys(new_desired_state_def, ECSService.UPDATE_PARAM_CONVERSIONS)

        return self.client.update_service(**update_definition)

    def is_state_equivalent(self, state1, state2):
        """
        Args:
           state1 (State):
           state2 (State):

        Returns:
           bool
        """
        return ECSService.equivalent_states.get(state1) == ECSService.equivalent_states.get(state2)

    def get_desired_state_definition(self):
        """
        Calls get_task_definition() and updates taskDefinition in desired_state_definition. If desired state
        is terminated this also sets the desiredCount to 0 in desired_state_definition.

        Returns:
            desired_state_definition
        """
        try:
            self.desired_state_definition["taskDefinition"] = self.get_task_definition()
        except Exception:
            pass

        if self.is_state_equivalent(self.desired_state, State.terminated):
            self.desired_state_definition["desiredCount"] = 0

        return self.desired_state_definition



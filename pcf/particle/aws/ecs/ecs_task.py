import time

from pcf.core import State
from pcf.core.aws_resource import AWSResource
from pcf.particle.aws.ecs.ecs_cluster import ECSCluster
from pcf.particle.aws.ecs.ecs_task_definition import ECSTaskDefinition
from pcf.util import pcf_util
import logging

logger = logging.getLogger(__name__)

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


class ECSTask(AWSResource):
    """
   This is the implementation of Amazon's ECS Task. This particle requires task definition and ecs cluster either
   to be included in the initial state definition or have those particles as parents.
   """

    flavor = "ecs_task"
    state_lookup = {
        "missing": State.terminated,
        "running": State.running,
        "stopped": State.stopped,
        "pending": State.pending
    }
    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0
    }

    START_PARAM_CONVERSIONS = {
        "clusterArn": "cluster",
        "taskDefinitionArn": "taskDefinition",
        "overrides": "",
        "count": "",
        "startedBy": "",
        "group": "",
        "placementConstraints": "",
        "placementStrategy": ""
    }

    UNIQUE_KEYS = ["aws_resource.taskName"]

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition, "ecs", session=session)
        self.failure_reason = None

        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the ECS Task

        """
        self.unique_keys = ECSTask.UNIQUE_KEYS

    def get_task_definition_arn(self):
        """
        Calls get_task_definition and returns the Arn attribute from that response.

        Returns:
             ECS Task Definition Arn
        """
        return self.get_task_definition().get_attribute_value("taskDefinitionArn")

    def get_task_definition(self):
        """
        Filters ecs_task parents for ecs_task_definition particle. Returns none if no parents and an exception if
        there is more than one ecs_task_definition particle as a parent.

        Returns:
             ECS Task Definition Particle or None
        """
        if len(self.parents) > 0:
            ecs_task_def_parents = list(filter(lambda x: x.flavor == ECSTaskDefinition.flavor, self.parents))

            if len(ecs_task_def_parents) == 1:
                task_definition_particle = ecs_task_def_parents[0]
                task_definition_particle.sync_state()

                return task_definition_particle
            else:
                raise Exception("ecs_task requires exactly 1 task definition as the parent")

    def get_ecs_cluster_arn(self):
        """
        Calls get_ecs_cluster and returns the Arn attribute from that response.

        Returns:
             ECS Cluster Arn
        """
        return self.get_ecs_cluster().get_attribute_value("clusterArn")

    def get_ecs_cluster(self):
        """
        Filters ecs_task parents for ecs_cluster particle. Returns none if no parents and an exception if
        there is more than one ecs_cluster particle as a parent.

        Returns:
             ECS Cluster Particle or None
        """
        if len(self.parents) > 0:
            ecs_cluster_parents = list(filter(lambda x: x.flavor == ECSCluster.flavor, self.parents))

            if len(ecs_cluster_parents) == 1:
                ecs_cluster_parents[0].sync_state()
                return ecs_cluster_parents[0]
            else:
                raise Exception("ecs_task requires exactly 1 ecs_cluster as the parent")

    def get_task_arn(self):
        """
        Checks if the current or desired state definitions have a startedBy key which means the task has been
        initialized. If this key if found this calls boto3 list tasks and filters for tasks that match the startBy key
        and cluster name. If only one task matches then this returns the taskArn otherwise returns None.

        Returns:
             ECS Task Arn or None
        """
        if self.get_attribute_value("taskArn"):
            return self.get_attribute_value("taskArn")

        if not pcf_util.get_item_from_dicts("startedBy", self.current_state_definition, self.desired_state_definition):
            return None

        list_task_request = {
            "startedBy": pcf_util.get_item_from_dicts("startedBy", self.current_state_definition, self.desired_state_definition),
            "cluster": self.get_ecs_cluster_arn()
        }

        task_arns = []
        resps = []

        for status in ["RUNNING", "PENDING", "STOPPED"]:
            resp = self.client.list_tasks(**list_task_request, desiredStatus=status)
            resps.append(resp)
            task_arns += resp.get("taskArns", [])

        if len(task_arns) == 1:
            return task_arns[0]
        elif len(task_arns) > 1:
            error_msg = "there are more than 1 ecs task matching the criteria: {}".format(resps)
            raise Exception(error_msg)
        else:
            return None

    def get_status(self):
        """
        Uses task arn and ecs cluster arn to call boto3 describe_tasks

        Returns:
             ECS Task Status
        """
        task_id = self.get_task_arn()
        if not task_id:
            return {"lastStatus": "missing"}

        ecs_task_status_resp = self.client.describe_tasks(cluster=self.get_ecs_cluster_arn(), tasks=[self.get_task_arn()])

        ecs_task_statuses = ecs_task_status_resp.get("tasks", []) + ecs_task_status_resp.get("failures", [])

        if len(ecs_task_statuses) == 1:
            return ecs_task_statuses[0]
        else:
            error_msg = "ecs task status returned unexpected results: {}".format(ecs_task_status_resp)
            raise Exception(error_msg)

    def _terminate(self):
        """
        Calls _stop()
        """
        self._stop()

    def _start(self):
        """
        Calls boto3 run_task function to create a new task. If successful this gets the arn of the task and adds it to the
        current_state_definition.
        """
        new_desired_state_def, diff_dict = pcf_util.update_dict(self.current_state_definition, self.get_desired_state_definition())
        start_definition = pcf_util.keep_and_replace_keys(new_desired_state_def, ECSTask.START_PARAM_CONVERSIONS)
        self.sync_state()
        if self.state == State.stopped and "containers" in self.current_state_definition:
            containers = self.current_state_definition.get("containers")
            for container in containers:
                if container.get("exitCode", -1) != 0:
                    logger.warning("Task {} failed to execute with exit code: {} and reason: {}... setting desired state to {}"
                                   .format(self.get_task_arn(),
                                            container.get("exitCode"),
                                           container.get("reason"),
                                           State.stopped))
                    self.failure_reason = {
                        "type": "container",
                        "reason": self.current_state_definition.get("stoppedReason", "N/A")
                    }
                    self.set_desired_state(State.stopped)
                    return

        resp = self.client.run_task(**start_definition)

        task = resp.get("tasks", [])
        failures = resp.get("failures", [])

        if len(task) == 1:
            self.current_state_definition["taskArn"] = task[0].get("taskArn")
        elif len(task) == 0 and len(failures) > 0:
            logger.warning("Task {} failed to be placed due to an ECS error: {}... setting desired state to {}"
                           .format(self.get_task_arn(),
                                   failures[0].get("reason"),
                                   State.stopped))
            self.failure_reason ={
                "type": "ecs",
                "reason": failures[0].get("reason")
            }
            self.set_desired_state(State.stopped)

        else:
            Exception("ECS Task failed to start")



    def _stop(self):
        """
        Calls boto3 stop_task function using the task arn. If a stop reason is not given in the desired_state_definition
        then "PCF default stop action" is used.
        """
        stop_reason = self.get_attribute_value("stopReason")

        if not stop_reason: stop_reason = "PCF default stop action"

        response = self.client.stop_task(
            cluster=self.get_ecs_cluster_arn(),
            task=self.get_task_arn(),
            reason=stop_reason
        )
        return response

    def sync_state(self):
        """
        Calls get_status and updates the current_state_definition and the state.

        """
        full_status = self.get_status()
        if full_status:
            status = full_status.get("lastStatus", "missing").lower()
            ecs_desired_status = full_status.get("desiredStatus", "").lower()
            container = full_status.get("containers",[{}])
            if container[0].get("exitCode", -1) == 0:
                self.set_desired_state(State.stopped)
            if status == ecs_desired_status or not ecs_desired_status:
                self.state = ECSTask.state_lookup.get(status)
            else:
                self.state = State.pending
            self.current_state_definition = full_status

    def _update(self):
        pass

    def is_state_definition_equivalent(self):
        return True

    def is_state_equivalent(self, state1, state2):
        """
        Uses equivalent_states to determine if states are equivalent.

        Args:
            state1 (State):
            state2 (State):

        Returns:
            bool
        """
        return ECSTask.equivalent_states.get(state1) == ECSTask.equivalent_states.get(state2)

    def get_desired_state_definition(self):
        """
        Calls get_task_definition_arn() and get_ecs_cluster_arn() and updates desired_state_definition.

        Returns:
            desired_state_definition
        """
        self.desired_state_definition["taskDefinitionArn"] = self.get_task_definition_arn()
        self.desired_state_definition["clusterArn"] = self.get_ecs_cluster_arn()
        self.desired_state_definition["taskArn"] = self.desired_state_definition.get("taskArn")

        return self.desired_state_definition

    def wait(self):
        """
        Default time to wait during pending state.
        """
        time.sleep(5)

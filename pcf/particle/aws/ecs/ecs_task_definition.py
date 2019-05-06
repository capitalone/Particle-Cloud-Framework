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

from botocore.errorfactory import ClientError

class ECSTaskDefinition(AWSResource):
    """
    This is the implementation of Amazon's ECS Task Definition.
    """

    flavor = "ecs_task_definition"
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

    UNIQUE_KEYS = ["aws_resource.containerDefinitions.name"]

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition, "ecs", session=session)

        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the ECS Task Definition

        """
        self.unique_keys = ECSTaskDefinition.UNIQUE_KEYS

    def get_task_definition_id(self):
        """
        Parses the current and desired state definition and returns the family. If there is a revision it appends
        it to the family.

        Returns:
             task definition id
        """
        task_definition_family = pcf_util.get_item_from_dicts("family", self.current_state_definition, self.get_desired_state_definition())
        task_definition_revision = pcf_util.get_item_from_dicts("revision", self.current_state_definition, self.get_desired_state_definition())

        if task_definition_revision:
            return "{}:{}".format(task_definition_family, task_definition_revision)
        else:
            return task_definition_family

    def get_status(self):
        """
        Calls boto3 describe_task_definition using get_task_definition_id().

        Returns:
             status or {"status":"missing"}
        """
        try:
            task_definition_status_resp = self.client.describe_task_definition(taskDefinition=self.get_task_definition_id())
            return task_definition_status_resp.get("taskDefinition", [])
        except ClientError as e:
            err_msg = e.response.get("Error", {}).get("Message")
            if err_msg and "Unable to describe task definition" in err_msg:
                return {"status": "missing"}
            else:
                raise e

        except Exception as e:
            err_msg = e.args[0]

            if err_msg and err_msg.endswith("is not a task_definition"):
                return {"status": "missing"}
            else:
                raise e

    #TODO need to add a way to get family:revision for this to work
    def _terminate(self):
        """
        Calls boto3 deregister_task_definition()

        Returns:
            boto3 deregister_task_definition() response
        """
        resp = self.client.deregister_task_definition(taskDefinition=self.get_task_definition_id())
        return resp

    def _start(self):
        """
        Calls boto3 register_task_definition()

        Returns:
           boto3 register_task_definition() response
        """
        resp = self.client.register_task_definition(**self.get_desired_state_definition())
        self.current_state_definition = resp
        return resp

    def _stop(self):
        """
        Calls _terminate()
        """
        return self._terminate()

    def _update(self):
        """
        Calls _start()
        """
        return self._start()

    def sync_state(self):
        """
        Calls get_status() and updates the current_state_definition and the state.
        """
        full_status = self.get_status()
        if full_status:
            status = full_status.get("status", "active").lower()
            self.state = ECSTaskDefinition.state_lookup.get(status)

            self.current_state_definition = full_status

    def is_state_equivalent(self, state1, state2):
        """
        Args:
            state1 (State):
            state2 (State):

        Returns:
            bool
        """
        return ECSTaskDefinition.equivalent_states.get(state1) == ECSTaskDefinition.equivalent_states.get(state2)


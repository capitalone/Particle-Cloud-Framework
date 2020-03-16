# Copyright 2018-2020 Capital One Services, LLC
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
import time
import logging

logger = logging.getLogger(__name__)

class NotebookLifecycleConfig(AWSResource):
    """
    This is the implementation of Amazon's Sagemaker Notebook lifecycle config.
    """
    flavor = "sagemaker_notebook_lifecycle_config"

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

    START_PARAM_FILTER = {
        "NotebookInstanceLifecycleConfigName",
        "OnCreate",
        "OnStart"
    }

    UPDATE_PARAM_FILTER = {
        "NotebookInstanceLifecycleConfigName",
        "OnCreate",
        "OnStart"
    }

    UNIQUE_KEYS = ["aws_resource.NotebookInstanceLifecycleConfigName"]

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition=particle_definition, resource_name="sagemaker", session=session)
        self.notebook_instance_lifecycle_config_name = self.desired_state_definition["NotebookInstanceLifecycleConfigName"]
        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the Sagemaker Notebook
        """
        self.unique_keys = NotebookLifecycleConfig.UNIQUE_KEYS

    def get_status(self):
        """
        Calls the describe notebook instance lifecycle config boto call and returns current definition

        Returns:
            status (dict)
        """
        try:
            current_definition = self.client.describe_notebook_instance_lifecycle_config(NotebookInstanceLifecycleConfigName=self.notebook_instance_lifecycle_config_name)

        except ClientError as e:
            if e.response['Error']['Code'] == 'ValidationException':
                logger.info("Notebook Lifecycle Config {} was not found. State is terminated".format(self.notebook_instance_lifecycle_config_name))
                return {"status": "missing"}
            else:
                raise e
        return current_definition

    def _start(self):
        """
        Starts the Sagemaker Notebook Lifecycle Config particle that matches desired state definition

        Returns:
            response of boto3 create_notebook_instance
        """

        start_definition = pcf_util.param_filter(self.get_desired_state_definition(), NotebookLifecycleConfig.START_PARAM_FILTER)
        return self.client.create_notebook_instance_lifecycle_config(**start_definition)

    def sync_state(self):
        """
        Sagemaker Notebook Lifecycle Config implementation of sync state. Calls get status and sets the current state.
        """
        full_status = self.get_status()

        if full_status.get("status") == "missing":
            self.state = State.terminated
            return

        self.current_state_definition = full_status
        self.state = State.running

    def _stop(self):
        """
        Sagemaker lifecycle config does not have a stopped state so it calls terminate
        """
        return self.terminate()

    def _terminate(self):
        """
        Deletes Sagemaker Notebook Lifecycle Config

        Returns:
            response of boto3 delete_notebook_instance_lifecycle_config()
        """

        return self.client.delete_notebook_instance_lifecycle_config(NotebookInstanceLifecycleConfigName=self.notebook_instance_lifecycle_config_name)

    def _update(self):
        """
        Updates Sagemaker Notebook Lifecycle Config

        Returns:
            response of boto3 update_notebook_instance_lifecycle_config()
        """
        update_definition = pcf_util.param_filter(self.get_desired_state_definition(), NotebookLifecycleConfig.UPDATE_PARAM_FILTER)
        return self.client.update_notebook_instance_lifecycle_config(**update_definition)

    def is_state_equivalent(self, state1, state2):
        """
        Compared the desired state and current state definition

        Args:
            state1 (State):
            state1 (State):

        Returns:
            bool
        """
        return NotebookLifecycleConfig.equivalent_states.get(state1) == NotebookLifecycleConfig.equivalent_states.get(state2)

    def is_state_definition_equivalent(self):
        """
        Compared the desired state and current state definition

        Returns:
            bool
        """
        self.get_state()
        self.current_state_definition = pcf_util.param_filter(self.current_state_definition, NotebookLifecycleConfig.START_PARAM_FILTER)
        desired_definition = pcf_util.param_filter(self.desired_state_definition, NotebookLifecycleConfig.START_PARAM_FILTER)

        diff_dict = pcf_util.diff_dict(self.current_state_definition, desired_definition)
        return diff_dict == {}

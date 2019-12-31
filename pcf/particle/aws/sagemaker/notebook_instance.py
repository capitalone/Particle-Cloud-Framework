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
import time
import logging

logger = logging.getLogger(__name__)

class NotebookInstance(AWSResource):
    """
    This is the implementation of Amazon's Sagemaker Notebook.
    """
    flavor = "sagemaker_notebook_instance"
    state_lookup = {
        "missing": State.terminated,
        "Pending": State.pending,
        "InService": State.running,
        "Stopping": State.pending,
        "Stopped": State.stopped,
        "Failed": State.running,
        "Deleting": State.pending,
        "Updating": State.pending
    }

    equivalent_states = {}

    START_PARAM_FILTER = {
        "NotebookInstanceName",
        "InstanceType",
        "SubnetId",
        "SecurityGroupIds",
        "RoleArn",
        "KmsKeyId",
        "LifecycleConfigName",
        "DirectInternetAccess",
        "VolumeSizeInGB",
        "AcceleratorTypes",
        "DefaultCodeRepository",
        "AdditionalCodeRepositories",
        "RootAccess",
        "Tags"
    }

    UPDATE_PARAM_FILTER = {}

    PARAM_CONVERSIONS = {
        "SecurityGroups": "SecurityGroupIds",
        "NotebookInstanceLifecycleConfigName": "LifecycleConfigName",
    }


    UNIQUE_KEYS = ["aws_resource.NotebookInstanceName"]

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition=particle_definition, resource_name="sagemaker", session=session)
        self.notebook_instance_name = self.desired_state_definition["NotebookInstanceName"]
        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the Sagemaker Notebook
        """
        self.unique_keys = NotebookInstance.UNIQUE_KEYS


    def get_status(self):
        """
        Calls the describe notebook instance boto call and returns current definition

        Returns:
            current definition
        """
        try:
            current_definition = self.client.describe_notebook_instance(NotebookInstanceName=self.notebook_instance_name)
            current_definition["Tags"] = self.client.list_tags(ResourceArn=current_definition.get("NotebookInstanceArn")).get("Tags")

        except ClientError as e:
            if e.response['Error']['Message'] == 'RecordNotFound':
                logger.info("Notebook {} was not found. State is terminated".format(self.notebook_instance_name))
                return {"NotebookInstanceName": self.notebook_instance_name,
                        "NotebookInstanceStatus": "missing"}
            else:
                raise e
        return current_definition


    def _start(self):
        """
        Starts the Sagemaker Notebook particle that matches desired state definition

        Returns:
            response of boto3 create_notebook_instance
        """
        if self.state == State.stopped:
            return self.client.start_notebook_instance(NotebookInstanceName=self.notebook_instance_name)
        else:
            start_definition = pcf_util.param_filter(self.get_desired_state_definition(), NotebookInstance.START_PARAM_FILTER)
            return self.client.create_notebook_instance(**start_definition)

    def _stop(self):
        """
        Calls boto3 Sagemaker stop_notebook_instance

        Returns:
            boto3 stop_notebook_instance response
        """
        return self.client.stop_notebook_instance(NotebookInstanceName=self.notebook_instance_name)


    def _terminate(self):
        """
        Deletes Sagemaker Notebook

        Returns:
            response of boto3 delete_notebook_instnace()
        """

        if self.state == State.running:
            self._stop()
            while True:
                if self.client.describe_notebook_instance(
                    NotebookInstanceName=self.notebook_instance_name).get("NotebookInstanceStatus") == "Stopped":
                    break
                time.sleep(10)

        return self.client.delete_notebook_instance(NotebookInstanceName=self.notebook_instance_name)

    def sync_state(self):
        """
        Sagemaker Notebook implementation of sync state. Calls get status and sets the current state.
        """
        self.current_state_definition = self.get_status()
        self.state = self.state_lookup.get(self.current_state_definition.get("NotebookInstanceStatus", "missing"))

    def _update(self):
        #Will implement later
        pass



    def is_state_definition_equivalent(self):
        """
        Compared the desired state and current state definition

        Returns:
            bool
        """
        self.get_state()
        self.current_state_definition = pcf_util.param_filter(self.current_state_definition, NotebookInstance.START_PARAM_FILTER)
        desired_definition = pcf_util.param_filter(self.desired_state_definition, NotebookInstance.START_PARAM_FILTER)

        diff_dict = pcf_util.diff_dict(self.current_state_definition, desired_definition)
        return diff_dict == {}

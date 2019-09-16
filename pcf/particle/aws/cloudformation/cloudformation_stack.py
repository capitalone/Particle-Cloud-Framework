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

from pcf.core.aws_resource import AWSResource
from pcf.core import State
from pcf.util import pcf_util
from pcf.core.pcf_exceptions import NoResourceException
import json
from botocore.errorfactory import ClientError
import logging
from jinja2 import Template

logger = logging.getLogger(__name__)

class CloudFormationStack(AWSResource):
    """
    Particle that maps to Cloudformation Stack
    """

    flavor = "cloudformation"

    PARAM_FILTER = {
        "StackName",
        "TemplateBody",
        "TemplateURL",
        "Parameters",
        "DisableRollback",
        "RollbackConfiguration",
        "TimeoutInMinutes",
        "NotificationARNs",
        "Capabilities",
        "ResourceTypes",
        "RoleARN",
        "OnFailure",
        "StackPolicyBody",
        "StackPolicyURL",
        "Tags",
        "ClientRequestToken",
        "EnableTerminationProtection"
    }

    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0,
    }
    # ['CREATE_IN_PROGRESS', 'DELETE_IN_PROGRESS', 'ROLLBACK_IN_PROGRESS', 'UPDATE_IN_PROGRESS', ]

    UNIQUE_KEYS = ["aws_resource.StackName"]

    def __init__(self, particle_definition, session=None):
        """
        Args:
            particle_definition (definition): desired configuration of the particle
        """
        super(CloudFormationStack, self).__init__(particle_definition, "cloudformation", session=session)
        self.stack_name = self.desired_state_definition["StackName"]
        if self.desired_state_definition.get('custom_config', {}).get('template_parameters', {}):
            self.render_template()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the stack
        """
        self.unique_keys = CloudFormationStack.UNIQUE_KEYS

    def _start(self):
        """
        Creates the cloudformation stack according to the particle definition

        Returns:
            stack: boto3 response
        """
        start_definition = pcf_util.param_filter(self.desired_state_definition, CloudFormationStack.PARAM_FILTER)
        response = self.client.create_stack(**start_definition)

        return response

    def _terminate(self):
        """
        Deletes the cloudformation stack using its name

        Returns:
            boto3 response
        """
        #Cannot termiante during these inprogress status: https://docs.aws.amazon.com/AWSJavaSDK/latest/javadoc/com/amazonaws/services/cloudformation/model/StackStatus.html
        try:
            response = self.client.delete_stack(StackName=self.stack_name)
        except ClientError as e:
            if 'IN_PROGRESS' in e.response['Error']['Message']:
                logger.info(f"Cannot terminate stack {self.stack_name} while update in progress")
                return
            raise e

        return response

    def _stop(self):
        """
        Calls _terminate()
        """
        return self.terminate()

    def _update(self):
        """
        Update cloudformation stack based on the new configuration provided
        """

        #Cannot update during these inprogress status: https://docs.aws.amazon.com/AWSJavaSDK/latest/javadoc/com/amazonaws/services/cloudformation/model/StackStatus.html
        try:
            update_definition = pcf_util.param_filter(self.desired_state_definition, CloudFormationStack.PARAM_FILTER)
            response = self.client.update_stack(**update_definition)
        except ClientError as e:
            if 'IN_PROGRESS' in e.response['Error']['Message']:
                logger.info(f"Cannot update stack {self.stack_name} while creation or deletion in progress")
                return
            raise e

        return response

    def get_status(self):
        
        try:
            cloudformation_resp = self.client.describe_stacks(StackName=self.stack_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ValidationError':
                logger.info(f"Cloudformation stack {self.stack_name} was not found. State is terminated")
                return {"status": "missing"}
            raise e
        return cloudformation_resp

    def sync_state(self):
        """
        Sync state calls get_status to determines and set the state of the cloudformation stack
        """
        full_status = self.get_status()

        if full_status == {"status": "missing"}:
            self.state = State.terminated
            return

        self.state = State.running
        self.current_state_definition = full_status.get("Stacks")[0]

    def is_state_definition_equivalent(self):
        """
        Compares the desired state and current state definitions.

        Returns:
            bool
        """
        self.current_state_definition = pcf_util.param_filter(self.current_state_definition, CloudFormationStack.PARAM_FILTER)

        #seperate boto call to get the cloudformation template
        response = self.client.get_template(
            StackName=self.stack_name,
            TemplateStage="Original"
        )
        # template comes back with extra quotes and extra escape \ for new lines. not sure why
        self.current_state_definition['TemplateBody'] = json.dumps(response.get('TemplateBody')).replace('\\n', '\n')[1:-1]
        filtered_desired_def = pcf_util.param_filter(self.desired_state_definition, CloudFormationStack.PARAM_FILTER)
        diff_dict = pcf_util.diff_dict(self.current_state_definition, filtered_desired_def)
        return diff_dict == {}

    def render_template(self):
        """
        Opens the userdata template file and renders the file with userdata parameters.
        Returns:
            None
        """
        template_body = self.desired_state_definition.get("TemplateBody", None)

        if template_body:
            context = self.desired_state_definition.get("custom_config", {}).get("template_parameters", {})
            template = Template(template_body)
            self.desired_state_definition["TemplateBody"] = template.render(context)


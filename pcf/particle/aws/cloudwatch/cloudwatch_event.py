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
import logging

from botocore.errorfactory import ClientError

logger = logging.getLogger(__name__)

class CloudWatchEvent(AWSResource):

    """
    This is the implementation of Amazon's CloudWatch Events service.
    """
    flavor = "cloudwatch_events"

    START_PARAM_FILTER = {
        "Name",
        "ScheduleExpression",
        "EventPattern",
        "State",
        "Description",
        "RoleArn",
    }

    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0,
    }

    UNIQUE_KEYS = ["aws_resource.Name"]

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition=particle_definition, resource_name="events", session=session)
        self.rule_name = self.desired_state_definition["Name"]
        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the log group

        """
        self.unique_keys = CloudWatchEvent.UNIQUE_KEYS

    def _terminate(self):
        """
        Terminates the events particle that matches the rule_name

        Returns:
            response of boto3 delete_function
        """
        return self.client.delete_rule(Name=self.rule_name)

    def get_status(self):
        """
        Calls the describe rule boto call and returns the

        Returns:
            current definition
        """
        try:
            current_definition = self.client.describe_rule(Name=self.rule_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.info("Rule {} was not found. State is terminated".format(self.rule_name))
                return {"status": "missing"}
            else:
                raise e
        return current_definition

    def _start(self):
        """
        Starts the events particle that matches desired state definition

        Returns:
            response of boto3 put_rule
        """
        start_definition = pcf_util.param_filter(self.get_desired_state_definition(), CloudWatchEvent.START_PARAM_FILTER)
        return self.client.put_rule(**start_definition)

    def _stop(self):
        """
        CloudWatch Events does not have a stopped state so it calls terminate

        Returns:
            response of terminate function
        """
        return self._terminate()

    def sync_state(self):
        """
        CloudWatch Events implementation of sync state. Calls get status and sets the current state.
        """
        status_def = self.get_status()
        if status_def.get("status") == "missing":
            self.state = State.terminated
            return
        self.current_state_definition = status_def
        self.state = State.running

    def _update(self):
        update_definition = pcf_util.param_filter(self.get_desired_state_definition(), CloudWatchEvent.START_PARAM_FILTER)
        self.client.put_rule(**update_definition)


    def is_state_definition_equivalent(self):
        """
        Compared the desired state and current state definition

        Returns:
            bool
        """
        self.get_state()
        self. current_state_definition = pcf_util.param_filter(self.current_state_definition, CloudWatchEvent.START_PARAM_FILTER)
        desired_definition = pcf_util.param_filter(self.desired_state_definition, CloudWatchEvent.START_PARAM_FILTER)
        diff_dict = pcf_util.diff_dict(self.current_state_definition, desired_definition)
        return diff_dict == {}

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
from botocore.exceptions import ClientError


class SNSTopic(AWSResource):

    """
    This is the implementation of Amazon's SNS.
    """
    flavor = "sns"

    START_PARAM_FILTER = {
        "Name",  # Required
        "Attributes"
    }

    DEFINITION_FILTER = {
        "Name",
        "Attributes",
    }

    START_ATTR = {
        #"DeliveryPolicy",
        "DisplayName",
        #"Policy"
    }

    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0,
    }

    UNIQUE_KEYS = ["aws_resource.Name"]

    def __init__(self, particle_definition):
        super(SNSTopic, self).__init__(particle_definition=particle_definition, resource_name="sns")
        self.topic_name = self.desired_state_definition.get("Name")
        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the sns topic

        """
        self.unique_keys = SNSTopic.UNIQUE_KEYS

    def _start(self):
        """
        Starts the SNS Topic according to the desired definition

        Returns:
            response of boto3 create_topic
        """
        start_definition = pcf_util.param_filter(self.get_desired_state_definition(), SNSTopic.START_PARAM_FILTER)
        if "Attributes" in start_definition.keys():
            start_definition["Attributes"] = pcf_util.param_filter(start_definition["Attributes"], SNSTopic.START_ATTR)
        response = self.client.create_topic(**start_definition)
        self._arn = response.get("TopicArn")
        return response

    def _terminate(self):
        """
        Terminates the Topic identified by the Topic ARN

        Returns:
            response of boto3 delete_topic
        """
        return self.client.delete_topic(TopicArn=self.arn)

    def _stop(self):
        """
        SNS does not have a stopped state so it calls terminate

        Returns:
            response of terminate function
        """
        return self._terminate()

    def get_current_definition(self):
        """
        Uses boto calls to get the Attributes for the Topic

        Returns:
            current definition if the topic exists, otherwise None
        """
        if self._arn:
            try:
                current_definition = self.client.get_topic_attributes(
                    TopicArn=self._arn
                )
                current_definition["Name"] = self.topic_name
                self.current_state_definition = current_definition
                return current_definition
            except ClientError:
                return None
        else:
            return None

    def sync_state(self):
        """
        Uses get_current_definition to determine whether the topic exists or not and sets the state

        Returns:
            void
        """
        # get the current definition. if it exists, running; if missing, terminated.
        if self.get_current_definition():
            self.state = State.running
        else:
            self.state = State.terminated

    def is_state_definition_equivalent(self):
        """
        Compared the desired state and current state definition

        Returns:
            bool
        """
        self.sync_state()
        # use filters to remove any extra information
        self.current_state_definition = pcf_util.param_filter(self.current_state_definition, SNSTopic.DEFINITION_FILTER)
        self.desired_state_definition = pcf_util.param_filter(self.desired_state_definition, SNSTopic.DEFINITION_FILTER)
        if "Attributes" in self.desired_state_definition.keys():
            self.desired_state_definition["Attributes"] = pcf_util.param_filter(
                self.desired_state_definition.get("Attributes"), SNSTopic.START_ATTR)
            # only compare attributes specified in desired, ignore all else
            self.current_state_definition["Attributes"] = pcf_util.param_filter(
                self.current_state_definition.get("Attributes"), self.desired_state_definition.get("Attributes").keys())

        diff_dict = pcf_util.diff_dict(self.current_state_definition, self.desired_state_definition)
        return diff_dict == {}

    def _update(self):
        """
        Updates any changed attributes

        Returns:
            void
        """
        # if not self.is_state_definition_equivalent():
        #     # add/update new/existing attributes, cannot remove attributes - just set/reset attr.
        #     desired_attr = self.desired_state_definition.get("Attributes")
        #     if desired_attr:
        #         for key in desired_attr:
        #             self.client.set_topic_attributes(
        #                 TopicArn=self._arn,
        #                 AttributeName=key,
        #                 AttributeValue= desired_attr[key]
        #             )
        pass


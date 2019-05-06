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


class CloudWatchLog(AWSResource):

    """
    This is the implementation of Amazon's CloudWatch Logs service.
    """
    flavor = "cloudwatch_logs"

    START_PARAM_FILTER = {
        "logGroupName",
        "kmsKeyId",
        "tags",
    }

    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0,
    }

    UNIQUE_KEYS = ["aws_resource.logGroupName"]

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition=particle_definition, resource_name="logs", session=session)
        self.group_name = self.desired_state_definition["logGroupName"]
        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the log group

        """
        self.unique_keys = CloudWatchLog.UNIQUE_KEYS

    def _start(self):
        """
        Starts the Cloudwatch Log Group according to the desired definition

        Returns:
            response of boto3 create_log_group
        """
        start_definition = pcf_util.param_filter(self.desired_state_definition, CloudWatchLog.START_PARAM_FILTER)
        return self.client.create_log_group(**start_definition)

    def _terminate(self):
        """
        Terminates the Log Group identified by the logGroupName

        Returns:
            response of boto3 delete_log_group
        """
        return self.client.delete_log_group(logGroupName=self.group_name)

    def _stop(self):
        """
        CloudWatch Logs does not have a stopped state so it calls terminate

        Returns:
            response of terminate function
        """
        return self._terminate()

    def get_current_definition(self):
        """
        Calls the describe log group boto call and returns the group's attributes

        Returns:
            current definition if the group exists, otherwise a status missing message
        """
        log_list = self.client.describe_log_groups(logGroupNamePrefix=self.group_name, limit=1).get("logGroups")
        # search list for exact name match since describe_log_groups does a prefix search
        if len(log_list) >= 1:
            for log in log_list:
                if log.get("logGroupName") == self.group_name:
                    return log
        return None

    def sync_state(self):
        """
        CloudWatch Logs implementation of sync state. Calls get current definition and sets the current state.

        Returns:
            void
        """
        # get the state. if it exists, running; if missing, terminated.
        current_definition = self.get_current_definition()
        if current_definition is None:
            self.state = State.terminated
        else:
            self.current_state_definition = current_definition
            self.state = State.running

    def is_state_definition_equivalent(self):
        """
        Compared the desired state and current state definition

        Returns:
            bool
        """
        self.sync_state()
        # remove extra information
        self.current_state_definition = pcf_util.param_filter(self.current_state_definition, CloudWatchLog.START_PARAM_FILTER)
        # get the tags and add them on (they're together when creating, but separate when retrieving)
        self.current_state_definition["tags"] = self.client.list_tags_log_group(logGroupName=
                                                                                self.group_name).get("tags")
        self.desired_state_definition = pcf_util.param_filter(self.desired_state_definition, CloudWatchLog.START_PARAM_FILTER)
        diff_dict = pcf_util.diff_dict(self.current_state_definition, self.desired_state_definition)
        return diff_dict == {}

    def _update(self):
        """
        Updates any changed tags or KMS key

        Returns:
            void
        """
        if not self.is_state_definition_equivalent():
            # remove any removed tags
            removed_tags = list(set(self.current_state_definition.get("tags")) -
                                set(self.desired_state_definition.get("tags")))
            if removed_tags is not None and len(removed_tags) > 0:
                self.client.untag_log_group(
                    logGroupName=self.group_name,
                    tags=removed_tags,
                )
            # add and update new/existing tags
            desired_tags = self.desired_state_definition.get("tags")
            if desired_tags is not None and len(desired_tags) > 0:
                self.client.tag_log_group(
                    logGroupName=self.group_name,
                    tags=desired_tags
                )
            current_key = self.current_state_definition.get("kmsKeyId")
            desired_key = self.desired_state_definition.get("kmsKeyId")
            if current_key != desired_key:
                # remove key if it is no longer defined
                if desired_key is None or desired_key == "":
                    self.client.disassociate_kms_key(
                        logGroupName=self.group_name
                    )
                else:
                    # update or add key if applicable
                    self.client.associate_kms_key(
                        logGroupName=self.group_name,
                        kmsKeyId=desired_key
                    )

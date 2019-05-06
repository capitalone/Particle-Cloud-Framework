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


class SQSQueue(AWSResource):

    """
    This is the implementation of Amazon's SQS.
    """
    flavor = "sqs_queue"

    START_PARAM_FILTER = {
        "QueueName",  # Required
        "Attributes"
    }

    DEFINITION_FILTER = {
        "QueueName",
        "Attributes",
        "Tags"
    }

    START_ATTR = {
        "DelaySeconds",
        "MaximumMessageSize",
        "MessageRetentionPeriod",
        "Policy",
        "ReceiveMessageWaitTimeSeconds",
        "RedrivePolicy",
        "VisibilityTimeout",
        "KmsMasterKeyId",
        "KmsDataKeyReusePeriodSeconds",
        "FifoQueue",
        "ContentBasedDeduplication",
        "ApproximateNumberOfMessages",
        "ApproximateNumberOfMessagesDelayed",
        "ApproximateNumberOfMessagesNotVisible",
        "CreatedTimestamp",
        "LastModifiedTimestamp",
        "QueueArn"
    }

    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0,
    }

    UNIQUE_KEYS = ["aws_resource.QueueName"]

    def __init__(self, particle_definition, session=None):
        super(SQSQueue, self).__init__(particle_definition=particle_definition, resource_name="sqs", session=session)
        self.queue_name = self.desired_state_definition.get("QueueName")
        self._set_unique_keys()
        self._set_url(self.desired_state_definition.get("OwnerAwsId"))

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the sqs queue

        """
        self.unique_keys = SQSQueue.UNIQUE_KEYS

    def _set_url(self, owner):
        """
        Used when making changes or terminating pre-existing queue
        handles queues created by other accounts

        Params:
            owner: queue owner's AWS ID

        Returns:
            void
        """
        try:
            if owner:
                self.queue_url = self.client.get_queue_url(
                    QueueName=self.queue_name,
                    QueueOwnerAWSAccountId=owner
                )
            else:
                self.queue_url = self.client.get_queue_url(QueueName=self.queue_name)["QueueUrl"]
        except ClientError:
            self.queue_url = None

    def _start(self):
        """
        Starts the SQS Queue according to the desired definition

        Returns:
            response of boto3 create_queue
        """
        start_definition = pcf_util.param_filter(self.get_desired_state_definition(), SQSQueue.START_PARAM_FILTER)
        if "Attributes" in start_definition.keys():
            start_definition["Attributes"] = pcf_util.param_filter(start_definition["Attributes"], SQSQueue.START_ATTR)
        response = self.client.create_queue(**start_definition)
        self.queue_url = response["QueueUrl"]
        if self.desired_state_definition.get("Tags"):
            self.client.tag_queue(
                QueueUrl=self.queue_url,
                Tags=self.desired_state_definition.get("Tags")
            )
        return response

    def _terminate(self):
        """
        Terminates the Queue identified by the Queue Name and optionally the Queue Owner

        Returns:
            response of boto3 delete_queue
        """
        return self.client.delete_queue(QueueUrl=self.queue_url)

    def _stop(self):
        """
        SQS does not have a stopped state so it calls terminate

        Returns:
            response of terminate function
        """
        return self._terminate()

    def get_current_definition(self):
        """
        Uses boto calls to get the Attributes and Tags for the Queue

        Returns:
            current definition if the queue exists, otherwise None
        """
        if self.queue_url:
            try:
                current_definition = self.client.get_queue_attributes(
                    QueueUrl=self.queue_url,
                    AttributeNames=['All']
                )
                current_definition["QueueName"] = self.queue_name
                current_definition["Tags"] = self.client.list_queue_tags(QueueUrl=self.queue_url)["Tags"]
                self.current_state_definition = current_definition
                return current_definition
            except ClientError:
                return None
        else:
            return None

    def sync_state(self):
        """
        Uses get_current_definition to determine whether the queue exists or not and sets the state

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
        self.current_state_definition = pcf_util.param_filter(self.current_state_definition, SQSQueue.DEFINITION_FILTER)
        self.desired_state_definition = pcf_util.param_filter(self.desired_state_definition, SQSQueue.DEFINITION_FILTER)
        self.desired_state_definition["Attributes"] = pcf_util.param_filter(
            self.desired_state_definition.get("Attributes"), SQSQueue.START_ATTR)
        # only compare attributes specified in desired, ignore all else
        self.current_state_definition["Attributes"] = pcf_util.param_filter(
            self.current_state_definition.get("Attributes"), self.desired_state_definition.get("Attributes").keys())

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
            removed_tags = list(set(self.current_state_definition.get("Tags")) -
                                set(self.desired_state_definition.get("Tags")))
            if removed_tags:
                self.client.untag_queue(
                    QueueUrl=self.queue_url,
                    TagKeys=removed_tags
                )
            # add and update new/existing tags
            desired_tags = self.desired_state_definition.get("Tags")
            if desired_tags:
                self.client.tag_queue(
                    QueueUrl=self.queue_url,
                    Tags=desired_tags
                )
            # adding and updating for changed attributes. cannot remove attributes - just set
            # add and update new/existing attr. cannot remove attributes - just set/reset
            desired_attr = self.desired_state_definition.get("Attributes")
            if desired_attr:
                self.client.set_queue_attributes(
                    QueueUrl=self.queue_url,
                    Attributes=desired_attr
                )


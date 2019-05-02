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

import moto
import boto3

from pcf.particle.aws.sqs.sqs_queue import SQSQueue
from pcf.core import State


class TestSQS:
    particle_definition = {
        "pcf_name": "gg-pcf",
        "flavor": "sqs_queue",
        "aws_resource": {
            "QueueName": "test_SQS_queue.fifo",  # Required
            # "OwnerAwsId": "owner", # only if the queue belongs to a different user
            "Attributes": {
                # https://boto3.readthedocs.io/en/latest/reference/services/sqs.html#SQS.Client.create_queue
                # for all the validation criteria from boto3
                "DelaySeconds": "0",
                "MaximumMessageSize": "262144",
                "MessageRetentionPeriod": "345600",
                "Policy": "AWS policy",
                "ReceiveMessageWaitTimeSeconds": "20",
                # "RedrivePolicy": "{}",
                "VisibilityTimeout": "43200",
                "KmsMasterKeyId": "enc/sqs",
                "KmsDataKeyReusePeriodSeconds": "300",
                "FifoQueue": "true",
                "ContentBasedDeduplication": "true",
                # "ApproximateNumberOfMessages": "1",
                # "ApproximateNumberOfMessagesDelayed": "0",
                # "ApproximateNumberOfMessagesNotVisible": "0",
                # "CreatedTimestamp": "1534276486.369445",
                # "LastModifiedTimestamp": "1534276486.369445",
                "QueueArn": "arn:aws:sqs:us-east-1:123456789012:test_SQS_queue.fifo"
            },
            "Tags": {
                "test_tag": "value",
                "remove_tag": "bye"
            }
        }
    }


    @moto.mock_sqs
    def test_apply_states(self):
        particle = SQSQueue(self.particle_definition)

        # Test start
        particle.set_desired_state(State.running)
        particle.apply()

        assert particle.is_state_definition_equivalent()
        assert particle.get_state() == State.running

        # Test update
        self.particle_definition["aws_resource"]["Attributes"]["MaximumMessageSize"] = "262143" # reset existing
        self.particle_definition["aws_resource"]["Attributes"]["ContentBasedDeduplication"] = "false" # add new
        self.particle_definition["aws_resource"]["Tags"]["new_tag"] = "new" # new tag
        self.particle_definition["aws_resource"]["Tags"]["test_tag"] = "changed" # reset tag
        self.particle_definition["aws_resource"]["Tags"].pop("remove_tag") # remove tag
        particle = SQSQueue(self.particle_definition)

        particle.set_desired_state(State.running)
        particle.apply()

        assert particle.is_state_definition_equivalent()
        assert particle.get_state() == State.running

        # Test terminate
        particle.set_desired_state(State.terminated)
        particle.apply()

        assert particle.get_state() == State.terminated

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
from pcf.core import State
import placebo
import boto3
import os

from pcf.particle.aws.sns.sns_topic import SNSTopic

class TestSNSTopic:
    PATH = "replay"
    PARTICLE = SNSTopic
    DEF = {
            "pcf_name": "pcf_sns_test",  # Required
            "flavor": "sns_topic",  # Required
            "aws_resource": {
                # Refer to https://boto3.amazonaws.com/v1/documentation/api/1.9.5/reference/services/sns.html#SNS.Client.create_topic for more information
                "Name": "pcf-sns-test",  # Required
                "Attributes": {  # optional - attributes will be set to default values if not specified
                    # "DeliveryPolicy": "", # HTTP|HTTPS|Email|Email-JSON|SMS|Amazon SQS|Application|AWS Lambda
                    "DisplayName": "pcf-test"
                    # "Policy": "" # dict
                },
                "custom_config": {
                    # Refer to https://boto3.amazonaws.com/v1/documentation/api/1.9.5/reference/services/sns.html#SNS.Client.subscribe for a full list of parameters
                    # "Subscription": { # optional
                    #     "Protocol": "", # Required - http|https|email|email-json|sms|sqs|application|lambda
                    #     "Endpoint": "", # http|https|email|email-json|sms|sqs|application|lambda
                    #     "Attributes": {}, # dict
                    #     # "ReturnSubscriptionArn": false # boolean - default=false
                    # }
                }
            }
        }
    UPDATED_DEF = {
            "pcf_name": "pcf_sns_test",  # Required
            "flavor": "sns_topic",  # Required
            "aws_resource": {
                # Refer to https://boto3.amazonaws.com/v1/documentation/api/1.9.5/reference/services/sns.html#SNS.Client.create_topic for more information
                "Name": "pcf-sns-test",  # Required
                "Attributes": {  # optional - attributes will be set to default values if not specified
                    # "DeliveryPolicy": "", # HTTP|HTTPS|Email|Email-JSON|SMS|Amazon SQS|Application|AWS Lambda
                    "DisplayName": "new-pcf-test"
                    # "Policy": "" # dict
                },
                "custom_config": {
                    # Refer to https://boto3.amazonaws.com/v1/documentation/api/1.9.5/reference/services/sns.html#SNS.Client.subscribe for a full list of parameters
                    # "Subscription": { # optional
                    #     "Protocol": "", # Required - http|https|email|email-json|sms|sqs|application|lambda
                    #     "Endpoint": "", # http|https|email|email-json|sms|sqs|application|lambda
                    #     "Attributes": {}, # dict
                    #     # "ReturnSubscriptionArn": false # boolean - default=false
                    # }
                }
            }
        }
############################################################################

    def test_apply_states(self):
        session = boto3.Session()
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, self.PATH)
        pill = placebo.attach(session, data_path=filename)
        pill.playback()

        particle = self.PARTICLE(self.DEF, session)

        # Test start

        particle.set_desired_state(State.running)
        particle.apply(sync=True)

        print(particle.get_state() == State.running)
        print(particle.is_state_definition_equivalent())

        assert particle.get_state() == State.running

        # Test update
        if self.UPDATED_DEF:
            particle = self.PARTICLE(self.UPDATED_DEF, session)
            particle.set_desired_state(State.running)
            particle.apply(sync=True)
            print(particle.is_state_definition_equivalent())
            assert particle.is_state_definition_equivalent() == True

        # Test Terminate

        particle.set_desired_state(State.terminated)
        particle.apply(sync=True)

        print(particle.get_state() == State.terminated)
        assert particle.get_state() == State.terminated
        pill.stop()

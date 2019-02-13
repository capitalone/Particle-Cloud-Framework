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

from pcf.particle.aws.sns.sns import SNSTopic
from pcf.core import State

class TestSNS:
    particle_definition = {
        "pcf_name": "pcf_sns_test", # Required
        "flavor":"sns", # Required
        "aws_resource":{
            "Name":"pcf-sns-test", # Required
            "custom_config": {
                "Attributes": {
                    # "DeliveryPolicy": "", # HTTP|HTTPS|Email|Email-JSON|SMS|Amazon SQS|Application|AWS Lambda
                    "DisplayName": "pcf-test"
                    # "Policy": "" # dict
                },
                # subscription parameters
            }
        }
    }

    @moto.mock_sns
    def test_apply_states(self):
        particle = SNSTopic(self.particle_definition)

        # Test start
        particle.set_desired_state(State.running)
        particle.apply()

        assert particle.is_state_definition_equivalent()
        assert particle.get_state() == State.running

        # example update topic attributes
        updated_def = self.particle_definition
        updated_def["aws_resource"]["Attributes"]["DisplayName"] = "new-pcf-test" # reset existing
        sns = SNSTopic(updated_def)
        sns.set_desired_state(State.running)
        sns.apply()

        # Test terminate
        particle.set_desired_state(State.terminated)
        particle.apply()

        assert particle.get_state() == State.terminated

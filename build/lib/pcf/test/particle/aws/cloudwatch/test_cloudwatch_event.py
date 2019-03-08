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

from pcf.particle.aws.cloudwatch.cloudwatch_event import CloudWatchEvent
from pcf.core import State

class TestCloudWatchEvent():
    particle_definition = {
        "pcf_name": "pcf_cloudwatch_event", #Required
        "flavor": "cloudwatch_events", #Required
        "aws_resource": {
            # Refer to https://boto3.readthedocs.io/en/latest/reference/services/events.html#CloudWatchEvents.Client.put_rule for a full list of parameters
            "Name": "pcf_test_events", #Required
            "ScheduleExpression": "rate(5 minutes)", #Required
            "State": "ENABLED", #Required
            "Description": "pcf cloudwatch events",
        }
    }


    @moto.mock_events
    def test_apply_states(self):
        particle = CloudWatchEvent(self.particle_definition)

        #Test start
        particle.set_desired_state(State.running)
        particle.apply()

        assert particle.get_state() == State.running
        assert particle.get_current_state_definition() == particle.get_desired_state_definition()

        # Test update
        self.particle_definition["aws_resource"]["State"] = 'DISABLED'
        particle = CloudWatchEvent(self.particle_definition)

        particle.set_desired_state(State.running)
        particle.apply()

        assert particle.get_current_state_definition() == particle.get_desired_state_definition()
        assert particle.get_state() == State.running

        #Test terminate
        particle.set_desired_state(State.terminated)
        particle.apply()

        assert particle.get_state() == State.terminated


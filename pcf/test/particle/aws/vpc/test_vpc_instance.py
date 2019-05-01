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

from pcf.particle.aws.vpc.vpc_instance import VPCInstance
from pcf.core import State


class TestVPC:
    particle_definition = {
        "pcf_name": "pcf_vpc",
        "flavor": "vpc_instance",
        "aws_resource": {
            "custom_config":{
                "vpc_name":"test"
            },
            "CidrBlock":"10.0.0.0/16"
        }
    }

    @moto.mock_ec2
    def test_apply_states(self):
        particle = VPCInstance(self.particle_definition)

        # Test start

        particle.set_desired_state(State.running)
        particle.apply(sync=True)

        assert particle.get_state() == State.running

        # Test Terminate

        particle.set_desired_state(State.terminated)
        particle.apply(sync=True)

        assert particle.get_state() == State.terminated


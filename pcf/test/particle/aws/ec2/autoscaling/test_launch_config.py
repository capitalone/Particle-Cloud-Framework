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

from pcf.particle.aws.ec2.autoscaling.launch_configuration import LaunchConfiguration
from pcf.core import State


class TestLaunchConfiguration():

    particle_definition = {
        "pcf_name": "lc-test",
        "flavor": "launch_configuration",
        "aws_resource": {
            "LaunchConfigurationName": "lc-test",
            "InstanceType": "t2.nano",
            "KeyName": "test-key",
            "IamInstanceProfile": "test-role",
            "ImageId":"test-id"
        }
    }

    @moto.mock_autoscaling
    def test_get_current_def(self):
        asg = LaunchConfiguration(self.particle_definition)
        des_def = asg.desired_state_definition

        assert self.particle_definition['aws_resource'] == des_def

    @moto.mock_autoscaling
    def test_get_status(self):
        conn = boto3.client('autoscaling', region_name='us-east-1')
        conn.create_launch_configuration(LaunchConfigurationName='lc-test')

        particle = LaunchConfiguration(self.particle_definition)
        status = particle.get_status()

        assert status[0].get('LaunchConfigurationName') == 'lc-test'

    @moto.mock_autoscaling
    def test_apply_states(self):
        conn = boto3.client('autoscaling', region_name='us-east-1')
        conn.create_launch_configuration(LaunchConfigurationName='lc-test')

        particle = LaunchConfiguration(self.particle_definition)

        # Test start
        particle.set_desired_state(State.running)
        particle.apply(sync=False)

        assert particle.get_state() == State.running

        # Test Terminate
        particle.set_desired_state(State.terminated)
        particle.apply()

        assert particle.get_state() == State.terminated

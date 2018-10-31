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
from unittest import TestCase
from pcf.particle.aws.ec2.autoscaling.auto_scaling_group import AutoScalingGroup
from pcf.core import State, pcf_exceptions


class TestAutoScalingGroup(TestCase):

    particle_definition = {
        "pcf_name": "asg-test",
        "flavor": "auto_scaling_group",
        "aws_resource": {
            "AutoScalingGroupName": "asg-test",
            "LaunchConfigurationName": "TestLC",
            "MinSize": 1,
            "MaxSize": 3,
            "VPCZoneIdentifier": 'VPCZoneIdentifier'
        }
    }
    incorrect_particle_definition = {
        "pcf_name": "asg-test",
        "flavor": "auto_scaling_group",
    }

    @moto.mock_autoscaling
    def test_get_current_def(self):
        asg = AutoScalingGroup(self.particle_definition)
        des_def = asg.desired_state_definition

        assert self.particle_definition['aws_resource'] == des_def

    @moto.mock_autoscaling
    def test_get_status(self):
        mocked_networking = self.setup_networking()
        conn = boto3.client('autoscaling', region_name='us-east-1')
        conn.create_launch_configuration(LaunchConfigurationName='TestLC')
        conn.create_auto_scaling_group(AutoScalingGroupName='asg-test',
                                       MinSize=1,
                                       MaxSize=3,
                                       LaunchConfigurationName='TestLC',
                                       VPCZoneIdentifier=mocked_networking['subnet1'])

        particle = AutoScalingGroup(self.particle_definition)
        status = particle.get_status()

        assert status[0].get('AutoScalingGroupName') == 'asg-test'

    @moto.mock_autoscaling
    def test_apply_states(self):
        conn = boto3.client('autoscaling', region_name='us-east-1')
        conn.create_launch_configuration(LaunchConfigurationName='TestLC')

        particle = AutoScalingGroup(self.particle_definition)

        # Test start
        particle.set_desired_state(State.running)
        particle.apply(sync=False)

        assert particle.get_state() == State.running

        # Test Update
        self.particle_definition["aws_resource"]["MaxSize"] = 2

        particle = AutoScalingGroup(self.particle_definition)
        particle.set_desired_state(State.running)
        particle.apply(sync=True)

        assert particle.get_state() == State.running
        assert particle.current_state_definition['MaxSize'] == particle.desired_state_definition['MaxSize']
        assert particle.is_state_definition_equivalent()

        # Test Terminate
        particle.set_desired_state(State.terminated)
        particle.apply()

        assert particle.get_state() == State.terminated

    @moto.mock_ec2
    def setup_networking(self):
        ec2 = boto3.resource('ec2', region_name='us-east-1')
        vpc = ec2.create_vpc(CidrBlock='10.11.0.0/16')
        subnet1 = ec2.create_subnet(
            VpcId=vpc.id,
            CidrBlock='10.11.1.0/24',
            AvailabilityZone='us-east-1a')
        subnet2 = ec2.create_subnet(
            VpcId=vpc.id,
            CidrBlock='10.11.2.0/24',
            AvailabilityZone='us-east-1b')

        return {'vpc': vpc.id, 'subnet1': subnet1.id, 'subnet2': subnet2.id}

    @moto.mock_autoscaling
    def test_incorrect_definitions(self):

        # Test missing AWS resource definition
        self.assertRaises(pcf_exceptions.InvalidUniqueKeysException, AutoScalingGroup, self.incorrect_particle_definition)

        # Test missing required field AutoScalingGroupName

        self.incorrect_particle_definition["aws_resource"]={}

        self.assertRaises(pcf_exceptions.InvalidUniqueKeysException, AutoScalingGroup,
                          self.incorrect_particle_definition)

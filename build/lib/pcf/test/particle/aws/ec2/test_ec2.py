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

from pcf.particle.aws.ec2.ec2_instance import EC2Instance
from pcf.core import State


class TestEC2():
    particle_definition = {
        "pcf_name": "gg-pcf",
        "flavor": "ec2_instance",
        "aws_resource": {
            "custom_config":{
                "instance_name":"gg-instance",
            },
            "ImageId": "ami-12345678",
            "InstanceType": "m4.large",
            "KeyName": "secret-key",
            "MaxCount": 1,
            "MinCount": 1,
            "SecurityGroupIds": [
                "test_sg",
            ],
            "SubnetId": "subnet-ab123",
            "IamInstanceProfile": {
                "Arn": "arn:aws:iam::123456789012:instance-profile/ecsInstanceRole"
            },
            "InstanceInitiatedShutdownBehavior": "stop",
            "tags": {
                "Test": "Tag"
            }
        }
    }



### refactor ec2 to not require userdata

    @moto.mock_ec2
    def test_apply_states(self):
        ec2_client = boto3.client('ec2', 'us-east-1')
        vpc = ec2_client.create_vpc(CidrBlock='10.0.0.0/16')['Vpc']
        subnet1 = ec2_client.create_subnet(VpcId=vpc['VpcId'], CidrBlock='10.1.0.0/24')['Subnet']['SubnetId']
        self.particle_definition["aws_resource"]["SubnetId"] = subnet1
        ec2_client.create_security_group(
            Description='test',
            GroupName='test_sg'
        )

        particle = EC2Instance(self.particle_definition)

        # Test start

        particle.set_desired_state(State.running)
        particle.apply()

        # assert particle.get_current_state_definition() == particle.get_desired_state_definition()
        assert particle.get_state() == State.running

        # Test Update

        # self.particle_definition["aws_resource"]["InstanceType"] = "t2.nano"
        #
        # particle = EC2Instance(self.particle_definition)
        # particle.set_desired_state(State.running)
        # particle.apply()
        #
        # assert particle.get_current_state_definition() == particle.get_desired_state_definition()
        # assert particle.get_state() == State.running

        # Test Terminate

        particle.set_desired_state(State.terminated)
        particle.apply(sync=False)

        assert particle.get_state() == State.terminated

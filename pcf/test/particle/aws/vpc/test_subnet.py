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

from pcf.particle.aws.vpc.vpc_instance import VPCInstance
from pcf.core.quasiparticle import Quasiparticle
from pcf.particle.aws.vpc.subnet import Subnet
from pcf.core import State


class TestSubnet:
    particle_definition = {
        "pcf_name": "pcf_subnet",
        "flavor": "subnet",
        "aws_resource": {
            "custom_config":{
                "subnet_name":"test"
            },
            "CidrBlock":"10.0.0.0/24",
            "VpcId":"CREATED IN TEST"
        }
    }

    vpc_parent_quasiparticle ={
        "pcf_name": "subnet_with_parent",
        "flavor": "quasiparticle",
        "particles":[
            {
                "flavor": "vpc_instance",
                "pcf_name":"vpc_parent",
                "aws_resource": {
                "custom_config":{
                "vpc_name":"test"
                },
                "CidrBlock":"10.0.0.0/16"
                }
            },
            {
                "flavor": "subnet",
                "parents":["vpc_instance:vpc_parent"],
                "aws_resource": {
                    "custom_config":{
                        "subnet_name":"test",
                        "Tags":[{"Key":"Name","Value":"test"}]
                    },
                    "CidrBlock":"10.0.0.0/24"
                }
            }
        ]
    }

    @moto.mock_ec2
    def test_apply_states(self):
        # create vpc

        ec2_client = boto3.client('ec2', 'us-east-1')
        vpc = ec2_client.create_vpc(CidrBlock='10.0.0.0/16')

        # define particle

        self.particle_definition["aws_resource"]["VpcId"] = vpc["Vpc"]['VpcId']
        particle = Subnet(self.particle_definition)

        # Test start

        particle.set_desired_state(State.running)
        particle.apply(sync=True)

        assert particle.get_state() == State.running

        # Test Terminate

        particle.set_desired_state(State.terminated)
        particle.apply(sync=True)

        assert particle.get_state() == State.terminated

    @moto.mock_ec2
    def test_vpc_parent(self):

        quasiparticle = Quasiparticle(self.vpc_parent_quasiparticle)

        # Test start

        quasiparticle.set_desired_state(State.running)
        quasiparticle.apply(sync=True)

        assert quasiparticle.get_state() == State.running
        assert quasiparticle.get_particle("subnet","subnet_with_parent").get_state() == State.running

        # Test Terminate

        quasiparticle.set_desired_state(State.terminated)
        quasiparticle.apply(sync=True)

        assert quasiparticle.get_state() == State.terminated

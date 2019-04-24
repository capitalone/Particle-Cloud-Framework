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

from pcf.core.quasiparticle import Quasiparticle
from pcf.core import State
from pcf.particle.aws.vpc.security_group import SecurityGroup
from pcf.particle.aws.vpc.vpc_instance import VPCInstance


class TestSecurityGroup:
    particle_definition = {
        "pcf_name": "pcf_sg",
        "flavor": "security_group",
        "aws_resource": {
            "Description": "pcf security group",
            "GroupName": "hoos_security_group",
            "VpcId": "vpc-abc",
            "DryRun": False,
            "custom_config": {
                "Tags": [
                    {
                        "Key": "Owner",
                        "Value": "Hoos"
                    }
                ],
                "IpPermissionsEgress": [],
                "IpPermissions": [
                    {
                        "FromPort": 80,
                        "IpProtocol": "tcp",
                        "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                        "ToPort": 80,
                        # "Ipv6Ranges": [],
                        # "PrefixListIds": [],
                        "UserIdGroupPairs": []
                    },
                ]
            }
        }
    }

    vpc_parent_quasiparticle = {
        "pcf_name": "sg_with_parent_vpc",
        "flavor": "quasiparticle",
        "particles": [
            {
                "flavor": "vpc_instance",
                "pcf_name": "vpc_parent",
                "aws_resource": {
                    "custom_config": {
                        "vpc_name": "test"
                    },
                    "CidrBlock": "10.0.0.0/16"
                }
            },
            {
                "flavor": "security_group",
                "parents": ["vpc_instance:vpc_parent"],
                "aws_resource": {
                    "Description": "pcf security group",
                    "GroupName": "Hoos",
                    "DryRun": False,
                    "custom_config": {
                        "Tags": [
                            {
                                "Key": "Owner",
                                "Value": "Hoos"
                            }
                        ],
                        "IpPermissionsEgress": [],
                        "IpPermissions": []
                    }
                }
            }
        ]
    }

    @moto.mock_ec2
    def test_apply_states(self):
        # test start
        sg = SecurityGroup(self.particle_definition)
        sg.set_desired_state(State.running)
        sg.apply()
        assert sg.get_state() == State.running
        # test update
        # changed and added tags
        self.particle_definition["aws_resource"]["custom_config"]["Tags"][0]["Value"] = "WaHoo"
        self.particle_definition["aws_resource"]["custom_config"]["Tags"].append({
            "Key": "PCF",
            "Value": "pcf"
        })
        # new rules
        self.particle_definition["aws_resource"]["custom_config"]["IpPermissionsEgress"] = [
            {
                "FromPort": 80,
                "IpProtocol": "tcp",
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                "ToPort": 80,
                # "Ipv6Ranges": [],
                # "PrefixListIds": [],
                "UserIdGroupPairs": []
            }
        ]
        # changed and added rule
        self.particle_definition["aws_resource"]["custom_config"]["IpPermissions"] = [
            {
                "FromPort": 80,
                "IpProtocol": "tcp",
                "IpRanges": [{"CidrIp": "0.0.0.0/16"}],
                "ToPort": 80,
                # "Ipv6Ranges": [],
                # "PrefixListIds": [],
                "UserIdGroupPairs": []
            },
            {
                "FromPort": 9090,
                "IpProtocol": "udp",
                "IpRanges": [{"CidrIp": "0.0.0.0/32"}],
                "ToPort": 9090,
                # "Ipv6Ranges": [],
                # "PrefixListIds": [],
                "UserIdGroupPairs": []
            }
        ]
        sg.set_desired_state(State.running)
        sg.apply()
        assert sg.is_state_definition_equivalent()

        sg.set_desired_state(State.terminated)
        sg.apply()
        assert sg.get_state() == State.terminated

    @moto.mock_ec2
    def test_vpc_parent(self):
        quasiparticle = Quasiparticle(self.vpc_parent_quasiparticle)

        # Test start

        quasiparticle.set_desired_state(State.running)
        quasiparticle.apply(sync=True)

        assert quasiparticle.get_state() == State.running
        assert quasiparticle.get_particle("security_group", "sg_with_parent_vpc").get_state() == State.running

        # Test Terminate

        quasiparticle.set_desired_state(State.terminated)
        quasiparticle.apply(sync=True)

        assert quasiparticle.get_state() == State.terminated


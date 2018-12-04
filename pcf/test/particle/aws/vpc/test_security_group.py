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

from pcf.particle.aws.vpc.security_group import SecurityGroup
from pcf.core import State


class TestVPC:
    particle_definition = {
        "pcf_name": "pcf_sg",
        "flavor": "security_group",
        "aws_resource": {
            "Description": "pcf security group",
            "GroupName": "hoos_security_group",
            "VpcId": "vpc-0e46163f7b74ae6ec",
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

    @moto.mock_ec2
    def test_apply_states(self):
        #test start
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


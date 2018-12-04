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

from pcf.particle.aws.vpc.security_group import SecurityGroup
from pcf.core import State

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
            # IpPermissionsEgress must be empty list to delete existing rules
            "IpPermissionsEgress": [
                # {
                #     "FromPort": 123,
                #     "IpProtocol": "string",
                #     "IpRanges": [
                #         {
                #             "CidrIp": "string",
                #             "Description": "string"
                #         },
                #     ],
                #     "Ipv6Ranges": [
                #         {
                #             "CidrIpv6": "string",
                #             "Description": "string"
                #         },
                #     ],
                #     "PrefixListIds": [
                #         {
                #             "Description": "string",
                #             "PrefixListId": "string"
                #         },
                #     ],
                #     "ToPort": 123,
                #     "UserIdGroupPairs": [
                #         {
                #             "Description": "string",
                #             "GroupId": "string",
                #             "GroupName": "string",
                #             "PeeringStatus": "string",
                #             "UserId": "string",
                #             "VpcId": "string",
                #             "VpcPeeringConnectionId": "string"
                #         },
                #     ]
                # }
            ],
            # IpPermissions must be empty list to delete existing rules
            "IpPermissions":  [
                {
                    "FromPort": 80,
                    "IpProtocol": "tcp",
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                    "ToPort": 80,
                    "Ipv6Ranges": [
                        # {
                        #     "CidrIpv6": "string",
                        #     "Description": "string"
                        # },
                    ],
                    "PrefixListIds": [
                        # {
                        #     "Description": "string",
                        #     "PrefixListId": "string"
                        # },
                    ],
                    "UserIdGroupPairs": [
                        # {
                        #     "Description": "string",
                        #     "GroupId": "string",
                        #     "GroupName": "string",
                        #     "PeeringStatus": "string",
                        #     "UserId": "string",
                        #     "VpcId": "string",
                        #     "VpcPeeringConnectionId": "string"
                        # },
                    ]
                },
            ]
        }
    }
}

sg = SecurityGroup(particle_definition)
sg.set_desired_state(State.running)
sg.apply()

print(sg.get_state())
print(sg.get_current_state_definition())
# changed and added tags
particle_definition["aws_resource"]["custom_config"]["Tags"][0]["Value"] = "WaHoo"
particle_definition["aws_resource"]["custom_config"]["Tags"].append({
    "Key": "PCF",
    "Value": "pcf"
})
# new rules
particle_definition["aws_resource"]["custom_config"]["IpPermissionsEgress"] = [
    {
        "FromPort": 80,
        "IpProtocol": "tcp",
        "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
        "ToPort": 80,
        "Ipv6Ranges": [],
        "PrefixListIds": [],
        "UserIdGroupPairs": []
    }
]
# changed and added rule
particle_definition["aws_resource"]["custom_config"]["IpPermissions"] = [
    {
        "FromPort": 80,
        "IpProtocol": "tcp",
        "IpRanges": [{"CidrIp": "0.0.0.0/16"}],
        "ToPort": 80,
        "Ipv6Ranges": [],
        "PrefixListIds": [],
        "UserIdGroupPairs": []
    },
    {
        "FromPort": 9090,
        "IpProtocol": "udp",
        "IpRanges": [{"CidrIp": "0.0.0.0/32"}],
        "ToPort": 9090,
        "Ipv6Ranges": [],
        "PrefixListIds": [],
        "UserIdGroupPairs": []
    }
]
sg.set_desired_state(State.running)
sg.apply()

print(sg.get_state())
print(sg.get_current_state_definition())

sg.set_desired_state(State.terminated)
sg.apply()


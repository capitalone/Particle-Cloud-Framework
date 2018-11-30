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

from pcf.particle.aws.vpc.security_group.security_group import SecurityGroup
from pcf.core import State

particle_definition = {
    "pcf_name": "pcf_sg",
    "flavor": "security_group",
    "aws_resource": {
        "Description": "pcf security group",
        "GroupName": "test_security_group",
        "VpcId": "vpc-0e46163f7b74ae6ec",
        "DryRun": False,
        "custom_config": {
            "Tags": [
                {
                    "Key": "Owner",
                    "Value": "Brian"
                }
            ],
        #     "Outbound": [
        #         {
        #             "FromPort": 123,
        #             "IpProtocol": "string",
        #             "IpRanges": [
        #                 {
        #                     "CidrIp": "string",
        #                     "Description": "string"
        #                 },
        #             ],
        #             "Ipv6Ranges": [
        #                 {
        #                     "CidrIpv6": "string",
        #                     "Description": "string"
        #                 },
        #             ],
        #             "PrefixListIds": [
        #                 {
        #                     "Description": "string",
        #                     "PrefixListId": "string"
        #                 },
        #             ],
        #             "ToPort": 123,
        #             "UserIdGroupPairs": [
        #                 {
        #                     "Description": "string",
        #                     "GroupId": "string",
        #                     "GroupName": "string",
        #                     "PeeringStatus": "string",
        #                     "UserId": "string",
        #                     "VpcId": "string",
        #                     "VpcPeeringConnectionId": "string"
        #                 },
        #             ]
        #         }
        #     ],
            "Inbound":  [
                {
                    "FromPort": 80,
                    "IpProtocol": "tcp",
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                    "ToPort": 80
        #             "Ipv6Ranges": [
        #                 {
        #                     "CidrIpv6": "string",
        #                     "Description": "string"
        #                 },
        #             ],
        #             "PrefixListIds": [
        #                 {
        #                     "Description": "string",
        #                     "PrefixListId": "string"
        #                 },
        #             ],
        #             "UserIdGroupPairs": [
        #                 {
        #                     "Description": "string",
        #                     "GroupId": "string",
        #                     "GroupName": "string",
        #                     "PeeringStatus": "string",
        #                     "UserId": "string",
        #                     "VpcId": "string",
        #                     "VpcPeeringConnectionId": "string"
        #                 },
        #             ]
                },
            ]
        }
    }
}

sg = SecurityGroup(particle_definition)
print(sg.get_current_definition())
sg.start()
print(sg.get_current_definition())
# import time
# time.sleep(15)
# sg.terminate()



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

import boto3
import moto

from pcf.core import State
from pcf.quasiparticle.aws.ec2_route53.ec2_route53 import EC2Route53


class TestEC2Route53Record():
    quasiparticle_definition = {
        "pcf_name": "ec2_route53",
        "flavor": "ec2_route53",
        "particles":[
            {"flavor":"route53_record",
             "aws_resource": {
                "Name": "prod.redis.db",
                "HostedZoneId": "ABCDEFGHI",
                "TTL": 10,
                "ResourceRecords": [{"Value":"127.0.0.1"}],
                "Type": "A"}
            },
            {
                "flavor": "ec2_instance",
                "multiplier":2,
                "aws_resource": {
                    "custom_config":{
                        "instance_name":"gg-instance",
                    },
                    "ImageId": "ami-1234567",
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
        ],

    }

    @moto.mock_ec2
    @moto.mock_route53
    def test_apply_states(self):
        route53_record_client = boto3.client('route53', region_name='us-east-1')
        resp = route53_record_client.create_hosted_zone(
            Name="db.",
            CallerReference=str(hash('foo')),
            HostedZoneConfig=dict(
                PrivateZone=True,
                Comment="db",
            )
        )

        ec2_client = boto3.client('ec2', 'us-east-1')
        vpc = ec2_client.create_vpc(CidrBlock='10.0.0.0/16')['Vpc']
        subnet1 = ec2_client.create_subnet(VpcId=vpc['VpcId'], CidrBlock='10.1.0.0/24')['Subnet']['SubnetId']

        self.quasiparticle_definition["particles"][0]["aws_resource"]["HostedZoneId"] = resp["HostedZone"]["Id"]
        self.quasiparticle_definition["particles"][1]["aws_resource"]["SubnetId"] = subnet1

        quasiparticle = EC2Route53(self.quasiparticle_definition)


        # Test start

        quasiparticle.set_desired_state(State.running)
        quasiparticle.apply(sync=True)

        assert quasiparticle.get_state() == State.running
        assert len(quasiparticle.pcf_field.get_particles(flavor='ec2_instance')) == 2
        assert len(quasiparticle.pcf_field.get_particles(flavor='route53_record')) == 1

        # Test Update

        self.quasiparticle_definition["particles"][0]["aws_resource"]["Type"] = "CNAME"
        self.quasiparticle_definition["particles"][1]["multiplier"] = 3

        quasiparticle = EC2Route53(self.quasiparticle_definition)
        quasiparticle.set_desired_state(State.running)
        quasiparticle.apply(sync=True)

        assert quasiparticle.get_state() == State.running
        assert quasiparticle.get_particle(flavor='route53_record', pcf_name="ec2_route53").current_state_definition["Type"] == "CNAME"
        assert len(quasiparticle.pcf_field.get_particles(flavor='ec2_instance')) == 3

        # Test Terminate

        quasiparticle.set_desired_state(State.terminated)
        quasiparticle.apply(sync=True)

        assert quasiparticle.get_state() == State.terminated


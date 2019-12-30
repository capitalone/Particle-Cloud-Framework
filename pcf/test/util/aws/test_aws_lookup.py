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
import os

from pcf.particle.aws.ec2.ec2_instance import EC2Instance
from pcf.core.aws_resource import AWSResource
from pcf.core import State

os.environ['AWS_DEFAULT_REGION'] = "us-east-1"


class TestLookup:
    particle_definition = {
        "pcf_name": "gg-pcf",
        "flavor": "ec2_instance",
        "aws_resource": {
            "custom_config":{
                "instance_name": "$lookup$instance_name$REPLACED_LATER",
            },
            "BlockDeviceMappings": [
                {
                    "Ebs": {
                        "SnapshotId": "$lookup$snapshot$ami-build"
                    }
                }
            ],
            "ImageId": "$lookup$ami$Ubuntu",
            "InstanceType": "m4.large",
            "KeyName": "secret-key",
            "MaxCount": 1,
            "MinCount": 1,
            "SubnetId": "$lookup$subnet$Public",
            "IamInstanceProfile": {
                "Arn": "$lookup$iam$instance-profile:InstanceProfile-Default"
            },
            "InstanceInitiatedShutdownBehavior": "stop",
            "tags": {
                "Test": "Tag"
            }
        }
    }


    @moto.mock_ec2
    @moto.mock_iam
    def test_replace_ids(self):
        ec2_resource = boto3.resource('ec2', 'us-east-1')
        ec2_client = boto3.client('ec2', 'us-east-1')
        vpc = ec2_client.create_vpc(CidrBlock='10.0.0.0/16')['Vpc']

        # mock up subnet
        subnetId = ec2_client.create_subnet(VpcId=vpc['VpcId'], CidrBlock='10.1.0.0/24')['Subnet']['SubnetId']
        subnet = ec2_resource.Subnet(subnetId)
        subnet.create_tags(
            Tags=[
                {
                    'Key': 'Name',
                    'Value': 'Public'
                }
            ]
        )

        # mock up EBS volume
        volumeId = ec2_client.create_volume(
            AvailabilityZone='us-east-1',
            Size=40
        )['VolumeId']

        # mock up snapshot
        ec2_client.create_snapshot(
            VolumeId=volumeId,
            TagSpecifications=[
                {
                    'ResourceType': 'snapshot',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': 'ami-build'
                        }
                    ]
                }
            ]
        )

        # mock up instance
        instanceId = ec2_resource.create_instances(
            MaxCount=1,
            MinCount=1
        )[0].id

        # add tag to instance
        ec2_client.create_tags(Resources=[instanceId], Tags=[{'Key':"PCFName", "Value":"testname"}])
        self.particle_definition["aws_resource"]["custom_config"]["instance_name"] = "$lookup$instance_name$" + instanceId

        # mock up ami
        ec2_client.create_image(
            Name='Ubuntu',
            InstanceId=instanceId
        )

        # mock instance profile
        iam_client = boto3.client("iam")
        iam_client.create_instance_profile(
            InstanceProfileName="InstanceProfile-Default"
        )

        particle = EC2Instance(self.particle_definition)

        # Test start
        particle.set_desired_state(State.running)
        particle.apply()

        assert particle.desired_state_definition["BlockDeviceMappings"][0]["Ebs"]["SnapshotId"][:4] == "snap"
        assert particle.desired_state_definition["custom_config"]["instance_name"] == "testname"
        assert particle.desired_state_definition["ImageId"][:3] == "ami"
        assert particle.desired_state_definition["SubnetId"][:6] == "subnet"
        #assert particle.desired_state_definition["IamInstanceProfile"]["Arn"] == "arn:aws:iam::123456789012:instance-profile/InstanceProfile-Default"

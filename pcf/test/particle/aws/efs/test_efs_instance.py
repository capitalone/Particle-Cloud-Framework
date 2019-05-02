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

from pytest import *
from unittest.mock import Mock
import pcf.core.aws_resource
from pcf.particle.aws.efs.efs_instance import EFSInstance
from pcf.core import State

import boto3
import moto
import datetime

particle_definition = {
    "pcf_name": "pcf_efs",
    "flavor": "efs_instance",
    "aws_resource": {
        "custom_config": {
            "instance_name": "efs-instance",
        },
        "CreationToken": "pcfFileSystem",
        "PerformanceMode": "generalPurpose"
    }
}

@fixture
def context(monkeypatch):
    mock_client = Mock(
        name='mock_client',
        create_file_system=Mock(
            return_value={
                'OwnerId': '123456789012',
                'CreationToken': 'pcfFileSystem',
                'FileSystemId': 'fs-abcd1234',
                'CreationTime': datetime.datetime(2018, 7, 9, 14, 26, 15),
                'LifeCycleState': 'creating',
                'NumberOfMountTargets': 0,
                'SizeInBytes': {'Value': 6144},
                'PerformanceMode': 'generalPurpose',
                'ResponseMetadata': {'HTTPStatusCode': 200},
            }
        ),
        delete_file_system=Mock(
            return_value={
                'ResponseMetadata': {'HTTPStatusCode': 200},
            }
        ),
        describe_file_systems=Mock(
            side_effect=[
                {
                    'FileSystems': [
                        {
                            'OwnerId': '123456789012',
                            'CreationToken': 'pcfFileSystem',
                            'FileSystemId': 'fs-abcd1234',
                            'CreationTime': datetime.datetime(2018, 7, 9, 14, 26, 15),
                            'LifeCycleState': 'available',
                            'Name': 'efs-instance',
                            'NumberOfMountTargets': 0,
                            'SizeInBytes': {'Value': 6144},
                            'PerformanceMode': 'generalPurpose',
                            'Encrypted': False
                        }
                    ]
                },
                {
                    'FileSystems': [
                        {
                            'OwnerId': '123456789012',
                            'CreationToken': 'pcfFileSystem',
                            'FileSystemId': 'fs-abcd1234',
                            'CreationTime': datetime.datetime(2018, 7, 9, 14, 26, 15),
                            'LifeCycleState': 'deleting',
                            'Name': 'efs-instance',
                            'NumberOfMountTargets': 0,
                            'SizeInBytes': {'Value': 6144},
                            'PerformanceMode': 'generalPurpose',
                            'Encrypted': False
                        }
                    ]
                },
                {
                    'FileSystems': [
                        {
                            'OwnerId': '123456789012',
                            'CreationToken': 'pcfFileSystem',
                            'FileSystemId': 'fs-abcd1234',
                            'CreationTime': datetime.datetime(2018, 7, 9, 14, 26, 15),
                            'LifeCycleState': 'deleted',
                            'Name': 'efs-instance',
                            'NumberOfMountTargets': 0,
                            'SizeInBytes': {'Value': 6144},
                            'PerformanceMode': 'generalPurpose',
                            'Encrypted': False
                        }
                    ]
                }
            ]
        ),
        create_tags=Mock(
            return_value={
                'ResponseMetadata': {'HTTPStatusCode': 200},
            }
        ),
        describe_tags=Mock(
            return_value={
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': 'efs-instance'
                    },
                ]
            }
        ),
        delete_tags=Mock(
            return_value={
                'ResponseMetadata': {'HTTPStatusCode': 200},
            }
        ),
        describe_mount_targets=Mock(
            side_effect=[
                {
                    'MountTargets': [
                        {
                            'OwnerId': '123456789012',
                            'FileSystemId': 'fs-abcd1234',
                            'MountTargetId': 'fsmt-e9347ba1',
                            'SubnetId': "subnet-066a1087",
                            'LifeCycleState': 'creating',
                            'IpAddress': '10.206.123.17',
                            'NetworkInterfaceId': 'eni-22217877'
                        }
                    ]
                },
                {
                    'MountTargets': []
                }
            ]
        )
    )

    mock_boto3 = Mock(
        client=Mock(return_value=mock_client),
    )

    monkeypatch.setattr(pcf.core.aws_resource, 'boto3', mock_boto3)

@moto.mock_ec2
def test_apply_states(context):
    ec2_client = boto3.client('ec2', 'us-east-1')
    vpc = ec2_client.create_vpc(CidrBlock='10.0.0.0/16')['Vpc']
    subnet1 = ec2_client.create_subnet(VpcId=vpc['VpcId'], CidrBlock='10.1.0.0/24')['Subnet']['SubnetId']
    ec2_client.create_security_group(
        Description='test',
        GroupName='test_sg'
    )

    particle = EFSInstance(particle_definition)

    # test start
    particle.set_desired_state(State.running)
    particle.apply()

    assert particle.get_state() == State.running
    assert particle.is_state_definition_equivalent() is True

    assert len(particle.describe_tags()) == 1

    # test create mount target
    mount_target_id = particle.create_mount_target(subnet1)

    assert len(particle.describe_mount_targets()) == 1

    #test delete mount target
    particle.delete_mount_target(mount_target_id)

    assert len(particle.describe_mount_targets()) == 0

    # test terminate
    particle.set_desired_state(State.terminated)
    particle.apply()

    assert particle.get_state() == State.terminated

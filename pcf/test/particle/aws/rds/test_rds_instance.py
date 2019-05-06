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

from pcf.particle.aws.rds.rds_instance import RDS
from pcf.core import State, pcf_exceptions
from pcf.util import pcf_util


class TestRDSInstance():
    particle_definition = {
        "pcf_name": "rds_test",
        "flavor": "rds_instance",
        "aws_resource": {
            "DBInstanceIdentifier": "test-instance",
            "DBInstanceClass": "db.m3.medium",
            "Engine": "postgres",
            "MasterUsername": "test",
            "DBName": "testdb",
            "AllocatedStorage": 11,
            "BackupRetentionPeriod": 30,
            "AvailabilityZone": "us-east-1",
            "EngineVersion": "9.4.9",
            "StorageEncrypted": True,
            "KmsKeyId": "testarn",
            "Port": 5432,
            "DBSubnetGroupName": 'test-subnet',
            "MasterUserPassword":"abcd1234"
        }
    }

    incorrect_particle_definition = {
        "pcf_name": "rds_test",
        "flavor": "rds_instance",
    }


    @moto.mock_rds2
    def test_get_current_def(self):
        rds = RDS(self.particle_definition)
        des_def = rds.desired_state_definition

        assert self.particle_definition['aws_resource'] == des_def

    @moto.mock_rds2
    @moto.mock_ec2
    def test_get_status(self):
        vpc_conn = boto3.client('ec2', 'us-east-1')
        vpc = vpc_conn.create_vpc(CidrBlock='10.0.0.0/16')['Vpc']
        subnet1 = vpc_conn.create_subnet(
            VpcId=vpc['VpcId'], CidrBlock='10.1.0.0/24')['Subnet']
        subnet2 = vpc_conn.create_subnet(
            VpcId=vpc['VpcId'], CidrBlock='10.1.0.0/26')['Subnet']

        subnet_ids = [subnet1['SubnetId'], subnet2['SubnetId']]
        rds_conn = boto3.client('rds', region_name='us-east-1')
        rds_conn.create_db_subnet_group(DBSubnetGroupName='test-subnet',
                                             DBSubnetGroupDescription='my db subnet',
                                             SubnetIds=subnet_ids)

        test_def = self.particle_definition['aws_resource']
        rds_conn.create_db_instance(**test_def)

        particle = RDS(self.particle_definition)
        status = particle.get_status()

        assert status['DBInstanceIdentifier'] == 'test-instance'

    @moto.mock_rds2
    @moto.mock_ec2
    def test_apply_states(self):
        #Mock VPC and Subnet Group first to mock RDS successfully.
        vpc_conn = boto3.client('ec2', 'us-east-1')
        vpc = vpc_conn.create_vpc(CidrBlock='10.0.0.0/16')['Vpc']
        subnet1 = vpc_conn.create_subnet(
            VpcId=vpc['VpcId'], CidrBlock='10.1.0.0/24')['Subnet']
        subnet2 = vpc_conn.create_subnet(
            VpcId=vpc['VpcId'], CidrBlock='10.1.0.0/26')['Subnet']

        subnet_ids = [subnet1['SubnetId'], subnet2['SubnetId']]
        rds_conn = boto3.client('rds', region_name='us-east-1')
        rds_conn.create_db_subnet_group(DBSubnetGroupName='test-subnet',
                                        DBSubnetGroupDescription='my db subnet',
                                        SubnetIds=subnet_ids)

        particle = RDS(self.particle_definition)

        # Test start
        particle.set_desired_state(State.running)
        self.particle_definition["aws_resource"]["ApplyImmediately"] = True
        self.particle_definition["aws_resource"]["SkipFinalSnapshot"] = True
        particle.apply(sync=False)

        assert particle.get_state() == State.running

        # Test Update
        self.particle_definition["aws_resource"]["EngineVersion"] = "9.5.0"

        particle = RDS(self.particle_definition)
        particle.set_desired_state(State.running)
        particle.apply(sync=True)

        assert particle.get_state() == State.running
        assert particle.current_state_definition['EngineVersion'] == particle.desired_state_definition['EngineVersion']
        assert particle.is_state_definition_equivalent() is True

        # Test Terminate
        particle.set_desired_state(State.terminated)
        particle.apply()

        assert particle.get_state() == State.terminated

    @moto.mock_rds2
    def test_incorrect_definitions(self):

        # Test missing definitions
        try:
            RDS(self.incorrect_particle_definition)
        except pcf_exceptions.InvalidUniqueKeysException:
            assert True
        else:
            assert False

        # Test Missing DBInstanceIdentifier

        self.incorrect_particle_definition["aws_resource"] = {}
        try:
            RDS(self.incorrect_particle_definition)
        except pcf_exceptions.InvalidUniqueKeysException:
            assert True
        else:
            assert False

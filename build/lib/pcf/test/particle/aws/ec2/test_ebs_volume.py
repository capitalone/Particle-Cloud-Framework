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

from pcf.particle.aws.ec2.ebs_volume import EBSVolume
from pcf.particle.aws.ec2.ec2_instance import EC2Instance
from pcf.core.quasiparticle import Quasiparticle
from pcf.core import State


class TestEBSVolume():
    particle_definition = {
        "pcf_name": "gg-pcf",
        "flavor": "ebs_volume",
        "aws_resource": {
            'custom_config':{
            "volume_name":'pcf-ebs-example'
            },
            'AvailabilityZone': 'us-east-1a',  # Required
            'Encrypted': True,  # Required
            'Size': 10,  # Required
            'VolumeType': 'standard',  # 'standard'|'io1'|'gp2'|'sc1'|'st1'  # Required
            'TagSpecifications': [{
                'ResourceType':"volume",
                'Tags':[{'Key':'Name',"Value":"gg-pcf"}], # Required
            }]
        }
    }

    particle_definition_attachment = {
        "pcf_name": "gg-pcf",
        "flavor": "ebs_volume",
        "parents":["ec2_instance:gg-pcf"],
        "aws_resource": {
            'custom_config':{
                "attach": True,
                "volume_name":'pcf-ebs-example'
            },
            'AvailabilityZone': 'us-east-1a',  # Required
            'Encrypted': True,  # Required
            'Size': 10,  # Required
            'VolumeType': 'standard',  # 'standard'|'io1'|'gp2'|'sc1'|'st1'  # Required
            'TagSpecifications': [{
                'ResourceType':"volume",
                'Tags':[{'Key':'Name',"Value":"gg-pcf"}], # Required
            }]
        }
    }

    ec2_particle_definition = {
        "pcf_name": "gg-pcf",
        "flavor": "ec2_instance",
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



    @moto.mock_ec2
    def test_apply_states(self):
        particle = EBSVolume(self.particle_definition)

        # Test start

        particle.set_desired_state(State.running)
        particle.apply()

        # assert particle.get_current_state_definition() == particle.get_desired_state_definition()
        assert particle.get_state() == State.running
        assert len(particle.tags) == 2

        # Test Update (modify_volumes not implemented in moto)

        self.particle_definition["aws_resource"]["TagSpecifications"] = [{
            'ResourceType':"volume",
            'Tags':[{'Key':'Name',"Value":"gg-pcf"},{'Key':'Name2',"Value":"gg-pcf2"}], # Required
        }]

        particle = EBSVolume(self.particle_definition)
        particle.set_desired_state(State.running)
        particle.apply()

        assert particle.get_state() == State.running
        assert len(particle.tags) == 3

        # Test Terminate

        particle.set_desired_state(State.terminated)
        particle.apply()

        assert particle.get_state() == State.terminated


    @moto.mock_ec2
    def test_attach_detach(self):
        # setup ec2

        ec2_client = boto3.client('ec2', 'us-east-1')
        vpc = ec2_client.create_vpc(CidrBlock='10.0.0.0/16')['Vpc']
        subnet1 = ec2_client.create_subnet(VpcId=vpc['VpcId'], CidrBlock='10.1.0.0/24')['Subnet']['SubnetId']
        self.ec2_particle_definition["aws_resource"]["SubnetId"] = subnet1
        ec2_client.create_security_group(
            Description='test',
            GroupName='test_sg'
        )

        # start quasiparticle for ebs attachment
        ebs_ec2_quasiparticle = Quasiparticle({
            "pcf_name": "quasi",
            "flavor": "quasiparticle",
            "particles": [
                self.ec2_particle_definition,
                self.particle_definition_attachment
            ]
        })
        ebs_ec2_quasiparticle.set_desired_state(State.running)
        ebs_ec2_quasiparticle.apply()

        assert ebs_ec2_quasiparticle.get_state() == State.running
        assert len(ebs_ec2_quasiparticle.get_particle("ebs_volume","gg-pcf").current_state_definition.get("Attachments")) == 1

        # TODO moto calls detach but doesnt seem to update state after
        # ebs_ec2_quasiparticle.set_desired_state(State.terminated)
        # ebs_ec2_quasiparticle.apply(cascade=True)
        #
        # assert ebs_ec2_quasiparticle.get_state() == State.terminated

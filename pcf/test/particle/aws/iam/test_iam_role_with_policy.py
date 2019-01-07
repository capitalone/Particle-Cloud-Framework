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
import json

from pcf.particle.aws.iam.iam_role import IAMRole
from pcf.particle.aws.iam.iam_policy import IAMPolicy
from pcf.core.quasiparticle import Quasiparticle
from pcf.core import State


class TestIAMRoleWithParentPolicies:

    @moto.mock_iam
    def test_apply_states(self):
        iam = boto3.resource('iam', region_name='us-east-1')
        conn = boto3.client('iam', region_name='us-east-1')

        my_managed_policy = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Effect': 'Allow',
                    'Action': 'logs:CreateLogGroup',
                    'Resource': '*'
                },
                {
                    'Effect': 'Allow',
                    'Action': [
                        'dynamodb:GetItem',
                    ],
                    'Resource': '*'
                }
            ]
        }

        my_managed_policy2 = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Effect': 'Allow',
                    'Action': 'logs:CreateLogGroup',
                    'Resource': '*'
                },
            ]
        }


        assume_role_policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole", 
                    "Principal": {
                        "Service": "ec2.amazonaws.com"
                    }, 
                    "Effect": "Allow", 
                }
            ]
        }

        quasiparticle_definition = {
            "pcf_name": "iam_role_with_iam_policy_parents",
            "flavor": "quasiparticle",
            "particles":[
                {
                    "flavor": "iam_policy",
                    "pcf_name":"iam_policy_parent",
                    "aws_resource": {
                        "custom_config": {},
                        "PolicyName":"pcf-test", # Required
                        "PolicyDocument": json.dumps(my_managed_policy)
                    }
                },
                {
                    "flavor": "iam_policy",
                    "pcf_name":"iam_policy_parent2",
                    "aws_resource": {
                        "custom_config": {},
                        "PolicyName":"pcf-test2", # Required
                        "PolicyDocument": json.dumps(my_managed_policy2)
                    }
                },
                {
                    "flavor": "iam_role",
                    "parents":["iam_policy:iam_policy_parent", "iam_policy:iam_policy_parent2"],
                    "aws_resource": {
                        "custom_config": {},
                        "RoleName":"pcf-test", # Required
                        "AssumeRolePolicyDocument": assume_role_policy_document,
                    }
                }
            ]
        }

        test_role = conn.create_role(RoleName="pcf-test", AssumeRolePolicyDocument=json.dumps(assume_role_policy_document))
        test_policy = conn.create_policy(
            PolicyName='pcf-test',
            PolicyDocument=json.dumps(my_managed_policy),
            Description='Test Policy'
        )

        conn.attach_role_policy(RoleName='pcf-test', PolicyArn='arn:aws:iam::123456789012:policy/pcf-test')
        iam_quasiparticle = Quasiparticle(quasiparticle_definition)

        # test start

        iam_quasiparticle.set_desired_state(State.running)
        iam_quasiparticle.apply(sync=True)

        print(iam_quasiparticle.member_particles)
        assert iam_quasiparticle.get_state() == State.running

        #test update by removing one policy

        updated_quasiparticle_definition = {
            "pcf_name": "iam_role_with_iam_policy_parents",
            "flavor": "quasiparticle",
            "particles":[
                {
                    "flavor": "iam_policy",
                    "pcf_name":"iam_policy_parent",
                    "aws_resource": {
                        "PolicyName":"pcf-test", # Required
                        "PolicyDocument": json.dumps(my_managed_policy)
                    }
                },
                {
                    "flavor": "iam_role",
                    "parents":["iam_policy:iam_policy_parent"],
                    "aws_resource": {
                        "RoleName":"pcf-test", # Required
                        "AssumeRolePolicyDocument": assume_role_policy_document,
                    }
                }
            ]
        }

        iam_quasiparticle = Quasiparticle(updated_quasiparticle_definition)
        iam_quasiparticle.set_desired_state(State.running)
        iam_quasiparticle.apply(sync=True)

        assert iam_quasiparticle.get_state() == State.running

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

from pcf.particle.aws.iam.iam_policy import IAMPolicy
from pcf.core import State


class TestIAMPolicy:

    @moto.mock_iam
    def test_apply_states(self):
        iam = boto3.resource('iam', region_name='us-east-1')
        conn = boto3.client('iam', region_name='us-east-1')
        policy_name = "pcf-policy-test"
        user = iam.create_user(UserName='test-user')

        iam_policy_example_json = {
            "pcf_name": "pcf-policy-test",  # Required
            "flavor": "iam_policy",  # Required
            "aws_resource": {
                "PolicyName": "pcf-policy-test",  # Required
                "PolicyDocument": json.dumps(
                    {
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
                                    'dynamodb:DeleteItem',
                                    'dynamodb:GetItem',
                                    'dynamodb:PutItem',
                                ],
                                'Resource': '*'
                            }
                        ]
                    })
            }
        }

        policy = conn.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps(iam_policy_example_json),
            Description='Test Policy'
        )

        particle = IAMPolicy(iam_policy_example_json)

        ## Test start
        particle.set_desired_state(State.running)
        particle.apply()

        assert particle.get_state() == State.running

        update_managed_policy = {
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
                        'dynamodb:DeleteItem',
                        'dynamodb:GetItem',
                    ],
                    'Resource': '*'
                }
            ]
        }

        iam_policy_example_json['aws_resource']['PolicyDocument'] = json.dumps(update_managed_policy)
        particle = IAMPolicy(iam_policy_example_json)
        particle.set_desired_state(State.running)
        particle.apply()
        
        assert particle.get_current_state_definition().get('PolicyDocument') == json.dumps(update_managed_policy)


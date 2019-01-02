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
from pcf.core import State


class IAMRole:

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

    iam_role_example_json = {
        "pcf_name": "pcf_iam_role", # Required
        "flavor":"iam_role", # Required
        "aws_resource":{
            "custom_config": {
                "policy_arns": []

            },
            "RoleName":"pcf-test", # Required
            "AssumeRolePolicyDocument": json.dumps(assume_role_policy_document),
        },
    }


    @moto.mock_iam
    def test_apply_states(self):
        particle = IAMRole(self.iam_role_example_json)

        # Test start

        particle.set_desired_state(State.running)
        particle.apply(sync=True)

        assert particle.get_state() == State.running

        # Test Terminate

        particle.set_desired_state(State.terminated)
        particle.apply(sync=True)

        assert particle.get_state() == State.terminated


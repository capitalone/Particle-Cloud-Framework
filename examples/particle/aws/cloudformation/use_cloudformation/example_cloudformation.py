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
import random
import string
from pcf.particle.aws.cloudformation.cloudformation_stack import CloudFormationStack
from pcf.core import State

# Only included required fields. For all fields,
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudfront.html#CloudFront.Client.create_distribution
particle_definition = {
    "pcf_name": "pcf_cloudformation",
    "flavor": "cloudformation",
    "aws_resource": {
        "StackName": "pcf-cloudformation", # used as the uid bc getting a distribution and its tags are separate api calls
        "Tags": [
            {
                "Key": "Name",
                "Value": "test"
            }
        ],
        "TemplateBody": ".",

    }
}


particle = CloudFormationStack(particle_definition)

particle.set_desired_state(State.running)
particle.apply(sync=True)

particle.set_desired_state(State.terminated)
particle.apply(sync=True)

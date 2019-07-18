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
import sys
import os
import json
import yaml

from pcf.particle.aws.cloudformation.cloudformation_stack import CloudFormationStack
from pcf.core import State


template_file_location = os.path.join(sys.path[0],"example_cloudformation.yml")
with open(template_file_location, "r") as content_file:
    content = yaml.load(content_file)

version = content.get('AWSTemplateFormatVersion')
content['AWSTemplateFormatVersion'] =  str(version)

## You can also pass in your cloudformation template configuratoin as a json 

# example_cloudformation_template = {  
#    "AWSTemplateFormatVersion":"2010-09-09",
#    "Description":"Example Project",
#    "Resources":{  
#       "TestKinesis":{  
#          "Type":"AWS::Kinesis::Stream",
#          "Properties":{  
#             "Name":"KinesisStreamCloudwatch",
#             "ShardCount":1,
#             "StreamEncryption":{  
#                "EncryptionType":"KMS",
#                "KeyId":"alias/aws/kinesis"
#             },
#             "Tags":[  
#                {  
#                   "Key":"Test1",
#                   "Value":"Test2"
#                }
#             ]
#          }
#       }
#    }
# }

# content = json.dumps(content)

# Only included required fields
particle_definition = {
    "pcf_name": "pcf_cloudformation",
    "flavor": "cloudformation",
    "aws_resource": {
        "StackName": "pcf-cloudformation",
        "Tags": [
            {
                "Key": "Name",
                "Value": "test"
            }
        ],
        "TemplateBody": json.dumps(content),

    }
}


particle = CloudFormationStack(particle_definition)

particle.set_desired_state(State.running)
particle.apply(sync=True)
print(particle.get_state())

## Example Update by adding additional tags to the resource. Updating cloudformation template also triggers an update.
particle_definition['aws_resource']['Tags'].append({"Key": "Name2", "Value": "test2"})
particle.set_desired_state(State.running)
particle.apply(sync=True)

particle.set_desired_state(State.terminated)
particle.apply(sync=True)
print(particle.get_state())


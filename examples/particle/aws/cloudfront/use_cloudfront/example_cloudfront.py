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

from pcf.core import State
import random
import string

# Only included required fields. For all fields,
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudfront.html#CloudFront.Client.create_distribution
particle_definition = {
        "Tags": [
            {
                "Key": "Name",
                "Value": "cloud-front1"
            }
        ],
        "Comment": "pcf-cloud-front", # used as the uid bc getting a distribution and its tags are separate api calls
        "CallerReference": "sdfa6df5a4sdf5asd7f9asd6fa5sd6f7a8sd9fa8sdf",
        "Origins": {
            "Quantity": 1,
            "Items": [
                {
                    "Id": "wahoo",
                    "DomainName": "hoo.com",
                },
            ]
        },
        "DefaultCacheBehavior": {
            "TargetOriginId": "string",
            "ForwardedValues": {
                "QueryString": False,
                "Cookies": {
                    "Forward": "none",
                },
            },
            "TrustedSigners": {
                "Enabled": True,
                "Quantity": 12,
            },
            "ViewerProtocolPolicy": "allow-all",
            "MinTTL": 50,
        },
        "Enabled": True,
    }


particle = CloudFront(particle_definition)

particle.set_desired_state(State.running)
particle.apply(sync=True)

particle.set_desired_state(State.terminated)
particle.apply(sync=True)

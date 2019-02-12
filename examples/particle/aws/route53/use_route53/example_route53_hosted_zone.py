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

from pcf.particle.aws.route53.route53_hosted_zone import HostedZone
from pcf.core import State
import random
import string

particle_definition = {
    "pcf_name": "pcf_hosted_zone",
    "flavor": "route53_hosted_zone",
    "aws_resource": {
        "Name": "www.hoooooos.com.",
        "custom_config": {
            "Tags": [
                {
                    "Key": "Owner",
                    "Value": "Hoo"
                }
            ]
        },
        "VPC": {
            "VPCRegion": "us-east-1",
            "VPCId": "vpc-12345"
        },
        "CallerReference": ''.join(random.choices(string.ascii_uppercase + string.digits, k=20)),
        "HostedZoneConfig": {
            "Comment": "hoo",
            "PrivateZone": True
        },
        # "DelegationSetId": ""
    }
}

hosted_zone = HostedZone(particle_definition)

# example start

hosted_zone.set_desired_state(State.running)
hosted_zone.apply()

print(hosted_zone.get_state())
print(hosted_zone.get_current_state_definition())

# example Terminate

hosted_zone.set_desired_state(State.terminated)
hosted_zone.apply()

print(hosted_zone.get_state())

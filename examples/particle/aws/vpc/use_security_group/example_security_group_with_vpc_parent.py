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

from pcf.particle.aws.vpc.security_group import SecurityGroup
from pcf.particle.aws.vpc.vpc_instance import VPC
from pcf.core.quasiparticle import Quasiparticle
from pcf.core import State

vpc_parent_quasiparticle = {
    "pcf_name": "sg_with_parent_vpc",
    "flavor": "quasiparticle",
    "particles": [
        {
            "flavor": "vpc",
            "pcf_name": "vpc_parent",
            "aws_resource": {
                "custom_config": {
                    "vpc_name": "test"
                },
                "CidrBlock": "10.0.0.0/16"
            }
        },
        {
            "flavor": "security_group",
            "parents": ["vpc:vpc_parent"],
            "aws_resource": {
                "Description": "pcf security group",
                "GroupName": "Hoos",
                "DryRun": False,
                "custom_config": {
                    "Tags": [
                        {
                            "Key": "Owner",
                            "Value": "Hoos"
                        }
                    ],
                    "IpPermissionsEgress": [],
                    "IpPermissions": []
                }
            }
        }
    ]
}

quasiparticle = Quasiparticle(vpc_parent_quasiparticle)

# example start

quasiparticle.set_desired_state(State.running)
quasiparticle.apply(sync=True)

print(quasiparticle.get_state())
print(quasiparticle.get_particle("security_group", "sg_with_parent_vpc").get_current_state_definition())

# example Terminate

quasiparticle.set_desired_state(State.terminated)
quasiparticle.apply(sync=True)

print(quasiparticle.get_state())

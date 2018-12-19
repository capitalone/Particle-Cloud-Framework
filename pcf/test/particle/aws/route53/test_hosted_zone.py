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
from pcf.particle.aws.route53.hosted_zone import HostedZone
from pcf.core import State


class TestRoute53HostedZone:
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
                    },
                    {
                        "Key": "UID",
                        "Value": "abc123"
                    }
                ]
            },
            "VPC": {
                "VPCRegion": "us-east-1",
                "VPCId": "vpc-12345"
            },
            "CallerReference": "werhasdkfboi12hasdfak",
            "HostedZoneConfig": {
                "Comment": "hoo",
                "PrivateZone": True
            },
            # "DelegationSetId": ""
        }
    }

    @moto.mock_route53
    def test_apply(self):
        particle = HostedZone(self.particle_definition)

        assert particle.get_status() is None
        # Test start

        particle.set_desired_state(State.running)
        particle.apply(sync=True)

        assert particle.get_state() == State.running

        assert particle.get_status().get("Name") == "www.hoooooos.com."

        # Test Update

        self.particle_definition["aws_resource"]["custom_config"]["Tags"][0]["Value"] = "Wahoo"

        particle = HostedZone(self.particle_definition)

        particle.set_desired_state(State.running)
        particle.apply(sync=True)

        assert particle.is_state_definition_equivalent()

        # Test Terminate

        particle.set_desired_state(State.terminated)
        particle.apply(sync=True)

        assert particle.get_state() == State.terminated

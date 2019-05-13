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

from pcf.particle.aws.route53.route53_record import Route53Record
from pcf.core import State
from pcf.util import pcf_util


class TestRoute53Record():
    particle_definition = {
              "pcf_name": "pcf_cluster",
              "flavor": "route53_record",
              "aws_resource": {
                  "Name": "many.lol.catz.com",
                  "HostedZoneId": "ABCDEFGHI",
                  "TTL": 10,
                  "ResourceRecords": [{"Value":"127.0.0.1"}],
                  "Type": "A"
              }
        }

    incorrect_particle_definition = {
        "pcf_name": "pcf_cluster",
        "flavor": "route53_record",
        "aws_resource": {
            "Name": "many.lol.catz.com",
            "ResourceRecords": [{"Value":"127.0.0.1"}],
            "Type": "A"
        }
    }


    @moto.mock_route53
    def test_get_status(self):
        conn = boto3.client('route53', region_name='us-east-1')
        resp = conn.create_hosted_zone(
            Name="db.",
            CallerReference=str(hash('foo')),
            HostedZoneConfig=dict(
                PrivateZone=True,
                Comment="db",
            )
        )
        self.particle_definition["aws_resource"]["HostedZoneId"] = resp["HostedZone"]["Id"]

        particle = Route53Record(self.particle_definition)
        status = particle.get_status()

        assert status == []

    @moto.mock_route53
    def test_apply_states(self):
        conn = boto3.client('route53', region_name='us-east-1')
        resp = conn.create_hosted_zone(
            Name="lol.catz.com",
            CallerReference=str(hash('foo')),
            HostedZoneConfig=dict(
                PrivateZone=True,
                Comment="db",
            )
        )
        self.particle_definition["aws_resource"]["HostedZoneId"] = resp["HostedZone"]["Id"]
        particle = Route53Record(self.particle_definition)

        # Test start

        particle.set_desired_state(State.running)
        particle.apply(sync=True)

        assert particle.get_state() == State.running
        assert particle.get_current_state_definition() == pcf_util.keep_and_remove_keys(particle.get_desired_state_definition(), Route53Record.REMOVE_PARAM_CONVERSIONS)

        # Test Update
        # Note: error will be thrown if you try to convert record set types
        self.particle_definition["aws_resource"]["ResourceRecords"] = [{"Value":"192.168.0.1"}]

        # Tests picking up existing record
        particle = Route53Record(self.particle_definition)
        particle.set_desired_state(State.running)
        particle.apply(sync=True)

        assert particle.get_current_state_definition() == pcf_util.keep_and_remove_keys(particle.get_desired_state_definition(), Route53Record.REMOVE_PARAM_CONVERSIONS)
        assert particle.get_state() == State.running

        # Test Terminate

        particle.set_desired_state(State.terminated)
        particle.apply(sync=True)

        assert particle.get_state() == State.terminated


    @moto.mock_route53
    def test_incorrect_definitions(self):

        # Test missing HostedZoneId

        try:
            Route53Record(self.incorrect_particle_definition)
        except KeyError as e:
            assert e.args[0] == "HostedZoneId"

        # Test incorrect HostedZoneId

        # particle = Route53Record(self.particle_definition)
        # particle.set_desired_state(State.running)
        # particle.apply(sync=False)

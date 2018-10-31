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

import boto3

from pcf.particle.aws.ec2.elb.elb import ElasticLoadBalancing
from pcf.core import State
from moto import mock_elb, mock_ec2

class TestELB():

    particle_definition = {
        "pcf_name": "elb-pcf",
        "flavor": "elb",
        "aws_resource": {
            "LoadBalancerName": "elb-pcf",
            "Scheme":"internal",
            "Listeners": [
                {'Protocol': 'tcp', 'LoadBalancerPort': 80, 'InstancePort': 8080}
            ],
        }
    }

    @mock_elb
    def test_get_current_def(self):
        asg = ElasticLoadBalancing(self.particle_definition)
        des_def = asg.desired_state_definition

        assert self.particle_definition['aws_resource'] == des_def

    @mock_elb
    def test_get_status(self):
        client = boto3.client('elb', region_name='us-east-1')
        client.create_load_balancer(
            LoadBalancerName='elb-pcf',
            Listeners=[
                {'Protocol': 'tcp', 'LoadBalancerPort': 80, 'InstancePort': 8080}],
            AvailabilityZones=['us-east-1a', 'us-east-1b']
        )

        particle = ElasticLoadBalancing(self.particle_definition)
        status = particle.get_status()

        assert status.get('LoadBalancerName') == 'elb-pcf'

    @mock_elb
    def test_apply_states(self):
        client = boto3.client('elb', region_name='us-east-1')

        particle = ElasticLoadBalancing(self.particle_definition)

        # Test start
        particle.set_desired_state(State.running)
        particle.apply(sync=False)

        assert particle.get_state() == State.running

        # Test Update
        #Skipping update for now otherwise need to write bunch of hack to make tests pass because moto sets
        #different value for the listeners that we don't need.

        # self.particle_definition["aws_resource"]["Scheme"] = 'external'
        #
        # particle = ElasticLoadBalancing(self.particle_definition)
        # particle.set_desired_state(State.running)
        # particle.apply(sync=True)
        #
        # assert particle.get_state() == State.running
        # assert particle.current_state_definition["Scheme"] == particle.desired_state_definition["Scheme"]
        # assert particle.is_state_definition_equivalent()
        #
        # Test Terminate
        particle.set_desired_state(State.terminated)
        particle.apply()

        assert particle.get_state() == State.terminated

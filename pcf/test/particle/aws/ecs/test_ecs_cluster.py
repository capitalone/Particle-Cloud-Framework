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
from unittest import TestCase

from pcf.particle.aws.ecs.ecs_cluster import ECSCluster
from pcf.core import State, pcf_exceptions


class TestECSCluster(TestCase):
    particle_definition = {
        "pcf_name": "pcf_ecs_cluster",
        "flavor": "ecs_cluster",
        "aws_resource": {
            "clusterName": "core"
        }
    }

    incorrect_particle_definition = {
        'pcf_name': 'gg',
        "flavor": "ecs_cluster",
    }

    @moto.mock_ecs
    def test_get_status(self):
        particle = ECSCluster(self.particle_definition)
        status = particle.get_status()

        assert status == {"status": "missing"}

    @moto.mock_ecs
    def test_apply_states(self):
        particle = ECSCluster(self.particle_definition)

        # Test start

        particle.set_desired_state(State.running)
        particle.apply()

        assert particle.get_state() == State.running

        # Test Update

        # ECS Cluster has no update function

        # Test Terminate

        particle.set_desired_state(State.terminated)
        particle.apply()

        assert particle.get_state() == State.terminated

    @moto.mock_ecs
    def test_incorrect_definitions(self):

        # Test missing definitions
        self.assertRaises(pcf_exceptions.InvalidUniqueKeysException, ECSCluster, self.incorrect_particle_definition)
        # Test Wrong Type in definition

        self.incorrect_particle_definition["aws_resource"]={}
        self.incorrect_particle_definition["aws_resource"]["clusterName"] = 100
        particle = ECSCluster(self.incorrect_particle_definition)
        particle.set_desired_state(State.running)
        try:
            particle.apply(sync=False)
        except Exception as e:
            is_right_exception = "Parameter validation" in e.args[0]
            assert is_right_exception

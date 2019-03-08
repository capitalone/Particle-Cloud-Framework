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

from pcf.particle.aws.ecs.ecs_task_definition import ECSTaskDefinition
from pcf.core import State


class TestECSTaskDefinition():
    particle_definition = {
        'pcf_name': 'gg',  # required
        'flavor': 'ecs_task_definition',  # required
        'aws_resource': {
            'family': 'gg-fam',
            'containerDefinitions':[
                {
                    "name": "wp",
                    "memory": 60000,
                    "essential": True,
                    "portMappings": [
                        {
                            "hostPort": 0,
                            "containerPort": 6006,
                            "protocol": "tcp"
                        }
                    ],
                    "mountPoints": [
                    ],
                    "environment": [
                        {"name": "environment-name", "value": "environment-value"}
                    ],
                    "privileged": True,
                    "image": "dockerhub.com/dockerimage",
                    "cpu": 3800
                }
            ]
        }
    }

    incorrect_particle_definition = {
        'pcf_name': 'gg',  # required
        'flavor': 'ecs_task_definition',  # required
        'aws_resource': {
            'containerDefinitions':[
                {
                    "name": "wp",
                }]
        }
    }


    @moto.mock_ecs
    def test_get_current_def(self):
        task_def = ECSTaskDefinition(self.particle_definition)
        des_def = task_def.desired_state_definition

        assert self.particle_definition['aws_resource'] == des_def

    @moto.mock_ecs
    def test_get_status(self):
        conn = boto3.client('ecs', region_name='us-east-1')
        conn.register_task_definition(family="gg-fam", containerDefinitions=self.particle_definition["aws_resource"]["containerDefinitions"])

        task_def = ECSTaskDefinition(self.particle_definition)

        status = task_def.get_status()
        assert status["family"] == "gg-fam"
        assert status["containerDefinitions"] == self.particle_definition["aws_resource"]["containerDefinitions"]

    @moto.mock_ecs
    def test_apply_states(self):
        particle = ECSTaskDefinition(self.particle_definition)

        # Test start

        particle.set_desired_state(State.running)
        particle.apply(sync=False)

        # moto doesn't return status when running the create_task_definition boto3 command
        assert particle.get_current_state_definition()["containerDefinitions"] == particle.get_desired_state_definition()["containerDefinitions"]

        # Test Update

        self.particle_definition["aws_resource"]["containerDefinitions"][0]["privileged"] = False
        particle = ECSTaskDefinition(self.particle_definition)
        particle.set_desired_state(State.running)
        particle.apply(sync=False)

        # moto doesn't return status when running the create_task_definition boto3 command
        assert particle.get_current_state_definition()["containerDefinitions"] == particle.get_desired_state_definition()["containerDefinitions"]

        # Test Terminate

        conn = boto3.client('ecs', region_name='us-east-1')
        conn.register_task_definition(
            family=self.particle_definition["aws_resource"]["family"],
            containerDefinitions= self.particle_definition["aws_resource"]["containerDefinitions"]
        )

        self.particle_definition["aws_resource"]["containerDefinitions"][0]["privileged"] = False
        particle = ECSTaskDefinition(self.particle_definition)
        particle.set_desired_state(State.terminated)
        particle.apply(sync=False)

        assert particle.get_state() == State.terminated


    @moto.mock_ecs
    def test_incorrect_definitions(self):

        # Test missing definitions

        particle = ECSTaskDefinition(self.incorrect_particle_definition)
        particle.set_desired_state(State.running)
        try:
            particle.apply(sync=False)
        except Exception as e:
            is_right_exception = "Parameter validation" in e.args[0]
            assert is_right_exception == True

        # Test Wrong Type in definition

        self.particle_definition["aws_resource"]["containerDefinitions"][0]["privileged"] = 100
        particle = ECSTaskDefinition(self.incorrect_particle_definition)
        particle.set_desired_state(State.running)
        try:
            particle.apply(sync=False)
        except Exception as e:
            is_right_exception = "Parameter validation" in e.args[0]
            assert is_right_exception == True

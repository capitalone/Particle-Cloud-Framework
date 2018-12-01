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

from pcf.particle.aws.emr.emr_cluster import EMRCluster
from pcf.core.quasiparticle import Quasiparticle
from pcf.core import State


class TestEMRCluster():
    particle_definition_instance_group = {
        "pcf_name": "pcf_cluster",
        "flavor": "emr_cluster",
        "aws_resource": {
            "ReleaseLabel":"emr-5.19.0",
            "Instances":{
                "KeepJobFlowAliveWhenNoSteps":True,
                "InstanceGroups":[{
                    "InstanceRole":"MASTER",
                    "Name":"master",
                    "InstanceCount":1,
                    "InstanceType":'m3.xlarge',
                    }]
                },
            "JobFlowRole":"EMR_EC2_DefaultRole",
            "Name":"test",
            "ServiceRole":"EMR_DefaultRole"
            }
        }

    particle_definition_instance_fleet = {
        "pcf_name": "pcf_cluster",
        "flavor": "emr_cluster",
        "aws_resource": {
            "ReleaseLabel":"emr-5.19.0",
            "Instances":{
                "KeepJobFlowAliveWhenNoSteps":True,
                "InstanceFleets":[{
                    "InstanceFleetType":"MASTER",
                    "Name":"master",
                    "TargetOnDemandCapacity":1,
                    "InstanceTypeConfigs": [{
                        "InstanceType":'m3.xlarge',
                    }]
                }]
            },
            "JobFlowRole":"EMR_EC2_DefaultRole",
            "Name":"test",
            "ServiceRole":"EMR_DefaultRole"
        }
    }

    @moto.mock_emr
    def test_apply_states_instance_group(self):
        particle = EMRCluster(self.particle_definition_instance_group)

        # Test start

        particle.set_desired_state(State.running)
        particle.apply(sync=True)

        assert particle.get_state() == State.running

        # Test Update

        self.particle_definition_instance_group["aws_resource"]["Instances"]["InstanceGroups"][0]["InstanceCount"] = 2

        particle = EMRCluster(self.particle_definition_instance_group)
        particle.set_desired_state(State.running)
        particle.apply(sync=True)

        assert particle.get_state() == State.running
        assert particle.current_state_definition['Instances']["master"]["RequestedInstanceCount"] == 2

        # Test Terminate

        particle.set_desired_state(State.terminated)
        particle.apply(sync=True)

        assert particle.get_state() == State.terminated

    @moto.mock_emr
    def test_apply_states_instance_fleet(self):
        particle = EMRCluster(self.particle_definition_instance_fleet)

        # Test start

        particle.set_desired_state(State.running)
        particle.apply(sync=True)

        assert particle.get_state() == State.running

        # Test Update
        # TODO moto instance fleets returns {} for instances
        #
        # self.particle_definition_instance_fleet["aws_resource"]["Instances"]["InstanceFleets"][0]["TargetOnDemandCapacity"] = 2
        #
        # particle = EMRCluster(self.particle_definition_instance_fleet)
        # particle.set_desired_state(State.running)
        # particle.apply(sync=True)
        #
        # assert particle.get_state() == State.running
        # assert particle.current_state_definition['Instances'] == 2

        # Test Terminate

        particle.set_desired_state(State.terminated)
        particle.apply(sync=True)

        assert particle.get_state() == State.terminated

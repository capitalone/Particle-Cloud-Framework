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
from pcf.particle.aws.batch.batch_job_definition import BatchJobDefinition

batch_def = {
    "pcf_name": "pcf-example",
    "flavor": "batch_job_definition",
    "aws_resource": {
        "jobDefinitionName": "test-definition",
        "type":"container",
        "containerProperties": {
            'command': [
                'sleep',
                '10',
            ],
            'image': 'busybox',
            'memory': 128,
            'vcpus': 1,
        }
    }
}

particle = BatchJobDefinition(batch_def)
particle.set_desired_state("running")
particle.apply()

print(particle.current_state_definition)
print(particle.state)

particle.set_desired_state("terminated")
particle.apply(sync=True)
print(particle.state)

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
from pcf.particle.aws.batch.batch_job_queue import BatchJobQueue
from pcf.particle.aws.batch.batch_job_definition import BatchJobDefinition
from pcf.particle.aws.batch.batch_compute_environment import BatchComputeEnvironment
from pcf.particle.aws.batch.batch_job import BatchJob

# batch_compute_def = {
#     "pcf_name": "pcf-compute-example",
#     "flavor": "batch_compute_environment",
#     "state": "ENABLED",
#     "aws_resource": {
#         "computeEnvironmentName": "test-comp-environment",
#         "type": "MANAGED",
#         "computeResources": {
#             'type': 'EC2',
#             'desiredvCpus': 1,
#             'instanceRole': 'arn:aws:iam::644160558196:instance-profile/ecsInstanceRole',
#             'instanceTypes': [
#                 'optimal',
#             ],
#             'maxvCpus': 4,
#             'minvCpus': 0,
#             'securityGroupIds': [
#                 'sg-6c7fa917',
#             ],
#             'subnets': [
#                 'subnet-3a334610',
#                 'subnet-efbcccb7',
#                 'subnet-e3b194de',
#                 'subnet-914763e7',
#             ]
#     },
#         "serviceRole": "arn:aws:iam::644160558196:role/service-role/AWSBatchServiceRole"
#     }
# }

# compute_particle = BatchComputeEnvironment(batch_compute_def)
# compute_particle.set_desired_state("running")
# compute_particle.apply()

# print(compute_particle.current_state_definition)
# print(compute_particle.state)

batch_queue_def = {
    "pcf_name": "pcf-queue-example",
    "flavor": "batch_job_queue",
    "aws_resource": {
        "jobQueueName": "test-queue",
        "state":"ENABLED",
        "priority":1,
        "computeEnvironmentOrder": [
            {
                'order': 1,
                'computeEnvironment': "test-comp-environment" 
            },
        ]
    }
}

queue_particle = BatchJobQueue(batch_queue_def)
queue_particle.set_desired_state("running")
queue_particle.apply()

print(queue_particle.current_state_definition)
print(queue_particle.state)

batch_definition_def = {
    "pcf_name": "pcf-definition-example",
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

definition_particle = BatchJobDefinition(batch_definition_def)
definition_particle.set_desired_state("running")
definition_particle.apply()

print(definition_particle.current_state_definition)
print(definition_particle.state)

batch_def = {
    "pcf_name": "pcf-example",
    "flavor": "batch_job",
    "parents":["batch_job_queue:pcf-queue-example", "batch_job_definition:pcf-definition-example"],
    "aws_resource": {
        "jobName": "test",
        "jobQueue":"test-queue",
        "jobDefinition":"test-definition"
    }
}

particle = BatchJob(batch_def)
particle.set_desired_state("running")
particle.apply()

print(particle.current_state_definition)
print(particle.state)

particle.set_desired_state("terminated")
particle.apply(sync=True)
print(particle.state)

definition_particle.set_desired_state("terminated")
definition_particle.apply(sync=True)
print(definition_particle.state)

queue_particle.set_desired_state("terminated")
queue_particle.apply(sync=True)
print(queue_particle.state)

# compute_particle.set_desired_state("terminated")
# compute_particle.apply(sync=True)
# print(compute_particle.state)

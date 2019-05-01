# Copyright 2019 Capital One Services, LLC
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
from pcf.core import State
import placebo
import boto3
import os

############# change to fit resource you are mocking #################
from pcf.particle.aws.cloudwatch.cloudwatch_log import CloudWatchLog
PATH = "cloudwatch/replay"
PARTICLE = CloudWatchLog
DEF = {
      "pcf_name": "pcf_cloudwatch_log",
      "flavor": "cloudwatch_logs",
      "aws_resource": {
        "logGroupName": "pcfLog",
        "tags": {
          "tagA": "string",
          "removed": "bye"
        }
      }
    }
UPDATED_DEF = {
      "pcf_name": "pcf_cloudwatch_log",
      "flavor": "cloudwatch_logs",
      "aws_resource": {
        "logGroupName": "pcfLog",
        "tags": {
          "tagA": "changed",
          "new": "hi"
        }
      }
    }
############################################################################

session = boto3.Session()
dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, PATH)
pill = placebo.attach(session, data_path=filename)
pill.record()

particle = PARTICLE(DEF, session)

# Test start

particle.set_desired_state(State.running)
particle.apply(sync=True)

print(particle.get_state() == State.running)
print(particle.is_state_definition_equivalent())

# Test update
if UPDATED_DEF:
    particle = PARTICLE(UPDATED_DEF, session)
    particle.set_desired_state(State.running)
    particle.apply(sync=True)

    print(particle.is_state_definition_equivalent())

# Test Terminate

particle.set_desired_state(State.terminated)
particle.apply(sync=True)

print(particle.get_state() == State.terminated)
pill.stop()

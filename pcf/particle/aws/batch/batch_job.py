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

import logging
from pcf.core import State
from pcf.core.aws_resource import AWSResource
from pcf.util import pcf_util

logger = logging.getLogger(__name__)


class BatchJob(AWSResource):

    # flavor = "batch_job"

    # state_lookup = {
    #     "CREATING": State.pending,
    #     "UPDATING": State.pending,
    #     "DELETING": State.pending,
    #     "DELETED": State.terminated,
    #     "VALID": State.running,
    #     "INVALID": State.terminated,
    # }

    # UPDATE_PARAM_FILTER = {
    #     "state",
    #     "priority",
    #     "computeEnvironmentOrder",
    # }

    # UNIQUE_KEYS = ['aws_resource.jobQueueName']

    def __init__(self):
        pass

    def sync_state(self):
        pass 

    def _terminate(self):
        pass

    def _start(self):
        pass

    def _stop(self):
        pass 

    def _update(self):
        pass 
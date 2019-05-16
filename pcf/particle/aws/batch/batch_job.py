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

    flavor = "batch_job"

    state_lookup = {
        "SUBMITTED": State.pending,
        "PENDING": State.pending, 
        "RUNNABLE": State.pending,
        "RUNNING": State.running, 
        "SUCCEEDED": State.terminated, 
        "FAILED": State.terminated,
    }

    UNIQUE_KEYS = ['aws_resource.jobName']

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition, "batch", session=session)
        self._set_unique_keys()
        self.name = self.desired_state_definition['jobName']

    def sync_state(self):
        status = self._get_status()
        if not status:
            self.state = State.terminated 
            self.current_state_definition = {}
            return 
        else:
            pass

    def _set_unique_keys(self):
        self.unique_keys = BatchJob.UNIQUE_KEYS

    def _get_status(self):
        res = self.client.describe_jobs(
            jobs=[self.name]
        )

        if len(res["jobs"]) != 1:
            return {}
        
        return res["Jobs"][0]

    def _terminate(self):
        pass

    def _start(self):
        pass

    def _stop(self):
        pass 

    def _update(self):
        pass 
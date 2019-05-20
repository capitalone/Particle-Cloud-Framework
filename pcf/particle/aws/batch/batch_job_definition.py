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


class BatchJobDefinition(AWSResource):
    
    flavor = "batch_job_definition"

    UNIQUE_KEYS = ['aws_resource.jobDefinitionName']

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition, "batch", session=session)
        self._set_unique_keys()
        self.name = self.desired_state_definition['jobDefinitionName']
    
    def sync_state(self):
        status = self._get_status()
        if not status:
            self.state = State.terminated 
            self.current_state_definition = {}
            return 
        else:
            job_status = status.get("status", "")
            self.state = self.state_lookup.get(job_status)
            self.current_state_definition = status

    def _set_unique_keys(self):
        self.unique_keys = BatchJobDefinition.UNIQUE_KEYS
    
    def _get_status(self):
        res = self.client.describe_job_definitions(
            jobDefinitions=[self.name],
        )

        if len(res["jobDefinitions"]) != 1:
            return {}
        
        return res["jobDefinitions"][0]

    def _terminate(self):
        resp = self.client.deregister_job_definition(jobDefinition=self.name)
        return resp

    def _start(self):
        resp = self.client.register_job_definition(**self.get_desired_state_definiton())
        self.current_state_definition = resp
        return resp 

    def _stop(self):
        return self._terminate()

    def _update(self):
        return self._start()
    
    def is_state_equivalent(self, state1, state2):
        pass

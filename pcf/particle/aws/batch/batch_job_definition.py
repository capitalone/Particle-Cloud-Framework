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

    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0
    }

    state_lookup = {
        "ACTIVE": State.running,
        "INACTIVE": State.terminated
    }

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition, "batch", session=session)
        self._set_unique_keys()
        self.name = self.desired_state_definition['jobDefinitionName']
        self.revision = None 
    
    def sync_state(self):
        """
        Sets the current state defintion and state.
        """
        full_status = self._get_status()
        if full_status:
            self.current_state_definition = full_status 
            self.state = self.state_lookup[full_status.get('status')]
            self.revision = full_status.get('revision')
        else:
            self.state = State.terminated 
            self.current_state_definition = {} 

    def _set_unique_keys(self):
        """
        User defined logic that sets keys from state definition to uniquely
        identify batch_jobs. Unsure if needed.
        """
        self.unique_keys = BatchJobDefinition.UNIQUE_KEYS
    
    def _get_status(self):
        """
        Returns current state of batch job definition.
        """
        res = self.client.describe_job_definitions(
            jobDefinitionName=self.name,
            status = 'ACTIVE'
        )

        # if no active jobs return empty dict
        if len(res["jobDefinitions"]) == 0:
            return {}
        
        # else return most recent revision 
        return res["jobDefinitions"][0]

    def _terminate(self):
        """
        This will deregister job definitions. 
        """
        resp = None
        if self.revision:
            job_definition = self.name + ':' + str(self.revision)
            resp = self.client.deregister_job_definition(jobDefinition=job_definition)
        return resp

    def _start(self):
        """
        This will register job definitions.
        """
        resp = self.client.register_job_definition(**self.desired_state_definition)
        return resp 

    def _stop(self):
        """
        This will deregister the job definition.
        """
        return self._terminate()

    def _update(self):
        """ 
        Will create a new revision.
        """
        return self._start()
    
    def is_state_equivalent(self, state1, state2):
        """
        Compares the desired state and current state definitions.
        Unsure on implementation.
        Returns: 
            bool
        """
        return BatchJobDefinition.equivalent_states.get(state1) == BatchJobDefinition.equivalent_states.get(state2)
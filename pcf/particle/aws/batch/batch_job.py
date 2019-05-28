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
        "RUNNING": State.pending, 
        "STARTING": State.pending,
        "SUCCEEDED": State.running, 
        "FAILED": State.terminated
    }

    equivalent_states = {
        State.running: 0,
        State.terminated: 2,
        State.pending: 1
    }

    UNIQUE_KEYS = ['aws_resource.jobName']

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition, "batch", session=session)
        self._set_unique_keys()
        self.name = self.desired_state_definition['jobName']
        self.jobId = None

    def sync_state(self):
        """
        Calls get status and sets the current state defintion and state.
        """
        status = self._get_status()
        if status:
            job_status = status.get('status')
            self.state = self.state_lookup.get(job_status)
            self.current_state_definition = status
            self.jobId = status.get('jobId')
            
            if self.desired_state_definition.get('state') == 'terminated' and job_status == 'SUCCEEDED':
                    self.state = State.terminated
        else:
            self.state = State.terminated 
            self.current_state_definition = {}

    def _set_unique_keys(self):
        """
        User defined logic that sets keys from state definition to uniquely
        identify batch_jobs.
        """
        self.unique_keys = BatchJob.UNIQUE_KEYS

    def _get_status(self):
        """
        Grabs current state of batch job.
        """
        if not self.jobId:
            return {}

        # print(self.jobId)
        res = self.client.describe_jobs(
            jobs=[self.jobId],
        )

        if len(res["jobs"]) != 1:
            return {}
        
        return res["jobs"][0]

    def _terminate(self):
        """
        This will cancel jobs that have not yet begin and terminate jobs 
        that are in the job queue.
        """
        return self.client.terminate(
            jobId=self.current_state_definition.get('jobId'),
            reason=self.desired_state_definition.get(
                'reason', 'Job terminated by PCF')
        )
        
    def _start(self):
        """
        Submit batch job based on desired state definition.
        
        Returns:
            jobName and jobId  
        """
        resp =  self.client.submit_job(**self.desired_state_definition)
        self.jobId = resp.get('jobId')
        return resp

    def _stop(self):
        """
        Batch job does have a cancel job, but that does not stop
        jobs which are already in the RUNNING or STARTING state. 
        """
        return self._terminate() 

    def _update(self):
        """ 
        Batch jobs cannot be updated after they are submitted. 
        """
        pass

    def is_state_equivalent(self, state1, state2):
        """
        Compares the desired state and current state definitions.
        Returns: 
            bool
        """
        return BatchJob.equivalent_states.get(state1) == BatchJob.equivalent_states.get(state2)

    def is_state_definition_equivalent(self):
        return True

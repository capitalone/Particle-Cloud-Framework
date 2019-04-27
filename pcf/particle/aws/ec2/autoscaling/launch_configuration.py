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


from pcf.core.aws_resource import AWSResource
from pcf.core import State

import logging

logger = logging.getLogger(__name__)

class LaunchConfiguration(AWSResource):
    """
    This is the implementation of Amazon's Launch Configuration.
    """
    flavor = "launch_configuration"

    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0
    }

    UNIQUE_KEYS = ["aws_resource.LaunchConfigurationName"]

    def __init__(self, particle_definition, session=None):
        super().__init__(particle_definition=particle_definition, resource_name="autoscaling", session=session)
        self.lc_name = self.desired_state_definition["LaunchConfigurationName"]

        self._set_unique_keys()

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the Auto Scaling Group Launch Configuration

        """
        self.unique_keys = LaunchConfiguration.UNIQUE_KEYS

    def _terminate(self):
        """
        deletes the launch configuration particle that matches the name

        Returns:
            response of boto3 delete_launch_configuration()
        """
        return self.client.delete_launch_configuration(LaunchConfigurationName=self.lc_name)

    def _start(self):
        """
        start the launch configuration particle that matches current state definition

        Returns:
            response of boto3 create_launch_configuration()
        """

        return self.client.create_launch_configuration(**self.get_desired_state_definition())

    def get_status(self):
        """
        Get the current status of your launch configuration particle. Calls boto3 describe_launch_configurations using lc_name

        Returns:
            dict with the launch configuration particle that matches the lc_name provided
        """
        lc_status = self.client.describe_launch_configurations(LaunchConfigurationNames=[self.lc_name])

        return lc_status.get('LaunchConfigurations',[])

    def sync_state(self):
        """
        Sync state calls get_status to determines and the state of the launch configuration particle.
        """
        lc_status = self.get_status()
        if len(lc_status) == 0:
            self.state = State.terminated
            self.current_state_definition = {}
        else:
            self.current_state_definition = lc_status[0]
            if lc_status[0].get('LaunchConfigurationName') == self.lc_name:
                self.state = State.running
            else:
                self.state = State.terminated

    def _stop(self):
        """
        Launch configuration does not have a stopped state so it calls terminate.
        """
        return self._terminate()

    def _update(self):
        """
        Not Implemented
        """
        pass


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

from pcf.core.docker_resource import DockerResource
from pcf.core import State
import docker
from pcf.util import pcf_util


class DockerImage(DockerResource):
    """
    Particle that maps to a docker image
    """

    flavor = 'docker_image'

    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0,
    }

    UNIQUE_KEYS = ["docker_resource.image"]

    def __init__(self, particle_definition):
        """
        Args:
            particle_definition (definition): desired configuration of the particle
        """
        super(DockerImage, self).__init__(particle_definition, method="images")
        self.image = self.desired_state_definition["image"]

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the distribution
        """
        self.unique_keys = DockerImage.UNIQUE_KEYS

    def _start(self):
        """

        """


    def _terminate(self):
        """

        """


    def _stop(self):
        """

        """


    def _update(self):
        """
        Not implemented
        """
        raise NotImplemented

    def get_status(self):
        """

        Returns:
            current definition of the distribution
        """
        try:
            return self.client.get_registry_data(self.image)
        except docker.errors.APIError:
            return {}


    def sync_state(self):
        """
        Sync state calls get_status to set the state and current_state_definition
        """
        full_status = self.get_status()
        self.current_state_definition = full_status

        if full_status:
            self.state = State.running
        else:
            self.state = State.terminated


    def is_state_equivalent(self, state1, state2):
        """
        Determines if states are equivalent
        Args:
            state1 (state): first state
            state2 (state): second state
        Returns:
            bool: whether the two states are equivalent
        """

    def is_state_definition_equivalent(self):
        """
        Since there is no update available, always return True
        Returns:
             bool: True
        """
        return True

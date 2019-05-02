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
from pcf.core import State, pcf_exceptions
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

    TERMINATE_PARAMS = {
        "force",
        "noprune"
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
        Pulls docker image from registry

        Returns:
            Image Object
        """
        return self.client.pull(self.image)

    def _terminate(self):
        """
        Calls docker image remove. Optional parameters noprune and force can be passed
        in via particle definition

        Returns:
            remove() response
        """
        filtered_definition = pcf_util.param_filter(self.desired_state_definition, DockerImage.TERMINATE_PARAMS)

        return self.client.remove(image=self.image, **filtered_definition)

    def _stop(self):
        """
         Calls _terminate()
        """

        return self._terminate()

    def _update(self):
        """
        Pulls docker image from registry

        Returns:
            Image Object
        """
        return self.client.pull(self.image)

    def get_status(self):
        """
        Gets the attrs of the image locally

        Returns:
            dict: Attrs dict from the image
        """
        try:
            return self.client.get(self.image).attrs
        except docker.errors.APIError:
            return {}

    def get_latest_hash(self):
        """
        Gets the latest hash from registry

        Returns:
            dict: Attrs dict from the image

        """
        try:
            return self.client.get_registry_data(self.image).attrs
        except docker.errors.APIError:
            raise pcf_exceptions.ImageMissing

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
        return DockerImage.equivalent_states.get(state1) == DockerImage.equivalent_states.get(state2)

    def is_state_definition_equivalent(self):
        """
        Checks if the current image matches the latest hash available in the registry

        Returns:
             bool
        """
        current_hash = self.current_state_definition.get("RepoDigests")
        latest_hash = self.get_latest_hash().get("Descriptor").get('digest')

        return any(latest_hash in local_digest for local_digest in current_hash)

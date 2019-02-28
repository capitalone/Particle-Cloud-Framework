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
from pcf.core.azure_resource import AzureResource
from pcf.core import State
from azure.storage.blob import PublicAccess


class BlobContainer(AzureResource):
    """
    This is the implementation of Azure's blob container service.
    https://azure-storage.readthedocs.io/ref/azure.storage.blob.html
    """
    flavor = "blob"

    equivalent_states = {
        State.running: 1,
        State.stopped: 0,
        State.terminated: 0
    }

    UNIQUE_KEYS = ["azure_resource.name"]

    def __init__(self, particle_definition, blob_service=None):
        super().__init__(particle_definition)
        self._name = self.desired_state_definition["name"]
        self._set_unique_keys()
        if not blob_service:
            blob_service = self.storage_client.create_block_blob_service()
        self._blob_service = blob_service

    def _set_unique_keys(self):
        """
        Logic that sets keys from state definition that are used to uniquely identify the storage bucket

        """
        self.unique_keys = BlobContainer.UNIQUE_KEYS

    def _start(self):
        """
        Creates the blob container

        Returns:
             response of create_container
        """
        if self.desired_state_definition.get("public"):
            return self._blob_service.create_container(self._name, public_access=PublicAccess.Container)
        return self._blob_service.create_container(self._name)

    def _terminate(self):
        """
        Deletes the blob container

        Returns:
             response of delete_container
        """
        return self._blob_service.delete_container(self._name)

    def _stop(self):
        """
        blob container does not have stopped states. Calls _terminate()
        """
        return self.terminate()

    def get_status(self):
        """
        Determines if the container exists

        Returns:
             exists (bool)
        """
        return self._blob_service.exists(self._name)

    def sync_state(self):
        """
        Calls get status and then sets the current state.
        """
        if self.get_status():
            self.state = State.running
        else:
            self.state = State.terminated

    def _update(self):
        """
        Not Implemented
        """
        pass

    def is_state_equivalent(self, state1, state2):
        """
        Determines if states are equivalent. Uses equivalent_states defined in the class.

        Args:
            state1 (State):
            state1 (State):

        Returns:
            bool
        """
        return BlobContainer.equivalent_states.get(state1) == BlobContainer.equivalent_states.get(state2)

    def is_state_definition_equivalent(self):
        """
        Since there is no update available, always return True

        Returns:
             bool: True
        """
        return True


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
from pcf.core.particle import Particle
from azure.common.client_factory import get_client_from_cli_profile
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.storage.common import CloudStorageAccount


class AzureResource(Particle):
    """
    The azure resource class inherits the particle class and handles the clients for azure resources
    """
    def __init__(self, particle_definition):
        super().__init__(particle_definition)
        self.desired_state_definition = self.particle_definition["azure_resource"]
        self.custom_config = self.desired_state_definition.get("custom_config", {})
        self.client = None

    @property
    def compute_client(self):
        """
        Uses client from cli so that users can use az login to get their credentials

        Returns:
             Compute Client
        """
        if not self.client:
            self.client = get_client_from_cli_profile(ComputeManagementClient)
        return self.client

    @property
    def storage_client(self):
        """
        Uses client from cli so that users can use az login to get their credentials

        Returns:
             Storage Client
        """
        if not self.client:
            resource_group = self.desired_state_definition.get("resource_group")
            storage_account = self.desired_state_definition.get("storage_account")
            if resource_group and storage_account:
                client = get_client_from_cli_profile(StorageManagementClient)
                storage_keys = client.storage_accounts.list_keys(resource_group, storage_account)
                storage_keys = {v.key_name: v.value for v in storage_keys.keys}

                self.client = CloudStorageAccount(storage_account, storage_keys['key1'])
            else:
                raise Exception("azure_resource.resource_group and azure_resource.storage_account must be defined")
        return self.client

    @property
    def resource_client(self):
        """
        Uses client from cli so that users can use az login to get their credentials

        Returns:
             Resource Client
        """
        if not self.client:
            self.client = get_client_from_cli_profile(ResourceManagementClient)
        return self.client

    @property
    def network_client(self):
        """
        Uses client from cli so that users can use az login to get their credentials

        Returns:
             Network Client
        """
        if not self.client:
            self.client = get_client_from_cli_profile(NetworkManagementClient)
        return self.client


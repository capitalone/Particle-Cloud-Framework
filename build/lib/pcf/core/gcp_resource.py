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

from pcf.core.particle import Particle

class GCPResource(Particle):
    """The gcp resource class inherits the particle class and adds the gcp client.
    It takes as an input the resource library (ie datastore)
    """
    def __init__(self, particle_definition, resource):
        super(GCPResource, self).__init__(particle_definition)
        self.resource = resource
        self.desired_state_definition = self.particle_definition["gcp_resource"]
        self.custom_config = self.desired_state_definition.get("custom_config", {})

        self._client = None

    @property
    def client(self):
        """
        Returns:
             Client
        """
        if not self._client:
            self._client = self._get_client()
        return self._client


    def _get_client(self, **kwargs):
        """
        Returns a new resource client

        Args:
            kwargs: See google docs for valid arguments (https://googlecloudplatform.github.io/google-cloud-python/latest/datastore/client.html)

        Returns:
            Client
        """
        return self.resource.Client(**kwargs)

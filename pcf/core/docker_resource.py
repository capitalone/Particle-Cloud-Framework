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
import docker
from pcf.util import pcf_util


class DockerResource(Particle):
    """Base Docker Resource
    """

    LOGIN_PARAMS = {
        "username",
        "password",
        "email",
        "registry",
        "reauth",
        "dockercfg_path",
    }

    def __init__(self, particle_definition, method=None):
        super(DockerResource, self).__init__(particle_definition)
        self.desired_state_definition = self.particle_definition["docker_resource"]
        self.custom_config = self.desired_state_definition.get("custom_config", {})

        self._client = None
        self.method = method

    @property
    def client(self):
        if not self._client:
            docker_client = self.particle_definition["docker_resource"].get("client")
            self._client = self._get_client(docker_client, **self.desired_state_definition)
        if self.method:
            return getattr(self._client, self.method)
        return self._client

    def _get_client(self, docker_client, **kwargs):
        if docker_client:
            return docker.login(pcf_util.param_filter(kwargs, DockerResource.LOGIN_PARAMS))

        return docker.from_env()


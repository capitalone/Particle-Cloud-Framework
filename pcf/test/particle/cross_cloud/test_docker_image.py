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

from pcf.particle.cross_cloud.docker.docker_image import DockerImage
import os
import docker
import pytest


dir_path = os.path.dirname(os.path.realpath(__file__))

image_def = {
    "pcf_name": "pcf-example",
    "flavor": "docker_image",
    "docker_resource": {
        "image": "pcf-test-docker-image",
        "build_params": {
            "path": dir_path
        }
    }
}


class TestDockerImage:

    def test_get_current_def(self):
        particle = DockerImage(image_def)
        attrs = particle.get_status()
        assert attrs["Id"] == "sha256:28ea16771556b2c4c3426955d090c45801295b727e83eee4c853b72625c48888"
        assert "pcf-test-docker-image:latest" in particle.client.get(particle.image).tags

    def test_terminate(self):
        particle = DockerImage(image_def)
        particle.terminate()
        with pytest.raises(docker.errors.ImageNotFound):
            particle.client.get(particle.image)



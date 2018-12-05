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

from pcf.particle.aws.lambda_function.lambda_function import LambdaFunction
from pcf.core.pcf_exceptions import MissingPythonConfig
from zipfile import ZipFile
import os
import importlib
import logging

logger = logging.getLogger(__name__)


class LambdaPython(LambdaFunction):
    flavor = "lambda_python_function"

    def __init__(self, particle_definition):
        super(LambdaFunction,self).__init__(particle_definition=particle_definition,resource_name="lambda")
        self.directory = self.custom_config.get("generate_zip")
        self._generate_zip()
        super(LambdaPython, self).__init__(particle_definition=particle_definition)

    def _generate_zip(self):
        if not self.directory:
            return

        files = self.custom_config.get("python_files")
        if not files:
            raise MissingPythonConfig

        with open(self.directory + "/requirements.txt",'r') as f:
            requirements = [line.strip().split('=')[0] for line in f]

        with ZipFile(self.name + ".zip", "w") as zip:
            for file in files:
                zip.write(os.path.abspath(file))

            for requirement in requirements:
                try:
                    path = importlib.util.find_spec(requirement).submodule_search_locations[0]
                    if path:
                        for root, dirs, files in os.walk(path):
                            for file in files:
                                zip.write(os.path.join(root,file))
                except:
                    logger.debug("Could not find {0}. Skipping".format(requirement))

        self.desired_state_definition["Code"] = {"ZipFile": self.name + ".zip"}




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
from pcf.core.pcf_exceptions import MissingException
from zipfile import ZipFile
import os
import importlib
import logging

logger = logging.getLogger(__name__)


class LambdaPython(LambdaFunction):
    """
    This extends the LambdaFunction. It adds the functionality to autogenerate a zip file of your python packages and files.
    THe python packages are autodiscovered using importlib.

    """
    flavor = "lambda_python_function"

    def __init__(self, particle_definition):
        super(LambdaFunction,self).__init__(particle_definition=particle_definition,resource_name="lambda")
        self.directory = self.custom_config.get("zip_directory")
        self.lambda_requirements = self.custom_config.get("lambda_requirements","requirements.txt")
        self._generate_zip()
        super(LambdaPython, self).__init__(particle_definition=particle_definition)

    def _generate_zip(self):
        """
        Creates a zip of python packages in requirements.txt and a list of files specified in python_files. It then adds
        the zip to the desired definition
        """
        if not self.directory:
            return

        python_files = self.custom_config.get("python_files")
        if not python_files:
            raise MissingException("generate_zip was set to true, but no python files were found in custom_config python_files")

        if not self.directory:
            raise MissingException("generate_zip was set and zip_directory is missing")

        with open(self.directory + "/" + self.lambda_requirements,'r') as f:
            requirements = [line.strip().split('=')[0] for line in f]

        with ZipFile(self.name + ".zip", "w") as zip:
            # zip python files
            for p_file in python_files:
                zip.write(p_file)

            # zip requirements from requirements.txt
            for requirement in requirements:
                try:
                    path = importlib.util.find_spec(requirement).submodule_search_locations[0]
                    if path:
                        rootdir = requirement
                        for root, dirs, files in os.walk(path):
                            for file in files:
                                filepath = os.path.join(root, file)
                                parentpath = os.path.relpath(filepath,path)
                                arcname = os.path.join(rootdir, parentpath)
                                zip.write(filepath,arcname)
                except:
                    logger.debug("Could not find {0}. Skipping".format(requirement))

        self.desired_state_definition["Code"] = {"ZipFile": self.name + ".zip"}




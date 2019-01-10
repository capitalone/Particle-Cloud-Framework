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

import os
from glob import glob
from pathlib import Path
from setuptools import setup, find_packages
from pcf import VERSION


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='pcf',
    version=VERSION,
    description='pcf',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    author='anovis',
    packages=find_packages(),
    url='https://github.com/capitalone/Particle-Cloud-Framework',
    install_requires=[
        "boto==2.48.0",
        "boto3==1.9.76",
        "Jinja2==2.9.6",
        "google-cloud-storage==1.10.0",
        "google-api-python-client==1.7.4",
        "commentjson==0.7.1",
        "deepdiff==3.3.0"
    ],
    package_data={'pcf': glob('**/*.j2', recursive=True)},
    include_package_data=True,
)

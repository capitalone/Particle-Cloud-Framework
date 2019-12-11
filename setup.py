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
    version=os.environ.get('PCF_TAG', VERSION),
    description='pcf',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    author='anovis,bb1314,davidyum',
    packages=find_packages(),
    url='https://github.com/capitalone/Particle-Cloud-Framework',
    entry_points='''
        [console_scripts]
        pcf=pcf.cli.cli:cli
    ''',
    install_requires=[
        "azure-storage-common==1.4.0",
        "azure-storage-blob==1.5.0",
        "azure-common==1.1.20",
        "azure-mgmt-compute==4.6.2",
        "azure-mgmt-resource==2.1.0",
        "azure-mgmt-network==2.7.0",
        "azure-mgmt-storage==3.3.0",
        "azure-cli-core==2.0.57",
        "boto==2.48.0",
        "boto3==1.9.143",
        "Jinja2==2.10.1",
        "google-compute-engine==2.8.13",
        "google-cloud-storage==1.15.0",
        "google-api-python-client==1.7.4",
        "commentjson==0.7.1",
        "botocore==1.12.143",
        "deepdiff==4.0.6",
        "click==7.0",
        "python-Levenshtein==0.12.0",
        "pyyaml==5.1"
    ],
    package_data={'pcf': glob('**/*.j2', recursive=True)},
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)

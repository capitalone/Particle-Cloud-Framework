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
from pcf.particle.aws.glacier.glacier_vault import GlacierVault
from pcf.core import State
import placebo
import boto3
import os


class TestGlacierVault:
    particle_definition = {
        "pcf_name": "pcf_glacier",
        "flavor": "glacier_vault",
        "aws_resource": {
            "vaultName": "pcf_test_glacier",  # Required
            "custom_config": {
                "Tags": {
                    "Name": "pcf-glacier-test"
                }
            }
        }
    }

    def test_create_vault(self):
        session = boto3.Session()
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'replay')
        pill = placebo.attach(session, data_path=filename)
        pill.playback()
        # define particle
        particle = GlacierVault(self.particle_definition, session)

        # Test start

        particle.set_desired_state("running")
        particle.apply()

        assert particle.get_state() == State.running

        # # test tags
        tags = particle.client.list_tags_for_vault(vaultName=particle.vault_name, accountId=particle.account_id)

        assert self.particle_definition.get("aws_resource").get("custom_config").get("Tags") == tags.get("Tags")

    def test_terminate(self):
        session = boto3.Session()
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'replay')
        pill = placebo.attach(session, data_path=filename)
        pill.playback()
        # define particle
        particle = GlacierVault(self.particle_definition, session)


        # Test Terminate

        particle.set_desired_state("terminated")
        particle.apply()

        assert particle.get_state() == State.terminated
        pill.stop()

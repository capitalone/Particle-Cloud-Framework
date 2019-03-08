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

import moto
import os

from pcf.particle.aws.s3.s3_bucket import S3Bucket
from pcf.core import State


class TestS3Bucket():
    particle_definition = {
        "pcf_name": "pcf_s3_bucket",
        "flavor": "s3_bucket",
        "aws_resource": {
            "Bucket": "pcf_test_bucket",
            "custom_config": {
                "Tags": {
                    "Name":"pcf-s3-test"
                }
            }
        }
    }


    @moto.mock_s3
    def test_apply_states(self):
        particle = S3Bucket(self.particle_definition)

        # Test start

        particle.set_desired_state(State.running)
        particle.apply()

        assert particle.get_state() == State.running

        # Test put object

        text = b'Some sample text'

        particle.client.put_object(Bucket=particle.bucket_name,Key="test-object",Body=text)
        particle.resource.Bucket(particle.bucket_name).upload_file(Key="test-file", Filename=os.path.join(os.path.dirname(__file__),"test.txt"))

        assert len(particle.client.list_objects(Bucket=particle.bucket_name)["Contents"]) == 2

        # Test tags
        tags = particle.client.get_bucket_tagging(Bucket=particle.bucket_name)
        assert not tags.get("TagSet") == None

        # Test terminate

        particle.client.delete_object(Bucket=particle.bucket_name, Key="test-object")
        particle.client.delete_object(Bucket=particle.bucket_name, Key="test-file")

        assert not particle.client.list_objects(Bucket=particle.bucket_name).get("Contents", False)

        particle.set_desired_state(State.terminated)
        particle.apply()

        assert particle.get_state() == State.terminated

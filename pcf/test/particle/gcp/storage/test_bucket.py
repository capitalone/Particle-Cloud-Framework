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

#based off https://github.com/GoogleCloudPlatform/google-cloud-python/blob/master/storage/tests/unit/test_client.py

import os
import json
import mock
import requests
from six.moves import http_client


from pcf.particle.gcp.storage.bucket import Bucket
from pcf.core import State


def _make_credentials():
    import google.auth.credentials

    return mock.Mock(spec=google.auth.credentials.Credentials)


def _make_response(status=http_client.OK, content=b'', headers={}):
    response = requests.Response()
    response.status_code = status
    response._content = content
    response.headers = headers
    response.request = requests.Request()
    return response


def _make_json_response(data, status=http_client.OK, headers=None):
    headers = headers or {}
    headers['Content-Type'] = 'application/json'
    return _make_response(
        status=status,
        content=json.dumps(data).encode('utf-8'),
        headers=headers)


def _make_requests_session(responses):
    session = mock.create_autospec(requests.Session, instance=True)
    session.request.side_effect = responses
    return session

# TODO fix tests. Get current state doesnt work which messes up tests
class TestStorage():

    def _make_one(self,project,credentials):
        from google.cloud.storage.client import Client

        return Client(project=project, credentials=credentials)
'''    def test_apply_states(self):
        PROJECT = 'PROJECT'
        CREDENTIALS = _make_credentials()
        BUCKET_NAME = 'test-bucket'

        client = self._make_one(project=PROJECT, credentials=CREDENTIALS)
        http = _make_requests_session([_make_json_response({})])

        client._http_internal = http

        storage_particle = Storage({"pcf_name":"name","gcp_resource":{"name":"test-bucket"}})
        storage_particle._client = client

        # Test start
        storage_particle.set_desired_state(State.running)
        storage_particle.apply(sync=False)

        data = {'items': [{'name': BUCKET_NAME}]}
        http = _make_requests_session([_make_json_response(data)])
        client._http_internal = http
        storage_particle._client = client
        storage_particle.apply(sync=False)

        assert storage_particle.get_state() == State.running

        # TODO mock put and delete objects... Test put object

        # text = b'Some sample text'
        #
        # storage_particle.put_object(blob_name="test-object",file_obj=text)
        # storage_particle.put_file(blob_name="test-file", file=os.path.join(os.path.dirname(__file__),"test.txt"))
        #
        # assert len(storage_particle.list_objects()["Contents"]) == 2
        #
        # # Test Terminate
        #
        # storage_particle.delete_object(blob_name="test-object")
        # storage_particle.delete_object(blob_name="test-file")

        # assert not particle.storage_particle().get("Contents", False)
        storage_particle = Storage({"pcf_name":"name","gcp_resource":{"name":"fake-bucket"}})

        storage_particle.set_desired_state(State.terminated)
        http = _make_requests_session([_make_json_response({})])
        client._http_internal = http
        storage_particle._client = client
        try:
            storage_particle.apply(sync=False)
        except:

            assert storage_particle.get_state() == State.terminated
'''

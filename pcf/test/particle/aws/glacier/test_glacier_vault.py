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

import pcf.core.aws_resource
import pytest
import boto3

from botocore.exceptions import ClientError
from pcf.particle.aws.glacier.glacier_vault import GlacierVault
from pcf.core import State
from unittest.mock import Mock

particle_definition = {
    "pcf_name": "pcf_glacier",
    "flavor": "glacier",
    "aws_resource": {
        "vaultName": "pcf_test_glacier", # Required
        "custom_config": {
            "Tags": {
                    "Name":"pcf-glacier-test"
                 }
        }
    }
}

nothing = {}

default_describe_vault = {
    'VaultARN': "string",
    'creationTime': 123,
    'VaultName': "pcf_test_glacier",
    'CreationDate': 123,
    'LastInventoryDate': "string",
    'NumberOfArchives': 123,
    'SizeInBytes': "string"
}

default_list_tags = {
    "Tags": {
        "Name": "pcf-glacier-test"
    }
}

client_error = {
    'Error':
        {
            'Message': 'Vault not found for ARN: arn:aws:glacier:us-east-1:-:vaults/pcf_test_glacier',
            'Code': 'ResourceNotFoundException'
        },
    'ResponseMetadata': {
        'RequestId': '',
        'HTTPStatusCode': 404,
        'HTTPHeaders': {
            'x-amzn-requestid': '',
            'content-type': 'application/json',
            'content-length': '154',
            'date': 'string',
            'cache-control': 'proxy-revalidate',
            'proxy-connection': 'Keep-Alive',
            'connection': 'Keep-Alive'
        },
        'RetryAttempts': 0
    }
}

def test_create_vault(monkeypatch):
    """
    monkey patching until newer moto release
    """
    # tests initialization
    mock_client = Mock(
        name="mock_client",
        add_tags_to_vault=Mock(
            side_effect=[nothing]
        ),
        list_tags_for_vault=Mock(
            return_value=default_list_tags
        )
    )
    mock_boto3 = Mock(
        client=Mock(return_value=mock_client),
    )

    monkeypatch.setattr(pcf.core.aws_resource, "boto3", mock_boto3)

    particle = GlacierVault(particle_definition)

    particle.set_desired_state(State.running)
    particle.apply()

    assert particle.get_state() == State.running

    # test tags
    tags = particle.client.list_tags_for_vault(vaultName=particle.vault_name, accountId="-")

    assert particle_definition.get("aws_resource").get("custom_config").get("Tags") == tags.get("Tags")

def test_terminate(monkeypatch):
    """
    monkey patching until newer moto release
    """
    # tests termination
    mock_client = Mock(
        name="mock_client",
        describe_vault=Mock(
            side_effect=[
                ClientError(client_error, "test ClientError"),
                ClientError(client_error, "test ClientError"),
                ClientError(client_error, "test ClientError"),
                default_describe_vault
            ]
        )
    )

    mock_boto3 = Mock(
        client=Mock(return_value=mock_client),
    )

    monkeypatch.setattr(pcf.core.aws_resource, "boto3", mock_boto3)

    particle = GlacierVault(particle_definition)

    particle.set_desired_state(State.terminated)
    particle.apply()

    assert particle.get_state() == State.terminated

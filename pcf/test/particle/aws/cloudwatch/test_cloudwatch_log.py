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

from pcf.particle.aws.cloudwatch.cloudwatch_log import CloudWatchLog
from unittest.mock import Mock
import pcf.core.aws_resource
from pytest import *
import boto3
from pcf.core import State


particle_definition = {
    "pcf_name": "pcf_cloudwatch_log", #Required
    "flavor": "cloudwatch_logs", #Required
    "aws_resource": {
        # https://boto3.readthedocs.io/en/latest/reference/services/logs.html#id39
        "logGroupName": "Cloud Watch Log A", #Required
        "kmsKeyId": "keyA",
        "tags": {
            # key-value pairs for tags
            "tagA": "string",
            "removed": "bye",
        }
    }
}

particle_definition2 = {
    "pcf_name": "pcf_cloudwatch_log", #Required
    "flavor": "cloudwatch_logs", #Required
    "aws_resource": {
        # https://boto3.readthedocs.io/en/latest/reference/services/logs.html#id39
        "logGroupName": "Cloud Watch Log A", #Required
        "kmsKeyId": "keyB",
        "tags": {
            # key-value pairs for tags
            "tagA": "!string",
            "new": "hi",
        }
    }
}

nothing = {
    'logGroups': [],
    'nextToken': None
}

default = {
    'logGroups': [
        {
            'logGroupName': 'Cloud Watch Log A',
            'creationTime': 123,
            'retentionInDays': 123,
            'metricFilterCount': 123,
            'arn': 'string',
            'storedBytes': 123,
            'kmsKeyId': 'keyA'
        },
    ],
    'nextToken': 'string'
}

altered = {
    'logGroups': [
        {
            'logGroupName': 'Cloud Watch Log A',
            'creationTime': 123,
            'retentionInDays': 123,
            'metricFilterCount': 123,
            'arn': 'string',
            'storedBytes': 123,
            'kmsKeyId': 'keyB'
        },
    ],
    'nextToken': 'string'
}

no_exact_match = {
    'logGroups': [
        {
            'logGroupName': 'Cloud Watch Log A- not supposed to return this one',
            'creationTime': 123,
            'retentionInDays': 123,
            'metricFilterCount': 123,
            'arn': 'string',
            'storedBytes': 123,
            'kmsKeyId': 'keyA'
        },
    ],
    'nextToken': 'string'
}

default_tag = {
    "tags": {
        "tagA": "string",
        "removed": "bye",
    }
}

altered_tag = {
    "tags": {
        "tagA": "!string",
        "new": "hi",
    }
}


@moto.mock_logs
def test_start(monkeypatch):
    """
    monkey patching until newer moto release
    """
    # tests initialization
    mock_client = Mock(
        name='mock_client',
        describe_log_groups=Mock(
            side_effect=[nothing, default, default, default]
        ),
        list_tags_log_group=Mock(
            return_value=default_tag
        )

    )
    mock_boto3 = Mock(
        client=Mock(return_value=mock_client),
    )

    monkeypatch.setattr(pcf.core.aws_resource, 'boto3', mock_boto3)

    particle = CloudWatchLog(particle_definition)

    particle.set_desired_state(State.running)
    particle.apply()

    assert particle.get_state() == State.running
    assert particle.get_current_state_definition() == particle.get_desired_state_definition()
    assert "aws_resource.logGroupName" in particle.unique_keys


def test_update(monkeypatch):
    # Test update
    mock_client = Mock(
        name='mock_client',
        describe_log_groups=Mock(
            side_effect=[default, default, default, altered, altered, altered, altered]
        ),
        list_tags_log_group=Mock(
            side_effect=[default_tag, altered_tag, altered_tag]
        )

    )
    mock_boto3 = Mock(
        client=Mock(return_value=mock_client),
    )

    monkeypatch.setattr(pcf.core.aws_resource, 'boto3', mock_boto3)

    particle = CloudWatchLog(particle_definition2)
    particle.set_desired_state(State.running)

    particle.apply()
    assert particle.get_current_state_definition() == particle.get_desired_state_definition()
    assert particle.get_state() == State.running


def test_terminate(monkeypatch):
    mock_client = Mock(
        name='mock_client',
        describe_log_groups=Mock(
            side_effect=[default, default, nothing]
        ),
        list_tags_log_group=Mock(
            side_effect=[default_tag, {"tags": {}}]
        )

    )
    mock_boto3 = Mock(
        client=Mock(return_value=mock_client),
    )

    monkeypatch.setattr(pcf.core.aws_resource, 'boto3', mock_boto3)

    #Test terminate
    particle = CloudWatchLog(particle_definition)
    particle.set_desired_state(State.terminated)
    particle.apply()
    assert particle.get_state() == State.terminated





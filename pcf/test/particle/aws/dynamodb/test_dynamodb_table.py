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
from pcf.particle.aws.dynamodb.dynamodb_table import DynamoDB
from pcf.core import State
import placebo
import boto3
import os


# class TestDynamoDBTable:
#     particle_definition = {
#         "pcf_name": "pcf_dynamodb", #Required
#         "flavor": "dynamodb_table", #Required
#         "aws_resource": {
#             # Refer to https://boto3.readthedocs.io/en/latest/reference/services/dynamodb.html#DynamoDB.Client.create_table for a full list of parameters
#             "AttributeDefinitions": [
#                 {
#                     "AttributeName": "Post",
#                     "AttributeType": "S"
#                 },
#                 {
#                     "AttributeName": "PostDateTime",
#                     "AttributeType": "S"
#                 },
#             ],
#             "TableName": "pcf_test_table",
#             "KeySchema": [
#                 {
#                     "AttributeName": "Post",
#                     "KeyType": "HASH"
#                 },
#                 {
#                     "AttributeName": "PostDateTime",
#                     "KeyType": "RANGE"
#                 },
#             ],
#             "LocalSecondaryIndexes" : [
#                 {
#                     "IndexName": "LastPostIndex",
#                     "KeySchema": [
#                         {
#                             "AttributeName": "Post",
#                             "KeyType": "HASH"
#                         },
#                         {
#                             "AttributeName": "PostDateTime",
#                             "KeyType": "RANGE"
#                         }
#                     ],
#                     "Projection": {
#                         "ProjectionType": "KEYS_ONLY"
#                     }
#                 }
#             ],
#             "ProvisionedThroughput": {
#                 "ReadCapacityUnits": 10,
#                 "WriteCapacityUnits": 10
#             },
#             "Tags": [
#                 {
#                     "Key": "Name",
#                     "Value": "pcf-dynamodb-test"
#                 }
#             ]
#         }
#     }
#
#     def test_create_table(self):
#         session = boto3.Session()
#         dirname = os.path.dirname(__file__)
#         filename = os.path.join(dirname, 'replay')
#         pill = placebo.attach(session, data_path=filename)
#         pill.playback()
#         # define particle
#         particle = DynamoDB(self.particle_definition, session)
#
#         # Test start
#
#         particle.set_desired_state("running")
#         particle.apply()
#
#         assert particle.get_state() == State.running
#
#         # # test tags
#         # tags = particle.client.list_tags_for_vault(vaultName=particle.vault_name, accountId=particle.account_id)
#
#         # assert self.particle_definition.get("aws_resource").get("custom_config").get("Tags") == tags.get("Tags")
#
#     def test_terminate(self):
#         session = boto3.Session()
#         dirname = os.path.dirname(__file__)
#         filename = os.path.join(dirname, 'replay')
#         pill = placebo.attach(session, data_path=filename)
#         pill.playback()
#         # define particle
#         particle = DynamoDB(self.particle_definition, session)
#
#
#         # Test Terminate
#
#         particle.set_desired_state("terminated")
#         particle.apply()
#
#         assert particle.get_state() == State.terminated
#         pill.stop()

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
from pcf.core import State
import placebo
import boto3
import os

from pcf.particle.aws.dynamodb.dynamodb_table import DynamoDB

class TestDynamoDBTable:
    PATH = "replay"
    PARTICLE = DynamoDB
    DEF = {
        "pcf_name": "pcf_dynamodb", #Required
        "flavor": "dynamodb_table", #Required
        "aws_resource": {
            # Refer to https://boto3.readthedocs.io/en/latest/reference/services/dynamodb.html#DynamoDB.Client.create_table for a full list of parameters
            "AttributeDefinitions": [
                {
                    "AttributeName": "Post",
                    "AttributeType": "S"
                },
                {
                    "AttributeName": "PostDateTime",
                    "AttributeType": "S"
                },
            ],
            "TableName": "pcf_test_table",
            "KeySchema": [
                {
                    "AttributeName": "Post",
                    "KeyType": "HASH"
                },
                {
                    "AttributeName": "PostDateTime",
                    "KeyType": "RANGE"
                },
            ],
            "LocalSecondaryIndexes" : [
                {
                    "IndexName": "LastPostIndex",
                    "KeySchema": [
                        {
                            "AttributeName": "Post",
                            "KeyType": "HASH"
                        },
                        {
                            "AttributeName": "PostDateTime",
                            "KeyType": "RANGE"
                        }
                    ],
                    "Projection": {
                        "ProjectionType": "KEYS_ONLY"
                    }
                }
            ],
            "ProvisionedThroughput": {
                "ReadCapacityUnits": 10,
                "WriteCapacityUnits": 10
            },
            "Tags": [
                {
                    "Key": "Name",
                    "Value": "pcf-dynamodb-test"
                }
            ]
        }
    }
    UPDATED_DEF = {
        "pcf_name": "pcf_dynamodb", #Required
        "flavor": "dynamodb_table", #Required
        "aws_resource": {
            # Refer to https://boto3.readthedocs.io/en/latest/reference/services/dynamodb.html#DynamoDB.Client.create_table for a full list of parameters
            "AttributeDefinitions": [
                {
                    "AttributeName": "Post",
                    "AttributeType": "S"
                },
                {
                    "AttributeName": "PostDateTime",
                    "AttributeType": "S"
                },
            ],
            "TableName": "pcf_test_table",
            "KeySchema": [
                {
                    "AttributeName": "Post",
                    "KeyType": "HASH"
                },
                {
                    "AttributeName": "PostDateTime",
                    "KeyType": "RANGE"
                },
            ],
            "LocalSecondaryIndexes" : [
                {
                    "IndexName": "LastPostIndex",
                    "KeySchema": [
                        {
                            "AttributeName": "Post",
                            "KeyType": "HASH"
                        },
                        {
                            "AttributeName": "PostDateTime",
                            "KeyType": "RANGE"
                        }
                    ],
                    "Projection": {
                        "ProjectionType": "KEYS_ONLY"
                    }
                }
            ],
            "ProvisionedThroughput": {
                "ReadCapacityUnits": 25,
                "WriteCapacityUnits": 30
            },
            "Tags": [
                {
                    "Key": "Name",
                    "Value": "pcf-dynamodb-test"
                }
            ]
        }
    }
############################################################################

    def test_apply_states(self):
        session = boto3.Session()
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, self.PATH)
        pill = placebo.attach(session, data_path=filename)
        pill.playback()

        particle = self.PARTICLE(self.DEF, session)

        # Test start

        particle.set_desired_state(State.running)
        particle.apply(sync=True)

        print(particle.get_state() == State.running)
        print(particle.is_state_definition_equivalent())

        assert particle.get_state() == State.running

        # Test update
        if self.UPDATED_DEF:
            particle = self.PARTICLE(self.UPDATED_DEF, session)
            particle.set_desired_state(State.running)
            particle.apply(sync=True)
            print(particle.is_state_definition_equivalent())
            assert particle.is_state_definition_equivalent() == True
            assert particle.get_state() == State.running

        # Test Terminate

        particle.set_desired_state(State.terminated)
        particle.apply()

        print(particle.get_state() == State.terminated)
        assert particle.get_state() == State.terminated
        pill.stop()

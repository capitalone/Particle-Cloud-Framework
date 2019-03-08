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

from pcf.particle.aws.dynamodb.dynamodb_table import DynamoDB
from pcf.core import State

class TestDynamoDB():
    particle_definition = {
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
            }
        }
    }

    item_value = {
        "Post": {
            "S": "adding post to table"
        },
        "PostDateTime": {
            "S": "201807031301"
        }
    }

    @moto.mock_dynamodb2
    def test_apply_states(self):
        particle = DynamoDB(self.particle_definition)

        #Test start
        particle.set_desired_state(State.running)
        particle.apply()

        assert particle.get_state() == State.running
        assert particle.is_state_definition_equivalent() is True

        # test update
        self.particle_definition["aws_resource"]["ProvisionedThroughput"] = {"ReadCapacityUnits": 25, "WriteCapacityUnits": 30}

        particle = DynamoDB(self.particle_definition)

        particle.set_desired_state(State.running)
        particle.apply()

        assert particle.get_state() == State.running
        assert particle.is_state_definition_equivalent() is True

        # test put item
        particle.put_item(self.item_value)

        assert len(particle.get_item(self.item_value)['Item']) == 2

        # test terminate
        particle.delete_item(self.item_value)

        assert not particle.get_item(self.item_value).get("Item", False)

        particle.set_desired_state(State.terminated)
        particle.apply()

        assert particle.get_state() == State.terminated

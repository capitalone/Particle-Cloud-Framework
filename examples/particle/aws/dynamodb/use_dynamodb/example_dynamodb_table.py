from pcf.core import State
from pcf.particle.aws.dynamodb.dynamodb_table import DynamoDB

#example dynamodb

dynamodb_example_json = {
    "pcf_name": "pcf_dynamodb",  # Required
    "flavor": "dynamodb_table",  # Required
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
            }
        ],
        "LocalSecondaryIndexes": [
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
        "Tags": {
            "Name": "pcf-dynamodb-test"
        }
    }
}

# create dynamodb particle using json
dynamodb_particle = DynamoDB(dynamodb_example_json)

# example start
dynamodb_particle.set_desired_state(State.running)
dynamodb_particle.apply()

print(dynamodb_particle.get_state())
print(dynamodb_particle.get_current_state_definition())

# example update
dynamodb_example_json["aws_resource"]["ProvisionedThroughput"] = {"ReadCapacityUnits": 25, "WriteCapacityUnits": 30}

dynamodb_particle = DynamoDB(dynamodb_example_json)

dynamodb_particle.set_desired_state(State.running)
dynamodb_particle.apply()

# example item
key_value = {
    "Post": {
        "S": "adding post to table"
    },
    "PostDateTime": {
        "S": "201807031301"
    }
}

# example put item
dynamodb_particle.put_item(key_value)

# example get item
print(dynamodb_particle.get_item(key_value))

# example delete item
print(dynamodb_particle.delete_item(key_value))

print(dynamodb_particle.get_state())
print(dynamodb_particle.get_current_state_definition())

# example terminate
dynamodb_particle.set_desired_state(State.terminated)
dynamodb_particle.apply()

print(dynamodb_particle.get_state())

from pcf.core import State
from pcf.particle.aws.sqs.sqs_queue import SQSQueue


# example SQS particle
particle_definition = {
    "pcf_name": "gg-pcf",
    "flavor": "sqs",
    "aws_resource": {
        "QueueName": "test_SQS_queue.fifo",  # Required
        # "OwnerAwsId": "owner", # only if the queue belongs to a different user
        "Attributes": {
            # https://boto3.readthedocs.io/en/latest/reference/services/sqs.html#SQS.Client.create_queue
            # for all the validation criteria from boto3
            "DelaySeconds": "0",
            "MaximumMessageSize": "262144",
            "MessageRetentionPeriod": "345600",
            "Policy": "AWS policy",
            "ReceiveMessageWaitTimeSeconds": "20",
            # "RedrivePolicy": "{}",
            "VisibilityTimeout": "43200",
            "KmsMasterKeyId": "enc/sqs",
            "KmsDataKeyReusePeriodSeconds": "300",
            "FifoQueue": "true",
            "ContentBasedDeduplication": "true",
            # "ApproximateNumberOfMessages": "1",
            # "ApproximateNumberOfMessagesDelayed": "0",
            # "ApproximateNumberOfMessagesNotVisible": "0",
            # "CreatedTimestamp": "1534276486.369445",
            # "LastModifiedTimestamp": "1534276486.369445",
            "QueueArn": "arn:aws:sqs:us-east-1:123456789012:test_SQS_queue.fifo"
        },
        "Tags": {
            "test_tag": "value",
            "remove_tag": "bye"
        }
    }
}


# create sqs particle using json
sqs_particle = SQSQueue(particle_definition)

# example start
sqs_particle.set_desired_state(State.running)
sqs_particle.apply()

print(sqs_particle.get_state())
print(sqs_particle.get_current_definition())
print(sqs_particle.get_current_state_definition())

# example update
updated_def = particle_definition
updated_def["aws_resource"]["Attributes"]["MaximumMessageSize"] = "262143" # reset existing
updated_def["aws_resource"]["Attributes"]["ContentBasedDeduplication"] = "false" # add new
updated_def["aws_resource"]["Tags"]["new_tag"] = "new" # new tag
updated_def["aws_resource"]["Tags"]["test_tag"] = "changed" # reset tag
updated_def["aws_resource"]["Tags"].pop("remove_tag") # remove tag
sqs_particle = SQSQueue(updated_def)
sqs_particle.set_desired_state(State.running)
sqs_particle.apply()

print(sqs_particle.get_state())
print(sqs_particle.get_current_definition())
print(sqs_particle.get_current_state_definition())

# example terminate
sqs_particle.set_desired_state(State.terminated)
sqs_particle.apply()

print(sqs_particle.get_state())

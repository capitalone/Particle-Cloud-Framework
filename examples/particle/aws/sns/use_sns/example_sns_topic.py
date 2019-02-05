from pcf.particle.aws.sns.sns import SNSTopic
from pcf.core import State
import os

# Setup AWS Profile to point to AWS Account

# Edit example json to work in your account
sns_topic_example_json = {
    "pcf_name": "pcf_sns_test", # Required
    "flavor":"sns", # Required
    "aws_resource":{
        # Refer to https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns.html#SNS.Client.create_topic for full list of parameters
        "Name":"pcf-sns-test", # Required
        # "Attributes": {
        #     #"DeliveryPolicy": '', #HTTP|HTTPS|Email|Email-JSON|SMS|Amazon SQS|Application|AWS Lambda
        #     "DisplayName": "pcf-test"
        #     #"Policy": ''
        # },
        #"custom_config": {
            # subscription parameters
            # add subscription to existing Topic ARN
        #}
    }
}

# create SNS Topic particle
sns = SNSTopic(sns_topic_example_json)

# example start
sns.set_desired_state(State.running)
sns.apply()

print(sns.get_state())

# example update subscription attributes

# example terminate
sns.set_desired_state(State.terminated)
sns.apply()

print(sns.get_state())

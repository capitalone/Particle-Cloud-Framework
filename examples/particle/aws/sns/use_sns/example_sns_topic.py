from pcf.particle.aws.sns.sns import SNSTopic
from pcf.core import State
import os

# Setup AWS Profile to point to AWS Account

# Edit example json to work in your account
sns_topic_example_json = {
    "pcf_name": "pcf_sns_test", # Required
    "flavor":"sns", # Required
    "aws_resource":{
        # Refer to https://boto3.amazonaws.com/v1/documentation/api/1.9.5/reference/services/sns.html#SNS.Client.create_topic for more information
        "Name":"pcf-sns-test", # Required
        "custom_config": {
            "Attributes": {
                # "DeliveryPolicy": "", # HTTP|HTTPS|Email|Email-JSON|SMS|Amazon SQS|Application|AWS Lambda
                "DisplayName": "pcf-test"
                # "Policy": "" # dict
            },
            # subscription parameters
        }
    }
}

# create SNS Topic particle
sns = SNSTopic(sns_topic_example_json)

# example start
sns.set_desired_state(State.running)
sns.apply()

print(sns.get_state())

# example update topic attributes
updated_def = sns_topic_example_json
updated_def["aws_resource"]["Attributes"]["DisplayName"] = "new-pcf-test" # reset existing
sns = SNSTopic(updated_def)
sns.set_desired_state(State.running)
sns.apply()

# example terminate
sns.set_desired_state(State.terminated)
sns.apply()

print(sns.get_state())

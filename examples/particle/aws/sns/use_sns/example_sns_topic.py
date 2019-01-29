from pcf.particle.aws.sns.sns import SNSTopic
from pcf.core import State

# Edit example json to work in your account
sns_topic_example_json = {
    "pcf_name": "pcf_sns_topic", # Required
    "flavor":"sns", # Required
    "aws_resource":{
        # Refer to https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns.html#SNS.Client.create_topic for full list of parameters
        "Name":"pcf-test", # Required
        "Attributes": {},
        "custom_config": {
            # subscription parameters
            # add subscription to existing Topic ARN
        }
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

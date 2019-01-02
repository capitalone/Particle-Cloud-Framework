from pcf.particle.aws.iam.iam_policy import IAMPolicy
from pcf.core import State
import json


my_managed_policy = {
    'Version': '2012-10-17',
    'Statement': [
        {
            'Effect': 'Allow',
            'Action': 'logs:CreateLogGroup',
            'Resource': '*'
        },
        {
            'Effect': 'Allow',
            'Action': [
                'dynamodb:DeleteItem',
                'dynamodb:GetItem',
                'dynamodb:PutItem',
            ],
            'Resource': '*'
        }
    ]
}

update_managed_policy = {
    'Version': '2012-10-17',
    'Statement': [
        {
            'Effect': 'Allow',
            'Action': 'logs:CreateLogGroup',
            'Resource': '*'
        },
        {
            'Effect': 'Allow',
            'Action': [
                'dynamodb:DeleteItem',
                'dynamodb:GetItem',
            ],
            'Resource': '*'
        }
    ]
}

# Edit example json to work in your account
iam_policy_example_json = {
    "pcf_name": "pcf_iam_policy", # Required
    "flavor":"iam_policy", # Required
    "aws_resource":{
        "PolicyName":"pcf-test", # Required
        "PolicyDocument": json.dumps(my_managed_policy)
    }
}

# create IAM Policy particle
policy = IAMPolicy(iam_policy_example_json)

# example start
# policy.set_desired_state(State.running)
# policy.apply()
# print(policy.state)
# print(policy.current_state_definition)


# example update
# iam_policy_example_json['aws_resource']['PolicyDocument'] = json.dumps(update_managed_policy)
# policy = IAMPolicy(iam_policy_example_json)
# policy.set_desired_state(State.running)
# policy.apply()
# print(policy.current_state_definition)

# example terminate
policy.set_desired_state(State.terminated)
policy.apply()
print(policy.state)




from pcf.particle.aws.iam.iam_role import IAMRole
from pcf.core import State
import json 


assume_role_policy_document = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": "sts:AssumeRole", 
            "Principal": {
                "Service": "ec2.amazonaws.com"
            }, 
            "Effect": "Allow", 
        }
    ]
}

# Edit example json to work in your account
iam_role_example_json = {
    "pcf_name": "pcf_iam_role", # Required
    "flavor":"iam_role", # Required
    "aws_resource":{
        "custom_config": {
            "policy_arns": []

        },
        "RoleName":"pcf-test", # Required
        "AssumeRolePolicyDocument": assume_role_policy_document,
        # "Tags": [
        #     {
        #         'Key': 'string',
        #         'Value': 'string'
        #     },
        # ]
    },
}


# create IAM Policy particle
role = IAMRole(iam_role_example_json)

# example start
role.set_desired_state(State.running)
role.apply()
print(role.state)
print(role.current_state_definition)

# example update
# iam_policy_example_json['aws_resource']['PolicyDocument'] = json.dumps(update_managed_policy)
# policy = IAMPolicy(iam_policy_example_json)
# policy.set_desired_state(State.running)
# policy.apply()
# print(policy.current_state_definition)

# # example update
# policy.set_desired_state(State.terminated)
# policy.apply()
# print(policy.state)

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
            "policy_arns": ["arn:aws:iam::12345678910:policy/pcf-test", "arn:aws:iam::12345678910:policy/pcf-test2"]

        },
        "RoleName":"pcf-test", # Required
        "AssumeRolePolicyDocument": json.dumps(assume_role_policy_document),
    },
}


# create IAM Policy particle
role = IAMRole(iam_role_example_json)

# example start
role.set_desired_state(State.running)
role.apply()
print(role.state)
print(role.current_state_definition)

# remove or add policies from the policy_arns list to update iam role
# iam_role_example_json["aws_resource"]["custom_config"]['policy_arns'] = []
# print(iam_role_example_json)
# role = IAMRole(iam_role_example_json)
# role.apply()
# print(role.current_state_definition)

# example terminate
role.set_desired_state(State.terminated)
role.apply()
print(role.state)

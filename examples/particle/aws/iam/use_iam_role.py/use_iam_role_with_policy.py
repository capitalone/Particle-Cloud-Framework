from pcf.particle.aws.iam.iam_role import IAMRole
from pcf.particle.aws.iam.iam_policy import IAMPolicy
from pcf.core.quasiparticle import Quasiparticle
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
                'dynamodb:GetItem',
            ],
            'Resource': '*'
        }
    ]
}

my_managed_policy2 = {
    'Version': '2012-10-17',
    'Statement': [
        {
            'Effect': 'Allow',
            'Action': 'logs:CreateLogGroup',
            'Resource': '*'
        },
    ]
}


assume_role_policy_document = json.dumps({
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
})



quasiparticle_definition = {
    "pcf_name": "iam_role_with_iam_policy_parents",
    "flavor": "quasiparticle",
    "particles":[
        {
            "flavor": "iam_policy",
            "pcf_name":"iam_policy_parent",
            "aws_resource": {
                "custom_config": {},
                "PolicyName":"pcf-test", # Required
                "PolicyDocument": json.dumps(my_managed_policy)
            }
        },
        {
            "flavor": "iam_policy",
            "pcf_name":"iam_policy_parent2",
            "aws_resource": {
                "custom_config": {},
                "PolicyName":"pcf-test2", # Required
                "PolicyDocument": json.dumps(my_managed_policy2)
            }
        },
        {
            "flavor": "iam_role",
            "parents":["iam_policy:iam_policy_parent", "iam_policy:iam_policy_parent2"],
            "aws_resource": {
                "custom_config": {},
                "RoleName":"pcf-test", # Required
                "AssumeRolePolicyDocument": assume_role_policy_document,
            }
        }
    ]
}



iam_quasiparticle = Quasiparticle(quasiparticle_definition)

# example start

iam_quasiparticle.set_desired_state(State.running)
iam_quasiparticle.apply(sync=True)

print(iam_quasiparticle.get_state())

# example update

# example update by removing one policy
updated_quasiparticle_definition = {
    "pcf_name": "iam_role_with_iam_policy_parents",
    "flavor": "quasiparticle",
    "particles":[
        {
            "flavor": "iam_policy",
            "pcf_name":"iam_policy_parent",
            "aws_resource": {
                "PolicyName":"pcf-test", # Required
                "PolicyDocument": json.dumps(my_managed_policy)
            }
        },
        {
            "flavor": "iam_role",
            "parents":["iam_policy:iam_policy_parent"],
            "aws_resource": {
                "RoleName":"pcf-test", # Required
                "AssumeRolePolicyDocument": assume_role_policy_document,
            }
        }
    ]
}

iam_quasiparticle = Quasiparticle(updated_quasiparticle_definition)
iam_quasiparticle.set_desired_state(State.running)
iam_quasiparticle.apply(sync=True)

print(iam_quasiparticle.get_state())

# example Terminate

iam_quasiparticle.set_desired_state(State.terminated)
iam_quasiparticle.apply(sync=True)

print(iam_quasiparticle.get_state())

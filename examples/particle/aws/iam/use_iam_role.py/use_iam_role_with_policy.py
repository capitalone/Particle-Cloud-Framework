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


iam_policy_example_json = {
    "pcf_name": "pcf_iam_policy", # Required
    "flavor":"iam_policy", # Required
    "aws_resource":{
        "PolicyName":"pcf-test", # Required
        "PolicyDocument": json.dumps(my_managed_policy)
    }
}

iam_quasiparticle = Quasiparticle(quasiparticle_definition)

# example start

iam_quasiparticle.set_desired_state(State.running)
iam_quasiparticle.apply(sync=True)

print(iam_quasiparticle.get_state())

# example Terminate

iam_quasiparticle.set_desired_state(State.terminated)
iam_quasiparticle.apply(sync=True)

print(iam_quasiparticle.get_state())

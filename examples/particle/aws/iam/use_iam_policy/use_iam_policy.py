from pcf.particle.aws.iam.iam_policy import IAMPolicy
from pcf.core import State
import json


my_managed_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "logs:CreateLogGroup",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:DeleteItem",
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:Scan",
            ],
            "Resource": "*"
        }
    ]
}

# Edit example json to work in your account
iam_policy_example_json = {
    "pcf_name": "pcf_iam_policy", # Required
    "flavor":"iam_policy", # Required
    "aws_resource":{
        # Refer to https://boto3.readthedocs.io/en/latest/reference/services/s3.html#S3.Client.create_bucket for full list of parameters
        "PolicyName":"pcf-test", # Required
        "PolicyDocument": json.dumps(my_managed_policy)
    }
}

# create S3 Bucket particle
policy = IAMPolicy(iam_policy_example_json)

# example start
policy.set_desired_state(State.running)
policy.apply()
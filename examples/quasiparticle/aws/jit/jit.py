import logging
import json

from pcf.core import State
from pcf.core.quasiparticle import Quasiparticle

from pcf.particle.aws.vpc.vpc import VPC
from pcf.particle.aws.vpc.subnet import Subnet
from pcf.particle.aws.vpc.security_group import SecurityGroup
from pcf.particle.aws.ec2.ec2_instance import EC2Instance
from pcf.particle.aws.iam.iam_role import IAMRole

logging.basicConfig(level=logging.DEBUG)

for handler in logging.root.handlers:
    handler.addFilter(logging.Filter('pcf'))


vpc_definition = {
    "flavor": "vpc",
    "aws_resource": {
        "custom_config": {
            "vpc_name": "jit-vpc",
        },
        "CidrBlock":"10.0.0.0/16"
    }
}

subnet_definition = {
    "flavor": "subnet",
    "parents":["vpc:pcf-jit-example"],
    "aws_resource": {
        "custom_config": {
            "subnet_name": "jit-subnet",
        },
        "CidrBlock":"10.0.0.0/24"
    }
}

security_group_definition = {
    "flavor": "security_group",
    "parents":["vpc:pcf-jit-example"],
    "aws_resource": {
        "custom_config":{
            "IpPermissions":[
                {
                    "FromPort": 80,
                    "IpProtocol": "tcp",
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                    "ToPort": 80,
                    "Ipv6Ranges": [],
                    "PrefixListIds": [],
                    "UserIdGroupPairs": []
                }
            ]
        },
        "GroupName":"jit-sg",
        "Description":"jit-sg"
    }
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


iam_role_definition = {
    "flavor":"iam_role", # Required
    "aws_resource":{
        "custom_config": {
            "policy_arns": [],
            "IsInstanceProfile": True
        },
        "RoleName":"jit-iam", # Required
        "AssumeRolePolicyDocument": assume_role_policy_document
    },
}


ec2_definition = {
    "flavor": "ec2_instance",  # Required
    "parents":["security_group:pcf-jit-example","subnet:pcf-jit-example","vpc:pcf-jit-example", "iam_role:pcf-jit-example"],
    "aws_resource": {
        "custom_config": {
            "instance_name": "jit-ec2",  # Required
        },
        # Refer to https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.ServiceResource.create_instances for a full list of parameters
        "ImageId": "$lookup$ami$ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-20180912",  # Required  <------
        "InstanceType": "t2.nano",  # Required
        "MaxCount": 1,
        "MinCount": 1,
        "SecurityGroupIds": ["$inherit$security_group:pcf-jit-example$GroupId"],
        "SubnetId":"$inherit$subnet:pcf-jit-example$SubnetId",  # Required
        "IamInstanceProfile": {
            "Arn":  "$lookup$iam$instance-profile:jit-iam"
        },
        "UserData": "echo abc123",
    }
}

# example quasiparticle that contains all required infrastructure.

jit_example_definition = {
    "pcf_name": "pcf-jit-example",  # Required
    "flavor": "quasiparticle",  # Required
    "particles": [
        vpc_definition,
        security_group_definition,
        subnet_definition,
        iam_role_definition,
        ec2_definition
    ]
}

# create quasiparticle
jit_quasiparticle = Quasiparticle(jit_example_definition)

# start example
jit_quasiparticle.set_desired_state(State.running)
jit_quasiparticle.apply(sync=True)
print(jit_quasiparticle.get_state())


# terminate example
jit_quasiparticle.set_desired_state(State.terminated)
jit_quasiparticle.apply(sync=True)
print(jit_quasiparticle.get_state())

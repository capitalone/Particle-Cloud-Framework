import logging

from pcf.core import State
from pcf.quasiparticle.aws.ec2_route53.ec2_route53 import EC2Route53

logging.basicConfig(level=logging.DEBUG)

for handler in logging.root.handlers:
    handler.addFilter(logging.Filter('pcf'))

# Edit example json to work in your account

# example quasiparticle that contains ec2 and route53
ec2_route53_example_definition = {
    "pcf_name": "pcf-example",  # Required
    "flavor": "ec2_route53",  # Required
    "particles": [{
        "flavor": "ec2_instance",  # Required
        "multiplier": 2,
        "aws_resource": {
            "custom_config": {
                "instance_name": "pcf-ec2-test",  # Required
                "tags": {
                    "OwnerContact": "you@yourcompany.com"
                },

            },
            # Refer to https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.ServiceResource.create_instances for a full list of parameters
            "ImageId": "ami-11111111",  # Required
            "InstanceType": "t2.nano",  # Required
            "KeyName": "my-key",
            "MaxCount": 1,
            "MinCount": 1,
            "SecurityGroupIds": [
                "sg-11111111",
                "sg-22222222"
            ],
            "SubnetId": "subnet-11111111",  # Required
            "UserData": "echo abc123",
            "IamInstanceProfile": {
                "Arn": "arn:aws:iam::111111111111:instance-profile/someRole"
            },
            "BlockDeviceMappings": [  # Required
                {
                    "DeviceName": "/dev/sda1",  # DeviceName changes for different Linux distro
                    "Ebs": {
                        "DeleteOnTermination": True,
                        "VolumeSize": 100,
                        "VolumeType": "gp2"
                    }
                }
            ]
        }
    },
        {
            "flavor": "route53_record",  # Required
            "aws_resource": {
                # Refer to https://boto3.readthedocs.io/en/latest/reference/services/route53.html#Route53.Client.change_resource_record_sets for full list of parameters
                "Name": "testingtesting.aws-inno-dqa.cb4good.com.",  # Required
                "HostedZoneId": "1A1A1A1A1A1A1A",  # Required
                "TTL": 300,
                "ResourceRecords": [],  # Required
                "Type": "A"  # Required
            }
        }
    ]
}

# create ec2_route53 quasiparticle
ec2_route53_quasiparticle = EC2Route53(ec2_route53_example_definition)

# example start
ec2_route53_quasiparticle.set_desired_state(State.running)
ec2_route53_quasiparticle.apply(sync=True)
route53 = ec2_route53_quasiparticle.get_particle("route53_record", "pcf-example")
ec2 = ec2_route53_quasiparticle.get_particle("ec2_instance", "pcf-example-1")
print(ec2.get_state())
print(route53.get_state())
print(ec2_route53_quasiparticle.get_state())

# example terminate
ec2_route53_quasiparticle.set_desired_state(State.terminated)
ec2_route53_quasiparticle.apply(sync=True)
route53 = ec2_route53_quasiparticle.get_particle("route53_record", "pcf-example")
ec2 = ec2_route53_quasiparticle.get_particle("ec2_instance", "pcf-example")
print(ec2.get_state())
print(route53.get_state())

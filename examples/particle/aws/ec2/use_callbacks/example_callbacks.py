from pcf.particle.aws.ec2.ec2_instance import EC2Instance
from pcf.core import State

# Edit example json to work in your account


def example_start_callback():
    print("callback triggered after start")


def example_terminate_callback(text):
    print(text)

# example ec2 instance json
ec2_instance_example_json = {
    "pcf_name": "ec2-example",  # Required
    "flavor": "ec2_instance",  # Required
    "callbacks": {
        "start": {"function": example_start_callback},
        "terminate": {"function": example_terminate_callback, "kwargs": {"text": "terminate"}}
    },
    "aws_resource": {
        "custom_config": {
            "instance_name": "my-instance",  # Required
            "userdata_params": {
                "ENVIRONMENT_VARIABLES": [
                    "PROXY=http://proxy.mycompany.com:8080",
                    "ABC=123"
                ],
                "VAR1": "hello",
                "VAR2": "world"
            },
            "userdata_wait": True,
            "userdata_bash": True,
            "tags": {
                "Name": "pcf-ec2-example",
                "Tag1": "hello",
                "Tag2": "world",
            }
        },
        # Refer to https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.ServiceResource.create_instances for a full list of parameters
        "ImageId": "ami-11111111",  # Required
        "InstanceType": "t2.nano",
        "KeyName": "my-key",
        "MaxCount": 1,
        "MinCount": 1,
        "SecurityGroupIds": [
            "sg-11111111",
            "sg-22222222"
        ],
        "SubnetId": "subnet-11111111",  # Required
        "IamInstanceProfile": {
            "Arn": "arn:aws:iam::111111111111:instance-profile/someRole"
        },
        "BlockDeviceMappings": [  # Required
            {
                "DeviceName": "/dev/sda1",  # DeviceName changes for different Linux distro
                "Ebs": {
                    "DeleteOnTermination": True,
                    "VolumeSize": 20,
                    "VolumeType": "gp2"
                }
            }
        ]
    }
}

# Setup ec2_instance particle using a sample configuration
ec2_instance_particle = EC2Instance(ec2_instance_example_json)

# example start
ec2_instance_particle.set_desired_state(State.running)
ec2_instance_particle.apply()

print(ec2_instance_particle.get_state())
print(ec2_instance_particle.get_current_state_definition())

# example terminate
ec2_instance_particle.set_desired_state(State.terminated)
ec2_instance_particle.apply()

print(ec2_instance_particle.get_state())

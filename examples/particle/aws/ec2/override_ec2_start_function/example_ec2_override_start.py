from pcf.particle.aws.ec2.ec2_instance import EC2Instance
from pcf.core import State

# Edit example json to work in your account

# example ec2 instance json
ec2_instance_example_json = {
    "pcf_name": "ec2-test",  # Required
    "flavor": "ec2_instance",  # Required
    "aws_resource": {
        "custom_config": {
            "instance_name": "ec2-test",  # Required
            "userdata_template_file": "example_userdata.sh.j2",
            "userdata_params": {
                "ENVIRONMENT_VARIABLES": [
                    "PROXY=http://proxy.mycompany.com:8080",
                ],
                # Custom params that match userdata jinja template
                "var1": "hello",
                "var2": "world"
            }
        },
        # Refer to https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.ServiceResource.create_instances for a full list of parameters
        "ImageId": "ami-11111111",  # Required
        "InstanceType": "t2.nano",  # Required
        "KeyName": "my-key",
        "MaxCount": 1,  # Required
        "MinCount": 1,  # Required
        "SecurityGroupIds": [
            "sg-11111111",
            "sg-22222222"
        ],
        "SubnetId": "subnet-11111111",  # Required
        "IamInstanceProfile": {
            "Arn": "arn:aws:iam::111111111111:instance-profile/AAAAAAAAAA"
        },
        "tags": {
            "TAG1": "HELLO",
            "TAG2": "WORLD"
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


# New user defined EC2 instance start function
class NewEC2Start(EC2Instance):
    def __init__(self, particle_definition):
        super(NewEC2Start, self).__init__(particle_definition)

    def __call__(self):
        print("I'm new!")
        try:
            instance_id = self.get_instance_id()
        except TooManyResourceException:
            raise TooManyResourceException()
        except NoResourceException:
            return self.create()

        if self.state == State.stopped:
            return self.client.start_instances(InstanceIds=[instance_id])


ec2_instance_particle._start = NewEC2Start(ec2_instance_example_json)

# example start
ec2_instance_particle.set_desired_state(State.running)
ec2_instance_particle.apply()

print(ec2_instance_particle.get_state())
print(ec2_instance_particle.get_current_state_definition())

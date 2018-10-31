from pcf.particle.aws.ec2.ec2_instance import EC2Instance
from pcf.core import State
import os
from multiprocessing import Pool


def fn(param):
    # example ec2 instance json
    ec2_instance_example_json = {
        "pcf_name": "ec2-test",  # Required
        "flavor": "ec2_instance",  # Required
        "aws_resource": {
            "custom_config": {
                "instance_name": "pcf-test-{}".format(param["idx"]),  # Required
                "userdata_template_file": "particle/aws/ec2/ec2_run_userdata/example_userdata.sh.j2",
                "userdata_params": {
                    "ENVIRONMENT_VARIABLES": [
                        "PROXY=http://proxy.mycompany.com:8080",
                        "HTTP_PROXY=$PROXY",
                        "HTTPS_PROXY=$PROXY",
                        "http_proxy=$PROXY",
                        "https_proxy=$PROXY",
                        "NO_PROXY=169.254.169.254,.mycompany.com,127.0.0.1,localhost,$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4/)",
                        "no_proxy=$NO_PROXY"
                    ],
                    # Custom params that match userdata jinja template
                    "var1": param["var1"],
                    "var2": param["var2"]
                },
                "tags": {
                    "Name": "pcf-test",
                    "Project": "PCF"
                },

                "userdata_wait": True,  # This feature relies on IamInstanceProfile role having EC2 write access
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
            "IamInstanceProfile": {
                "Arn": "arn:aws:iam::111111111111:instance-profile/AAAAAAAAAA"
            },
            "BlockDeviceMappings": [  # Required
                {
                    # "DeviceName": "/dev/sda1", # For any Debian based Liunx distro (ex: Debian, Ubuntu, RHEL)
                    "DeviceName": "/dev/xvda",  # DeviceName changes for different Linux distro
                    "Ebs": {
                        "DeleteOnTermination": True,
                        "VolumeSize": 100,
                        "VolumeType": "gp2"
                    }
                }
            ]
        }
    }

    # Setup ec2_instance particle using sample configuration
    ec2_instance_particle = EC2Instance(ec2_instance_example_json)

    # Start EC2 instance and run your code in Userdata
    instance_name = ec2_instance_example_json['aws_resource']['custom_config']['instance_name']
    print("Creating EC2 instance {} and running your code in Userdata".format(instance_name))
    ec2_instance_particle.set_desired_state(State.running)
    ec2_instance_particle.apply()
    print("{}: {}".format(instance_name, ec2_instance_particle.get_state()))

    # Terminate EC2 instance after Userdata script is done running
    print("Terminating EC2 instance {}".format(instance_name))
    ec2_instance_particle.set_desired_state(State.terminated)
    ec2_instance_particle.apply()
    print("{}: {}".format(instance_name, ec2_instance_particle.get_state()))


# List of parameters for variables in your code
params = [
    {
        "idx": 0,
        "var1": "Hello",
        "var2": "World"
    },
    {
        "idx": 1,
        "var1": "ABC",
        "var2": "123"
    },
    {
        "idx": 2,
        "var1": "XYZ",
        "var2": "456"
    }
]

pool = Pool(processes=len(params))
pool.map(fn, params)

import logging

from pcf.core import State
from pcf.quasiparticle.aws.ecs_instance_quasi.ecs_instance_quasi import ECSInstanceQuasi

logging.basicConfig(level=logging.DEBUG)

for handler in logging.root.handlers:
    handler.addFilter(logging.Filter('pcf'))

# Edit example json to work in your account

# example ec2 instance quasiparticle
ecs_instance_quasi_example_definition = {
    "pcf_name": "pcf-example",  # Required
    "flavor": "ecs_instance_quasi",  # Required
    "particles": [{
        "flavor": "ec2_instance",  # Required
        "aws_resource": {
            "custom_config": {
                "instance_name": "pcf-ec2-test",  # Required
                "userdata_template_file": "ecs_instance_userdata.sh.j2",
            # Required (AWS ECS Agent is run via userdata script to add EC2 to the ECS cluster)
                "userdata_params": {
                    "ENVIRONMENT_VARIABLES": [
                        "HTTP_PROXY=http://proxy.mycompany.com:8080",
                        "HTTPS_PROXY=http://proxy.mycompany.com:8080",
                        "http_proxy=http://proxy.mycompany.com:8080",
                        "https_proxy=http://proxy.mycompany.com:8080",
                        "NO_PROXY=169.254.169.254,.mycompany.com,127.0.0.1,localhost,/var/run/docker.sock,$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4/)",
                        "no_proxy=169.254.169.254,.mycompany.com,127.0.0.1,localhost,/var/run/docker.sock,$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4/)",
                        "AWS_DEFAULT_REGION=us-east-1"
                    ],
                    "ecs_cluster_name": "testing-quasi",  # Required
                }
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
            "flavor": "ecs_cluster",  # Required
            "aws_resource": {
                # Refer to https://boto3.readthedocs.io/en/latest/reference/services/ecs.html#ECS.Client.create_cluster for full list of parameters
                "clusterName": "testing-quasi"  # Required
            }
        },
        {
            "flavor": "ecs_instance",  # Required
            "aws_resource": {
                "attributes": [{"name": "test", "value": "attribute"}]
            }
        }
    ]
}

# create ecs_instance quasiparticle
ec2_instance_quasiparticle = ECSInstanceQuasi(ecs_instance_quasi_example_definition)

# example start
ec2_instance_quasiparticle.set_desired_state(State.running)
ec2_instance_quasiparticle.apply()
ecs_cluster = ec2_instance_quasiparticle.get_particle("ecs_cluster", "pcf-example")
ec2 = ec2_instance_quasiparticle.get_particle("ec2_instance", "pcf-example")
print(ec2.get_state())
print(ecs_cluster.get_state())
print(ec2_instance_quasiparticle.get_state())

# example terminate

ec2_instance_quasiparticle.set_desired_state(State.terminated)
ec2_instance_quasiparticle.apply()
ecs_cluster = ec2_instance_quasiparticle.get_particle("ecs_cluster", "pcf-example")
ec2 = ec2_instance_quasiparticle.get_particle("ec2_instance", "pcf-example")
print(ec2.get_state())
print(ecs_cluster.get_state())
ec2_instance_quasiparticle.get_state()
print(ec2_instance_quasiparticle.get_state())

from pcf.particle.aws.ecs.ecs_cluster import ECSCluster
from pcf.particle.aws.ec2.ec2_instance import EC2Instance

from pcf.particle.aws.ecs.ecs_instance import ECSInstance
from pcf.core import State
from pcf.core.pcf import PCF

# Example ECS Cluster config json
# ECS Cluster is a required parent for ECS Service
ecs_cluster_example_json = {
    "pcf_name": "pcf_ecs_cluster",  # Required
    "flavor": "ecs_cluster",  # Required
    "aws_resource": {
        # Refer to https://boto3.readthedocs.io/en/latest/reference/services/ecs.html#ECS.Client.create_cluster for full list of parameters
        "clusterName": "pcf_example"  # Required
    }
}
# Setup required parent ecs_cluster particle using a sample configuration
ecs_cluster = ECSCluster(ecs_cluster_example_json)

# Example EC2 Instance config json
ec2_instance_example_json = {
    "pcf_name": "ec2-example",  # Required
    "flavor": "ec2_instance",  # Required
    "aws_resource": {
        "custom_config": {
            "instance_name": "my-instance",  # Required
            "userdata_iamparams": {
                "ENVIRONMENT_VARIABLES": [
                    "PROXY=http://proxy.mycompany.com:8080",
                    "HTTP_PROXY=$PROXY",
                    "HTTPS_PROXY=$PROXY",
                    "http_proxy=$PROXY",
                    "https_proxy=$PROXY",
                    "NO_PROXY=169.254.169.254,.mycompany.com,127.0.0.1,localhost,$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4/)",
                    "no_proxy=$NO_PROXY"
                ]
            },
            "tags": {
                "Name": "pcf-ec2-example"
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
            "Arn": "arn:aws:iam::111111111111:instance-profile/AAAAAAAAAA"
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
# Setup required parent ec2_instance particle using a sample configuration
ec2_instance = EC2Instance(ec2_instance_example_json)

# Example ECS Instance config json
ecs_instance_example_json = {
    "pcf_name": "pcf_ecs_instance", # Required
    "flavor": "ecs_instance", # Required
    "parents": [
        ecs_cluster.get_pcf_id(),  # Required. This replaces Cluster in aws_resource
        ec2_instance.get_pcf_id(),  # Required. This replaces EC2 Instance ID in aws_resource
    ],
    "aws_resource": {
    }
}
# Setup ecs_instance particle using a sample configuration
ecs_instance = ECSInstance(ecs_instance_example_json)

pcf = PCF([])
pcf.add_particles((
    ecs_cluster,
    ec2_instance,
    ecs_instance,
))
pcf.link_particles(pcf.particles)
pcf.apply(sync=True, cascade=True)

# example start
ecs_cluster.set_desired_state(State.running)
ec2_instance.set_desired_state(State.running)
ecs_instance.set_desired_state(State.running)
pcf.apply(sync=True, cascade=True)

print(ecs_instance.get_state())
print(ecs_instance.get_current_state_definition())

# example terminate
ecs_cluster.set_desired_state(State.terminated)
ec2_instance.set_desired_state(State.terminated)
ecs_instance.set_desired_state(State.terminated)
pcf.apply(sync=True, cascade=True)
print(ecs_instance.get_state())

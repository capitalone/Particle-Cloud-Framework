from pcf.particle.aws.ec2.autoscaling.launch_configuration import LaunchConfiguration
from pcf.core import State

# Edit example json to work in your account

# example lc json
asg_lc_example_json = {
    "pcf_name": "launch-configuration-example",  # Required
    "flavor": "launch_configuration",  # Required
    "aws_resource": {
        # Refer to https://boto3.readthedocs.io/en/latest/reference/services/autoscaling.html#AutoScaling.Client.create_launch_configuration for a full list of parameters
        "LaunchConfigurationName": "pcf-launch-config-example",  # Required
        "InstanceType": "t2.nano",  # Required
        "KeyName": "my-key",
        "IamInstanceProfile": "AAAAAAAAAA",
        "ImageId": "ami-11111111"  # Required
    }
}

# Setup autoscaling group launch configuration particle using a sample configuration
lc_particle = LaunchConfiguration(asg_lc_example_json)

# example start
lc_particle.set_desired_state(State.running)
lc_particle.apply()

print(lc_particle.get_state())

# Launch Configuration has no update

# example terminate
lc_particle.set_desired_state(State.terminated)
lc_particle.apply()

print(lc_particle.get_state())

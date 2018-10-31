from pcf.particle.aws.ec2.autoscaling.auto_scaling_group import AutoScalingGroup
from pcf.core import State

# Edit example json to work in your account

# example asg json
asg_instance_example_json = {
    "pcf_name": "asg-test",  # Required
    "flavor": "auto_scaling_group",  # Required
    "aws_resource": {
        # Refer to https://boto3.readthedocs.io/en/latest/reference/services/autoscaling.html#AutoScaling.Client.create_auto_scaling_group for a full list of parameters
        "AutoScalingGroupName": "asg-test",  # Required
        "LaunchConfigurationName": "AAAAAAAA",  # Required
        "MinSize": 1,  # Required
        "MaxSize": 3,  # Required
        "VPCZoneIdentifier": "subnet-1111111"  # Required
    }
}

# Setup asg_instance particle using a sample configuration
asg_particle = AutoScalingGroup(asg_instance_example_json)

# example start
asg_particle.set_desired_state(State.running)
asg_particle.apply()

print(asg_particle.get_state())

# example update
updated_def = asg_instance_example_json
updated_def['aws_resource']['MaxSize'] = 2
asg_particle = AutoScalingGroup(updated_def)
asg_particle.set_desired_state(State.running)
asg_particle.apply()

print(asg_particle.get_state())
print(asg_particle.get_current_state_definition())

# example terminate
asg_particle.set_desired_state(State.terminated)
asg_particle.apply()

print(asg_particle.get_state())

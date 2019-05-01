from pcf.particle.aws.efs.efs_instance import EFSInstance
from pcf.core import State

# example efs instance json
efs_instance_example_json = {
    "pcf_name": "pcf_efs", # Required
    "flavor": "efs", # Required
    "aws_resource": {
        "custom_config": {
            "instance_name": "efs-instance", # Required
        },
        "CreationToken": "pcfFileSystem", # Required
        "PerformanceMode": "generalPurpose"
    }
}

efs_instance_particle = EFSInstance(efs_instance_example_json)

#example start
efs_instance_particle.set_desired_state(State.running)
efs_instance_particle.apply()

print(efs_instance_particle.get_state())
print(efs_instance_particle.get_current_state_definition())

# example tags
tags = [
    {
        'Key': 'key1',
        'Value': 'value1'
    },
    {
        'Key': 'key2',
        'Value': 'value2'
    }
]

efs_instance_particle.create_tags(tags)

print(efs_instance_particle.describe_tags())

#example delete tag
key_value = [
    'key1',
]

efs_instance_particle.delete_tags(key_value)

# example terminate
efs_instance_particle.set_desired_state(State.terminated)
efs_instance_particle.apply()

print(efs_instance_particle.get_state())

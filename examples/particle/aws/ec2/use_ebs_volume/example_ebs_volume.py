from pcf.particle.aws.ec2.ebs_volume import EBSVolume
from pcf.core import State

# example ec2 instance json
ebs_volume_example_json = {
    "pcf_name": "ebs-example",  # Required
    "flavor": "ebs_volume",  # Required
    "aws_resource": {
        # Refer to https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.ServiceResource.create_volume for a full list of parameters
        'AvailabilityZone': 'us-east-1a',  # Required
        'Encrypted': True,
        'Size': 20,  # Required
        'SnapshotId': "snap-11111111111111111",
        'VolumeType': 'gp2',  # 'standard'|'io1'|'gp2'|'sc1'|'st1'  # Required
        'Tags': {
            'Name': "pcf-ebs-example", # Required
            "Tag1": "hello",
            "Tag2": "world"
        },
    }
}

# Setup ebs volume particle using a sample configuration
ebs = EBSVolume(ebs_volume_example_json)

# example start
ebs.desired_state = State.running
ebs.apply()

print('volume:', ebs.volume_id)
print('state:', ebs.state)
print('definition:', ebs.current_state_definition)

ebs_volume_example_json['aws_resource']['Tags'].pop('Tag1')
ebs_volume_example_json['aws_resource']['Tags']['Tag2'] = 'bye'
ebs_volume_example_json['aws_resource']['Size'] = 30
ebs_volume_example_json['aws_resource']['VolumeId'] = ebs.volume_id

# example update
updated_ebs = EBSVolume(ebs_volume_example_json)
updated_ebs.desired_state = State.running
updated_ebs.apply()

print('volume:', updated_ebs.volume_id)
print('state:', updated_ebs.state)
print('definition:', updated_ebs.current_state_definition)

# example terminate
updated_ebs.desired_state = State.terminated
updated_ebs.apply()

print('volume (%s) terminated' % updated_ebs.volume_id)

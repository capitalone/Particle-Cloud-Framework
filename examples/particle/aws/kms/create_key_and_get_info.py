from pcf.particle.aws.kms.kms_key import KMSKey
from pcf.core import State
import logging

logging.basicConfig()

# Example KMS particle definition
kms_definition = {
    'pcf_name': 'kms_example',
    'flavor': 'kms_key',
    'aws_resource': {
        "Description": "an example key, not used for anything",
        "Tags": [
            {
                "TagKey": "InUse",
                "TagValue": "false"
            }
        ],
        "custom_config": {
            "key_name": "pcf_kms_example"
        }
    }
}

# Start the particle
key = KMSKey(kms_definition)
key.set_desired_state(State.running)
key.apply()
print('Key is active.')
print('ARN of key is: ' + key.arn)
print('Key alias is: ' + key.name)
print('KeyId is: ' + key.key_id)

# Terminate the particle
key.set_desired_state(State.terminated)
key.apply()
print('Key scheduled for deletion. Alias has been deleted.')

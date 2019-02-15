import boto3
from moto import mock_kms
from pcf.particle.aws.kms.kms_key import KMSKey
from pcf.core import State


class TestKMSKey:
    particle_definition = {
        'pcf_name': 'kms_unit_test',
        'flavor': 'kms_key',
        'aws_resource': {
            "custom_config": {
                "key_name": "pcf_unit_test"
            }
        }
    }

    @mock_kms
    def test_apply_states(self):
        kms_client = boto3.client('kms', 'us-east-1')
        particle = KMSKey(self.particle_definition)

        # Test start from no key
        particle.set_desired_state(State.running)
        particle.apply()
        assert particle.get_state() == State.running

        # Test stop from running (test disable key)
        particle.set_desired_state(State.stopped)
        particle.apply()
        assert particle.get_state() == State.stopped

        # Test start from stopped (re-enable key)
        particle.set_desired_state(State.running)
        particle.apply()
        assert particle.get_state() == State.running

        # Test terminate from running
        particle.set_desired_state(State.terminated)
        particle.apply()
        assert particle.get_state() == State.terminated

        # Create key with boto3 and test particle pickup
        new_key_id = kms_client.create_key().get('KeyMetadata').get('KeyId')
        kms_client.create_alias(AliasName='alias/pcf_unit_test',
                                TargetKeyId=new_key_id)
        particle_2 = KMSKey(self.particle_definition)
        assert particle_2.get_state() == State.running

        # Test terminate from stopped
        particle_2.set_desired_state(State.terminated)
        particle_2.apply()
        assert particle_2.get_state() == State.terminated

        # TODO Add test for particle creation to stopped immediately

from pcf.particle.aws.kinesis.kinesis import Kinesis
from pcf.core import State
import time

example_kinesis_json = {
    "pcf_name": "pcf_example",
    "flavor": "kinesis",
    "aws_resource": {
        "StreamName": "pcfKineTest3",
        "ShardCount": 8,
        "RetentionPeriodHours": 168,
        "EncryptionType": 'KMS',
        "KeyId": 'alias/aws/kinesis',
        "Tags": [{
            "Key": "test1",
            "Value": "test2"
        }]
    }
}

kinesis_particle = Kinesis(example_kinesis_json)

#kinesis_particle._terminate()
kinesis_particle.set_desired_state(State.running)
kinesis_particle.apply()

# kinesis_particle.set_desired_state(State.terminated)
# kinesis_particle.apply()
#print(kinesis_particle.get_state())
#print(kinesis_particle.get_current_state_definition())

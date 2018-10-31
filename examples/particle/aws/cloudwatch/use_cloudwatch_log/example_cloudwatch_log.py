from pcf.core import State
from pcf.particle.aws.cloudwatch.cloudwatch_log import CloudWatchLog


# example cloudwatch log particle
particle_definition = {
    "pcf_name": "pcf_cloudwatch_log", #Required
    "flavor": "logs", #Required
    "aws_resource": {
        # https://boto3.readthedocs.io/en/latest/reference/services/logs.html#id39
        "logGroupName": "Cloud_Watch_Log_A", #Required
        # "kmsKeyId": "keyA", #Must use valid key
        "tags": {
            # key-value pairs for tags
            "removed": "tag to be removed",
            "tagA": "string"
        }
    }
}


# create cloudwatch events particle using json
cloudwatch_log_particle = CloudWatchLog(particle_definition)

# example start
cloudwatch_log_particle.set_desired_state(State.running)
cloudwatch_log_particle.apply()

print(cloudwatch_log_particle.get_state())
print(cloudwatch_log_particle.get_current_definition())
print(cloudwatch_log_particle.get_current_state_definition())

# run again without changing anything
cloudwatch_log_particle.set_desired_state(State.running)
cloudwatch_log_particle.apply()

print(cloudwatch_log_particle.get_current_definition())

# example update
updated_def = particle_definition
updated_def["aws_resource"]["tags"]["tagA"] = "new string"
updated_def["aws_resource"]["tags"]["tagB"] = "new tag"
updated_def["aws_resource"]["tags"].pop("removed")
cloudwatch_log_particle = CloudWatchLog(updated_def)
cloudwatch_log_particle.set_desired_state(State.running)
cloudwatch_log_particle.apply()

print(cloudwatch_log_particle.get_state())
print(cloudwatch_log_particle.get_current_definition())
print(cloudwatch_log_particle.get_current_state_definition())

# example terminate
cloudwatch_log_particle.set_desired_state(State.terminated)
cloudwatch_log_particle.apply()

print(cloudwatch_log_particle.get_state())

from pcf.core import State
from pcf.particle.aws.cloudwatch.cloudwatch_event import CloudWatchEvent

#example cloudwatch event
cloudwatch_event_example_json = {
    "pcf_name": "pcf_cloudwatch_event", #Required
    "flavor": "events", #Required
    "aws_resource": {
        # Refer to https://boto3.readthedocs.io/en/latest/reference/services/events.html#CloudWatchEvents.Client.put_rule for a full list of parameters
        "Name": "PCFTest", #Required
        "ScheduleExpression": "rate(1 minute)", #Required
        "EventPatten": "", #Required
        "State": "ENABLED", #Required
        "Description": "pcf cloudwatch event",
    }
}

# create cloudwatch event particle using json
cloudwatch_event_particle = CloudWatchEvent(cloudwatch_event_example_json)

#example start
cloudwatch_event_particle.set_desired_state(State.running)
cloudwatch_event_particle.apply()

print(cloudwatch_event_particle.get_state())
print(cloudwatch_event_particle.get_current_state_definition())

#example update
cloudwatch_event_example_json["aws_resource"]["State"] = 'DISABLED'
cloudwatch_event_example_json["aws_resource"]["Descriptiom"] = 'pcf cloudwatch event update'

cloudwatch_event_particle = CloudWatchEvent(cloudwatch_event_example_json)

cloudwatch_event_particle.set_desired_state(State.running)
cloudwatch_event_particle.apply()

print(cloudwatch_event_particle.get_state())
print(cloudwatch_event_particle.get_current_state_definition())


#example terminate
cloudwatch_event_particle.set_desired_state(State.terminated)
cloudwatch_event_particle.apply()

print(cloudwatch_event_particle.get_state())

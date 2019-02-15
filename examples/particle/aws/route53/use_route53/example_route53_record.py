from pcf.particle.aws.route53.route53_record import Route53Record
from pcf.core import State


# Edit example json to work in your account
route53_record_example_json = {
    "pcf_name": "route_53", # Required
    "flavor":"route53_record", # Required
    "aws_resource":{
        # Refer to https://boto3.readthedocs.io/en/latest/reference/services/route53.html#Route53.Client.change_resource_record_sets for full list of parameters
        "Name":"test.test-name.com.", # Required
        "HostedZoneId":"HostedZoneId", # Required
        "TTL":333,
        "ResourceRecords":[{"Value":"1.1.1.1"}], # Required
        "Type":"A" # Required
    }
}

# create route53 record particle
route53 = Route53Record(route53_record_example_json)

# example start
route53.set_desired_state(State.running)
route53.apply(cascade=True)

print(route53.get_state())

# example update
updated_def = route53_record_example_json
updated_def["aws_resource"]["ResourceRecords"] = [{"Value":"2.3.4.5"}]
route53 = Route53Record(updated_def)
route53.set_desired_state(State.running)
route53.apply(cascade=True)

print(route53.get_state())
print(route53.get_current_state_definition())

# example terminate
route53.set_desired_state(State.terminated)
route53.apply(cascade=True)

print(route53.get_state())

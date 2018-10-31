from pcf.particle.aws.ec2.alb.alb import ApplicationLoadBalancing
from pcf.core import State

# Edit example json to work in your account


# example alb json
alb_example_json = {
    "pcf_name": "alb-example", # Required
    "flavor": "alb", # Required
    # Refer to https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.create_load_balancer for a full list of parameters
    "aws_resource": {
    	"Name": "alb-example", # Required
	    "Subnets":
            ['subnet-11111111', 'subnet-22222222'], # Required or [SubnetMappings]
	    "SecurityGroups": ['sg-11111111'],
    	"Scheme": "internal",
	    "Tags": [
			{'Key': 'Name', 'Value': 'pcf-alb-example'},
		    {'Key':'Tag1', 'Value': 'hello'},
		    {'Key':'Tag2', 'Value': 'world'},
	    ],
      "Type": "application",
      "IpAddressType": "ipv4"
    }
}

# Setup alb particle using a sample configuration
alb_particle = ApplicationLoadBalancing(alb_example_json)

# example start
alb_particle.set_desired_state(State.running)
alb_particle.apply(sync=False)

print(alb_particle.get_state())
print(alb_particle.desired_state_definition)

# example update
updated_def = alb_example_json
updated_def['aws_resource']['Tags'][1]['Value'] = 'bye'
updated_particle = ApplicationLoadBalancing(updated_def)
updated_particle.set_desired_state(State.running)
updated_particle.apply(sync=False)

print(updated_particle.get_state())
print(updated_particle.get_current_state_definition())

#example terminate
updated_particle.set_desired_state(State.terminated)
updated_particle.apply()

print(updated_particle.get_state())

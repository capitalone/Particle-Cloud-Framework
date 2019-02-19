from pcf.particle.aws.vpc.vpc_instance import VPCInstance
from pcf.core import State

particle_definition = {
    "pcf_name": "pcf_vpc",
    "flavor": "vpc_instance",
    "aws_resource": {
        "custom_config":{
            "vpc_name":"test",
            "Tags":[{"Key":"Name","Value":"test"}]
        },
        "CidrBlock":"10.0.0.0/16",
        "AmazonProvidedIpv6CidrBlock":True
    }
}

vpc_particle = VPCInstance(particle_definition)

# example start

vpc_particle.set_desired_state(State.running)
vpc_particle.apply(sync=True)

print(vpc_particle.get_state())
print(vpc_particle.get_current_state_definition())

# example Terminate

vpc_particle.set_desired_state(State.terminated)
vpc_particle.apply(sync=True)

print(vpc_particle.get_state())

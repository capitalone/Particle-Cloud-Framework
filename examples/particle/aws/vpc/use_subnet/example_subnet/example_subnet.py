from pcf.particle.aws.vpc.subnet import Subnet
from pcf.core import State

particle_definition = {
    "pcf_name": "pcf_subnet",
    "flavor": "subnet",
    "aws_resource": {
        "custom_config":{
            "subnet_name":"test"
        },
        "CidrBlock":"10.0.0.0/16",
        "VpcId":"123456789"
    }
}

subnet_particle = Subnet(particle_definition)

# example start

subnet_particle.set_desired_state(State.running)
subnet_particle.apply(sync=True)

print(subnet_particle.get_state())
print(subnet_particle.get_current_state_definition())

# example Terminate

subnet_particle.set_desired_state(State.terminated)
subnet_particle.apply(sync=True)

print(subnet_particle.get_state())

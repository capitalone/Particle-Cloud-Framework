from pcf.particle.aws.vpc.subnet import Subnet
from pcf.particle.aws.vpc.vpc_instance import VPCInstance
from pcf.core.quasiparticle import Quasiparticle
from pcf.core import State

quasiparticle_definition = {
    "pcf_name": "subnet_with_vpc_parent",
    "flavor": "quasiparticle",
    "particles":[
        {
            "flavor": "vpc",
            "pcf_name":"vpc_parent",
            "aws_resource": {
                "custom_config":{
                    "vpc_name":"test"
                },
                "CidrBlock":"10.0.0.0/16"
            }
        },
        {
            "flavor": "subnet",
            "parents":["vpc:vpc_parent"],
            "aws_resource": {
                "custom_config":{
                    "subnet_name":"test",
                    "Tags":[{"Key":"Name","Value":"test"}]
                },
                "CidrBlock":"10.0.0.0/24"
            }
        }
    ]
}

subnet_quasiparticle = Quasiparticle(quasiparticle_definition)

# example start

subnet_quasiparticle.set_desired_state(State.running)
subnet_quasiparticle.apply(sync=True)

print(subnet_quasiparticle.get_state())
print(subnet_quasiparticle.get_particle("subnet","subnet_with_vpc_parent").current_state_definition)

# example Terminate

subnet_quasiparticle.set_desired_state(State.terminated)
subnet_quasiparticle.apply(sync=True)

print(subnet_quasiparticle.get_state())

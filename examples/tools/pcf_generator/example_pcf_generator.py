# Example on how to use pcf generator tool

# used to create running resources
vpc_definition = {
    "flavor": "vpc",
    "aws_resource": {
        "custom_config": {
            "vpc_name": "example-vpc",
        },
        "CidrBlock":"10.0.0.0/16"
    }
}

subnet_definition = {
    "flavor": "subnet",
    "aws_resource": {
        "custom_config": {
            "subnet_name": "example-subnet",
        },
        "CidrBlock":"10.0.0.0/24",
        "AvailabilityZone": "us-east-1d",
        "AvailabilityZoneId": "use1-az6",
    }
}

quasiparticle_definition = {
    "pcf_name": "pcf-example",  # Required
    "flavor": "quasiparticle",  # Required
    "particles": [
        vpc_definition,
        subnet_definition,
    ]
}


# used to create subnet definition from running subnet
base_subnet_definition = {
    "pcf_name":"example",
    "flavor": "subnet",
    "aws_resource": {
        "custom_config": {
            "subnet_name": "example-subnet",
        },
    }
}

base_quasiparticle_definition = {
    "pcf_name":"example_quasiparticle",
    "flavor":"quasiparticle",
    "particles":[
        {
            "flavor": "vpc",
            "aws_resource": {
                "custom_config": {
                    "vpc_name": "example-vpc",
                }
            }
        },
        {
            "pcf_name":"example",
            "flavor":"subnet",
            "parents":["vpc:example"],
            "aws_resource":
                {
                    "custom_config":{
                        "subnet_name":"example_subnet"
                    }
                }
        }

    ]

}

# create a vpc and subnet to be used for the example
from pcf.core.quasiparticle import Quasiparticle
from pcf.core import State
subnet_vpc_quasiparticle = Quasiparticle(quasiparticle_definition)
subnet_vpc_quasiparticle.set_desired_state(State.running)
subnet_vpc_quasiparticle.apply()

# get the full subnet definition and both print it and create pcf.json file with the definition
from pcf.tools.pcf_generator.pcf_generator import GenerateParticle
generated_subnet_particle = GenerateParticle(base_subnet_definition)
print(generated_subnet_particle.generate_definition())
generated_subnet_particle.generate_json_file()

# example of a quasiparticle using the generator
from pcf.tools.pcf_generator.pcf_generator import GenerateQuasiparticle
quasiparticle = GenerateQuasiparticle(base_quasiparticle_definition)
print(quasiparticle.generate_definition())

# terminate the subnet created in this example
subnet_vpc_quasiparticle.set_desired_state(State.terminated)
subnet_vpc_quasiparticle.apply()

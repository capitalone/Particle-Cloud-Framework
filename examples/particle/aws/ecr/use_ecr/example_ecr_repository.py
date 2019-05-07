from pcf.core import State
from pcf.particle.aws.ecr.ecr_repository import ECRRepository
from pcf.core.pcf_exceptions import *


# example ECR particle
particle_definition = {
    "pcf_name": "gg-pcf",
    "flavor": "ecr_repository",
    "aws_resource": {
        "repositoryName" : "gg-ecr",
        "tags": [
            {
                'Key': 'lolcat',
                'Value': 'ggwp'
            }
        ]
    }
}

# create ECR repository particle
ecr_particle = ECRRepository(particle_definition)

# example start
ecr_particle.set_desired_state(State.running)
ecr_particle.apply()

print(ecr_particle.get_state())
print(ecr_particle.get_current_state_definition())

# example terminate
ecr_particle.set_desired_state(State.terminated)
ecr_particle.apply()

print(ecr_particle.get_state())

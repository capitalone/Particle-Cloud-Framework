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

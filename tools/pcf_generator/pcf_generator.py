import json
from pcf.util.pcf_util import update_dict


class GenerateParticle:
    def __init__(self, particle_definition):
        # import particle class
        self.particle = flavor_class(particle_definition)
        self.particle_json = particle_definition

    def generate_definition(self):
        self.particle.sync_state()
        # TODO generic for all resources
        # TODO desired definition is not always the same format as the current_definition
        self.particle_json["aws_resource"]= update_dict(self.particle.desired_definkition,self.particle.current_definition)
        return self.particle_json

    def generate_json_file(self, path="", filename='pcf.json'):
        particle_definition = self.generate_definition()
        with open(f'{path}/{filename}', 'w') as file:
            json.dump(particle_definition, file)


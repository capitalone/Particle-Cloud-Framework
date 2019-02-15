import json
import os
from pcf.util.pcf_util import update_dict,particle_class_from_flavor


class GenerateParticle:
    def __init__(self, particle_definition):
        self.particle_class = particle_class_from_flavor(particle_definition.get("flavor"))
        self.particle = self.particle_class(particle_definition)
        self.particle_json = particle_definition

    def generate_definition(self):
        self.particle.sync_state()
        # TODO generic for all resources
        # TODO desired definition is not always the same format as the current_definition
        self.particle_json["aws_resource"]= update_dict(self.particle.desired_state_definition,self.particle.current_state_definition)
        return self.particle_json

    def generate_json_file(self, path=None, filename='pcf.json'):
        if not path:
            path = os.path.dirname((os.path.abspath(__file__)))
        particle_definition = self.generate_definition()
        with open(f'{path}/{filename}', 'w') as file:
            json.dump(particle_definition, file)


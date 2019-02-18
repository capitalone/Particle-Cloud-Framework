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
        self.particle_json["aws_resource"], _ = update_dict(self.particle.desired_state_definition,self.particle.current_state_definition)
        return self.particle_json

    def generate_json_file(self, path=None, filename='pcf.json'):
        if not path:
            path = os.path.dirname((os.path.abspath(__file__)))
        particle_definition = self.generate_definition()
        with open(f'{path}/{filename}', 'w') as file:
            json.dump(particle_definition, file)


class GenerateQuasiparticle:
    def __init__(self, quasiparticle_definition):
        self.quasiparticle_json = quasiparticle_definition

    def generate_definition(self):
        generated_particle_list=[]
        for particle in self.quasiparticle_json.get("particles"):
            if not particle.get("pcf_name"):
                particle["pcf_name"] = self.quasiparticle_json.get("pcf_name")
            generated_particle = GenerateParticle(particle)
            generated_particle_list.append(generated_particle.generate_definition())

        self.quasiparticle_json["particles"] = generated_particle_list
        return self.quasiparticle_json

    def generate_json_file(self, path=None, filename='pcf.json'):
        if not path:
            path = os.path.dirname((os.path.abspath(__file__)))
        particle_definition = self.generate_definition()
        with open(f'{path}/{filename}', 'w') as file:
            json.dump(particle_definition, file)

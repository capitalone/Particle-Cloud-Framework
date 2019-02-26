# Copyright 2018 Capital One Services, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pcf.util import pcf_util


class PCF(object):
    def __init__(self, pcf_definition_json):
        self.particles = {}
        self.pcf_definition_json = pcf_definition_json
        self.load_pcf_definition(self.pcf_definition_json)

    def load_pcf_definition(self, pcf_definition_json):
        for particle_definition in pcf_definition_json:
            self.load_particle_definition(particle_definition)

        self.link_particles(self.particles)

    def load_particle_definition(self, particle_definition):
        from pcf.core import particle_flavor_scanner
        flavor_name = particle_definition["flavor"]
        particle_flavor = particle_flavor_scanner.get_particle_flavor(flavor_name)
        particle = particle_flavor(particle_definition)
        if flavor_name not in self.particles:
            self.particles[flavor_name] = {}
        self.particles[flavor_name][particle.name] = particle

    def link_particles(self, particles_dict):
        for k, v in particles_dict.items():
            if isinstance(v, dict):
                self.link_particles(v)
            else:
                v.link_relatives(self)

    def get_particle(self, flavor, pcf_name):
        return self.particles.get(flavor, {}).get(pcf_name)

    def get_particle_from_pcf_id(self, pcf_id):
        flavor, name = pcf_util.extract_components_from_pcf_id(pcf_id)
        return self.get_particle(flavor, name)

    def get_particles(self, flavor=None):
        if flavor:
            return self.particles.get(flavor, {})
        else:
            return self.particles

    def add_particle(self, particle):
        pcf_id = particle.get_pcf_id()
        flavor, name = pcf_util.extract_components_from_pcf_id(pcf_id)

        if flavor in self.particles and name in self.particles.get(flavor, {}):
            raise Exception("Particle {} already defined".format(pcf_id))
        else:
            if flavor not in self.particles:
                self.particles[flavor] = {}
            self.particles[flavor][name] = particle

    def add_particles(self, particles):
        for particle in particles:
            self.add_particle(particle)

    def apply(self, sync=True, cascade=False, validate_config=False, max_timeout=None, particles_dict=None):
        if not particles_dict: particles_dict = self.particles
        for k, v in particles_dict.items():
            if isinstance(v, dict):
                self.apply(particles_dict=v, sync=sync, cascade=cascade, validate_config=validate_config, max_timeout=max_timeout)
            else:
                v.apply(sync=sync, cascade=cascade, validate_config=validate_config, max_timeout=max_timeout)


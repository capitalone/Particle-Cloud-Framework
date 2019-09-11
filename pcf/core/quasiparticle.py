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

from copy import deepcopy
import functools
import logging

from pcf.core.particle import Particle
from pcf.core.pcf import PCF
from pcf.core import State, STATE_STRING_TO_ENUM
from pcf.util import pcf_util
from pcf.core.pcf_exceptions import MaxTimeoutException
from pcf.util.pcf_util import particle_class_from_flavor
from pcf.core.pcf_exceptions import InvalidState

logger = logging.getLogger(__name__)


class Quasiparticle(Particle):
    flavor = 'quasiparticle'

    def __init__(self, particle_definition):
        """
        Args:
            particle_definition(json): Particle definition in json format. Contains the fields pcf_name,parents (optional), particles (list)
        """
        super(Quasiparticle, self).__init__(particle_definition)
        self.member_particles = self.particle_definition["particles"]
        self.pcf_field = PCF([])
        self.fuse()

    def fuse(self):
        """
        To override fuse() functionality reimplement _fuse_particles()

        Returns:
             _fuse_particles()
        """
        self._fuse_particles()

    def _fuse_particles(self):
        """
        This functions adds all particles to a pcf object (pcf_field). If a particle contains a multiplier field that number of particles
        are created with indexes appended to the particle's unique identifier. If the quasiparticle has a parent, that parent is added to all
        particles in the quasiparticle. Finally link_particles is called on the pcf_field.
        """
        for particle in self.member_particles:
            particle_class_from_flavor(particle.get("flavor"))
            if not particle.get("pcf_name"):
                particle["pcf_name"] = self.name
            multiplier = particle.get("multiplier", False)
            base_particle_config = particle.get("base_particle_config", False)

            if base_particle_config:
                particle = self.update_particle_definition(particle, self.pcf_field.get_particle_from_pcf_id(particle["flavor"] + ":" + base_particle_config))

            # when there is no multiplier add quasiparticle parents to particle and add particle to pcf field
            if not multiplier:
                if self.particle_definition.get("parents"):
                    particle = self.add_parents_to_particle(particle)

                self.pcf_field.load_particle_definition(particle)

            # when there is a multiplier get the unique identifers, index them, add quasiparticle parents, and then add all particles to the pcf field
            else:
                particle_name = particle["pcf_name"]
                unique_identifier_list = pcf_util.get_particle_unique_identifiers(particle['flavor'])
                unqiue_value_dict = dict([(x, pcf_util.find_nested_dict_value(particle, x.split('.'))) for x in unique_identifier_list])
                for i in range(multiplier):
                    particle_multiple = deepcopy(particle)

                    particle_multiple["pcf_name"] = particle_name + "-" + str(i)
                    # appends the correct index to each item in particle definition that is unique
                    particle_multiple = functools.reduce((lambda d,l: pcf_util.replace_value_nested_dict(d, l.split('.'), unqiue_value_dict.get(l) + '-' + str(i))), unique_identifier_list, particle_multiple)
                    if self.particle_definition.get("parents"):
                        particle_multiple = self.add_parents_to_particle(particle_multiple)

                    self.pcf_field.load_particle_definition(particle_multiple)

        self.pcf_field.link_particles(self.pcf_field.particles)

    def add_parents_to_particle(self, particle_definition):
        """
        Adds parents to particle_definition

        Args:
            particle_definition:

        Returns:
            particle_definition: updated version
        """
        if not particle_definition.get("parents"):
            particle_definition["parents"] = self.particle_definition["parents"]
        else:
            particle_definition["parents"] = particle_definition["parents"] + self.particle_definition["parents"]

        return particle_definition


    def apply(self, sync=True, cascade=True, validate_config=False, rollback=False, max_timeout=None):
        """
        Calls apply all particles via pcf_field.apply()

        Args:
            sync (bool): sync or async mode. Defaults to True
            cascade (bool): Defaults to True
            validate_config (bool): specify whether or not to call particle config validation function
            rollback (bool): If true then all particles will be terminated if there is an error during start. Defaults to False
            max_timeout (int): raise the max timeout exception after x(int) seconds reached, defaults to None
        """

        try:
            self.pcf_field.apply(sync=sync, cascade=cascade, validate_config=validate_config, max_timeout=max_timeout)
        # if exception then terminate all particles if rollback set to True
        except Exception as error:
            logger.debug("Error detected in {0}. {1}".format(self.pcf_id, error))
            if rollback:
                logger.info("Error occured while running apply() with the rollback flag is set to true. Performing rollback.")
                self.set_desired_state(State.terminated)
                self.pcf_field.apply(sync=sync, cascade=cascade, validate_config=False, max_timeout=max_timeout)
            else:
                raise error

    def sync_state(self):
        pass

    def get_state(self):
        """
        If all the particles are in the same state then the quasiparticle returns that state. Otherwise will return State.pending

        Returns:
            self.state
        """
        self.state = None
        persist_on_terminate = False
        particles = self.pcf_field.get_particles()
        for flavor in particles:
            for particle in particles[flavor]:
                particle_state = particles[flavor][particle].get_state()
                particle_persist_on_terminate = particles[flavor][particle].persist_on_termination
                if not self.state:
                    self.state = particle_state
                    persist_on_terminate = particle_persist_on_terminate
                if self.state != particle_state:
                    # check if termination protection is set to true for running particles if other paritcles are terminated
                    if (self.state == State.running and persist_on_terminate and particle_state == State.terminated) or \
                        (self.state == State.terminated and particle_persist_on_terminate and particle_state == State.running):
                        self.state = State.terminated
                    else:
                        return State.pending
        return self.state

    def set_desired_state(self, desired_state):
        """
        Sets the desired state for all particles in the quasiparticle.

        Args:

            desired_state (str): one of running,stopped,terminated.
        """
        if isinstance(desired_state, str):
            self.desired_state = STATE_STRING_TO_ENUM.get(desired_state.lower())
            if not self.desired_state:
                raise InvalidState
        else:
            self.desired_state = desired_state

        particles = self.pcf_field.get_particles()
        for flavor in particles:
            for particle in particles[flavor]:
                particles[flavor][particle].set_desired_state(desired_state=desired_state)

    def set_particle_state(self, flavor, desired_state, pcf_name=None):
        """
        Sets the state of a particular particle.

        Args:
            flavor (str):
            desired_state (State):
            pcf_name (str): default is None
        """
        if not pcf_name:
            pcf_name = self.name
        particle = self.pcf_field.get_particle(flavor=flavor, pcf_name=pcf_name)
        particle.set_desired_state(desired_state)

    def get_particle(self, flavor, pcf_name):
        """
        Returns a particle from the quasiparticle

         Args:
            flavor (str):
            pcf_name (str):

        Returns:
            Particle
        """
        return self.pcf_field.get_particle(flavor=flavor, pcf_name=pcf_name)

    def update_particle_definition(self, particle_definition, base_particle):
        """
        Updates a particle's definition with a previous definition. Replaces any fields that are specified.

        Args:
            particle_definition (dict): new particle defintion (can be empty)
            base_particle (particle): the particle that the new particle is inheriting from

        Returns:
            updated_particle_definition
        """
        updated_particle_defintion, diff_dict = pcf_util.update_dict(base_particle.particle_definition, particle_definition)
        return updated_particle_defintion


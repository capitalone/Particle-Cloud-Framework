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

from pcf.core.quasiparticle import Quasiparticle
from pcf.particle.aws.ec2.ec2_instance import EC2Instance
import logging


logger = logging.getLogger(__name__)


class DistributedMasterWorker(Quasiparticle):
    """
    This Quasiparticle works for any distributed master worker technology. This quasiparticle makes sure the masters
    are all running before the worker nodes are stood up allowing the master config vars to be passed to the workers so
    they can connect on spin up.
    """
    flavor = "distributed_master_worker"

    def __init__(self, particle_definition):
        super(DistributedMasterWorker, self).__init__(particle_definition)
        self.master = self.particle_definition['custom_config'].get('master')
        self.set_parents()

    def set_parents(self):
        """
        Checks for the master ec2 instances and adds them as a parent to all other ec2 particles.
        """
        ec2_particles = self.pcf_field.get_particles(flavor="ec2_instance")
        ec2_masters = [ec2_particles[ec2_name] for ec2_name in ec2_particles.keys() if self.master in ec2_name]
        for ec2_name in ec2_particles:
            if self.master not in ec2_name:
                self.pcf_field.particles["ec2_instance"][ec2_name].parents.update(list(ec2_masters))

        self.pcf_field.link_particles(self.pcf_field.particles)


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
from pcf.particle.aws.route53.route53_record import Route53Record
import logging


logger = logging.getLogger(__name__)


class EC2Route53(Quasiparticle):
    """
    This quasiparticle maps as many ec2 particles that you specify with the multiplier and adds them to the route53 record.
    """
    flavor = "ec2_route53"

    def __init__(self, particle_definition):
        super(EC2Route53, self).__init__(particle_definition)
        self.set_parents()

    def set_parents(self):
        """
        Adds all ec2 particles as parents to the route53 particle.
        """
        route53 = self.pcf_field.get_particles(flavor="route53_record")
        route53_record_pcf_name = route53.get("pcf_name", self.name)
        ec2_particles = self.pcf_field.get_particles(flavor="ec2_instance")

        self.pcf_field.particles["route53_record"][route53_record_pcf_name].parents.update(list(ec2_particles.values()))
        self.pcf_field.link_particles(self.pcf_field.particles)


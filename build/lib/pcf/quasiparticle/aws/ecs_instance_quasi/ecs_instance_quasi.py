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
from pcf.particle.aws.ecs.ecs_instance import ECSInstance
from pcf.particle.aws.ecs.ecs_cluster import ECSCluster
import logging


logger = logging.getLogger(__name__)


class ECSInstanceQuasi(Quasiparticle):
    """
    This quasiparticle helps manage the ecs instance resource since the resource itself relies
    on an ecs cluster and ec2 instance.
    """
    flavor = "ecs_instance_quasi"

    def __init__(self, particle_definition):
        super(ECSInstanceQuasi, self).__init__(particle_definition)
        self.set_parents()

    def set_parents(self):
        """
        Sets ec2_instance and ecs_cluster and parents for the ecs_instance.
        """
        ec2_particle = self.pcf_field.get_particle_from_pcf_id("ec2_instance:" + self.name)
        ecs_cluster_particle = self.pcf_field.get_particle_from_pcf_id("ecs_cluster:" + self.name)
        self.pcf_field.particles["ecs_instance"][self.name].parents.update([ec2_particle,ecs_cluster_particle])
        self.pcf_field.link_particles(self.pcf_field.particles)


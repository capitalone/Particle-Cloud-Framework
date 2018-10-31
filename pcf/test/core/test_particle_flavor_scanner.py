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

import pytest

from pcf.core import particle_flavor_scanner
from pcf.core.particle import Particle
from pcf.core.quasiparticle import Quasiparticle


class TestParticleFlavorScanner():
    def test_get_particle_flavor_registry(self):
        assert len(particle_flavor_scanner.get_particle_flavor_registry().keys()) > 0

    def test_get_particle_flavor(self):
        with pytest.raises(particle_flavor_scanner.InvalidInputException):
            particle_flavor_scanner.get_particle_flavor(None)

        with pytest.raises(particle_flavor_scanner.InvalidInputException):
            particle_flavor_scanner.get_particle_flavor("")

        with pytest.raises(particle_flavor_scanner.InvalidInputException):
            particle_flavor_scanner.get_particle_flavor(["ABC"])


        with pytest.raises(particle_flavor_scanner.ParticleFlavorNotFoundError):
            particle_flavor_scanner.get_particle_flavor("flavor")


        class TestParticle(Particle):
            flavor = "strange"

        assert issubclass(particle_flavor_scanner.get_particle_flavor("strange"), Particle)

        class TestQuasiparticle(Quasiparticle):
            flavor = "charm"

        assert issubclass(particle_flavor_scanner.get_particle_flavor("charm"), Quasiparticle)

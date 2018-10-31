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

import importlib
import pkgutil
import os

from pcf.core.particle import Particle

dirs = [(os.path.dirname(__file__), __package__)]


while len(dirs) > 0:
    (curr_dir, curr_pkg) = dirs.pop()
    for (module_loader, name, ispkg) in pkgutil.iter_modules([curr_dir]):
        if ispkg:
            dirs.append((os.path.join(curr_dir, name), "{}.{}".format(curr_pkg, name)))

        importlib.import_module("." + name, curr_pkg)


def get_particle_flavor(flavor: str):
    if flavor and isinstance(flavor, str):
        registry_key = flavor.lower()
        if registry_key in Particle.registry:
            return Particle.registry[registry_key]
        else:
            raise ParticleFlavorNotFoundError(flavor)
    else:
        raise InvalidInputException(flavor)


def get_particle_flavor_registry():
    return Particle.registry


class ParticleFlavorNotFoundError(Exception):
    def __init__(self, flavor):
        super(ParticleFlavorNotFoundError, self).__init__(
            "{0} particle flavor was not found".format(flavor))


class InvalidInputException(Exception):
    def __init__(self, flavor):
        super(InvalidInputException, self).__init__(
            "Particle flavor {} names cannot be empty or null".format(flavor))

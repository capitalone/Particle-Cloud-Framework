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

from pcf.core.particle import Particle
from pcf.core.quasiparticle import Quasiparticle
from pcf.core import State
from pcf.util import pcf_util
from pcf.core.pcf_exceptions import MaxTimeoutException
from pytest import raises


class ParticleTest(Particle):
    flavor = "particle_flavor"

    UNIQUE_KEYS=["nested.key_field","key"]

    def _terminate(self):
        pass

    def _update(self):
        pass

    def _start(self):
        pass

    def _stop(self):
        pass

    def sync_state(self):
        pass

    def _set_unique_keys(self):
        pass


def test_multiplier():
    test_particle_definition_multiplier = {
        "pcf_name": "pcf_particle_name",
        "flavor":"particle_flavor",
        "multiplier":3,
        "nested":{"key_field":"unique_key"},
        "key":"unique_value"
    }

    test_quasiparticle_multiplier ={
        "pcf_name":"quasiparticle",
        "particles":[test_particle_definition_multiplier],
        "flavor": "particle_flavor",
        "nested": {"key_field": "unique_key"},
        "key": "unique_value"
    }

    quasiparticle = Quasiparticle(test_quasiparticle_multiplier)
    assert(len(quasiparticle.pcf_field.particles["particle_flavor"]) == 3)
    assert(quasiparticle.pcf_field.particles["particle_flavor"].get("pcf_particle_name-0", False))
    assert(quasiparticle.get_particle("particle_flavor","pcf_particle_name-0").particle_definition["nested"]["key_field"] == "unique_key-0")
    assert(quasiparticle.get_particle("particle_flavor","pcf_particle_name-0").particle_definition["key"] == "unique_value-0")
    diff = pcf_util.diff_dict(quasiparticle.get_particle("particle_flavor","pcf_particle_name-0").particle_definition,quasiparticle.get_particle("particle_flavor","pcf_particle_name-1").particle_definition)
    assert( len(diff) == 3) # two unique keys and pcf_name should be different


def test_base_config():
    test_particle_definition_base_config_1 = {
        "pcf_name": "pcf_particle_name",
        "flavor":"particle_flavor",
        "extra_config":"extra_value",
        "override":"first_value",
        "override_nested":{"nested":"original_nested_value"},
        "nested": {"key_field": "unique_key"},
        "key": "unique_value"
    }

    test_particle_definition_base_config_2 = {
        "pcf_name": "pcf_particle_name_2",
        "flavor":"particle_flavor",
        "base_particle_config": "pcf_particle_name",
        "override":"second_value",
        "override_nested":{"nested":"new_nested_value"},
        "nested": {"key_field": "unique_key"},
        "key": "unique_value"
    }

    test_quasiparticle_base_config ={
        "pcf_name":"quasiparticle",
        "particles":[test_particle_definition_base_config_1,test_particle_definition_base_config_2 ],
        "flavor": "particle_flavor",
        "nested": {"key_field": "unique_key"},
        "key": "unique_value"
    }

    quasiparticle = Quasiparticle(test_quasiparticle_base_config)
    assert(quasiparticle.get_particle("particle_flavor","pcf_particle_name").particle_definition == test_particle_definition_base_config_1)
    assert(quasiparticle.get_particle("particle_flavor","pcf_particle_name").particle_definition["override"] == "first_value")
    assert(quasiparticle.get_particle("particle_flavor","pcf_particle_name_2").particle_definition["override"] == "second_value")
    assert(quasiparticle.get_particle("particle_flavor","pcf_particle_name_2").particle_definition["extra_config"] == "extra_value")
    assert(quasiparticle.get_particle("particle_flavor","pcf_particle_name_2").particle_definition["override_nested"]["nested"] == "new_nested_value")

class TestRollbackParticle(Particle):
    flavor = "rollback_flavor"

    def _terminate(self):
        self.state = State.terminated

    def _update(self):
        pass

    def _start(self):
        if self.name == "particle_error":
            raise ValueError("error")
        else:
            self.state = State.running

    def _stop(self):
        pass

    def sync_state(self):
        try:
            self.state
        except Exception as e:
            self.state = State.terminated
        return self.state

    def _set_unique_keys(self):
        pass

def test_rollback():
    test_particle_definition_running = {
        "pcf_name": "pcf_particle_name",
        "flavor":"rollback_flavor",
    }

    test_particle_definition_error = {
        "pcf_name": "particle_error",
        "flavor":"rollback_flavor",
    }

    test_quasiparticle_running ={
        "pcf_name":"quasiparticle",
        "particles":[test_particle_definition_running],
        "flavor": "rollback_flavor"
    }
    test_quasiparticle_rollback ={
        "pcf_name":"quasiparticle",
        "particles":[test_particle_definition_running,test_particle_definition_error ],
        "flavor": "rollback_flavor"
    }

    quasiparticle_running = Quasiparticle(test_quasiparticle_running)
    quasiparticle_running.set_desired_state(State.running)
    quasiparticle_running.apply()
    assert(quasiparticle_running.get_particle("rollback_flavor","pcf_particle_name").state == State.running)

    quasiparticle_rollback = Quasiparticle(test_quasiparticle_rollback)
    quasiparticle_rollback.set_desired_state(State.running)
    assert(quasiparticle_rollback.get_particle("rollback_flavor","pcf_particle_name").desired_state == State.running)
    assert(quasiparticle_rollback.get_particle("rollback_flavor","particle_error").desired_state == State.running)
    quasiparticle_rollback.apply(rollback=True)
    assert quasiparticle_rollback.get_state() == State.terminated
    assert(quasiparticle_rollback.get_particle("rollback_flavor","particle_error").state == State.terminated)
    assert(quasiparticle_rollback.get_particle("rollback_flavor","pcf_particle_name").state == State.terminated)

    quasiparticle_rollback.set_desired_state(State.running)
    with raises(ValueError, message='error'):
        quasiparticle_rollback.apply(rollback=False)
    # TODO issue with pytest here .fails every other time.
    # assert(quasiparticle_rollback.get_state() == State.pending)
    # assert(quasiparticle_rollback.get_particle("rollback_flavor","pcf_particle_name").state == State.running)
    # assert(quasiparticle_rollback.get_particle("rollback_flavor","particle_error").state == State.terminated)

class TestMaxTimeout(Particle):
    flavor = "quasiparticle"

    def _terminate(self):
        self.state = State.terminated

    def _update(self):
        pass

    def _start(self):
        pass

    def _stop(self):
        pass

    def sync_state(self):
        try:
            self.state
        except Exception as e:
            self.state = State.terminated
        return self.state

    def _set_unique_keys(self):
        pass

def test_max_timeout():
    test_particle_definition = {
        "pcf_name": "pcf_particle_name",
        "flavor":"quasiparticle",
    }

    test_particle_definition_2 = {
        "pcf_name": "pcf_particle_name_2",
        "flavor":"quasiparticle",
    }

    test_quasiparticle_def ={
        "pcf_name":"quasiparticle",
        "particles":[test_particle_definition, test_particle_definition_2],
        "flavor": "quasiparticle"
    }
    test_quasiparticle = Quasiparticle(test_quasiparticle_def)
    test_quasiparticle.set_desired_state(State.running)
    with raises(MaxTimeoutException):
        test_quasiparticle.apply(max_timeout=5)

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

import os.path

from pcf.core.particle import Particle
from pcf.core.quasiparticle import Quasiparticle
from pcf.core import State
from pcf.core.pcf_exceptions import InvalidConfigException, InvalidValueReplaceException, InvalidUniqueKeysException, MaxTimeoutException
from pytest import raises


class PlainParticle(Particle):
    flavor = "plain_particle"
    UNIQUE_KEYS = []

    def __init__(self,particle_definition):
        super(PlainParticle, self).__init__(particle_definition)
        self.desired_state_definition = self.particle_definition

    def _terminate(self):
        pass

    def _update(self):
        pass

    def _start(self):
        pass

    def sync_state(self):
        try:
            self.state
        except Exception as e:
            self.state = State.terminated
        return self.state

def test_max_timeout():
    test_particle_def = {
        "pcf_name": "good_particle",
        "flavor": "plain_particle",
        "aws_resource": {
            "resource_name": "some service"
        }
    }
    particle = PlainParticle(test_particle_def)
    particle.set_desired_state(State.running)
    with raises(MaxTimeoutException):
        particle.apply(max_timeout=5)


def test_set_desired_state():
    test_particle_def = {
        "pcf_name": "good_particle",
        "flavor": "plain_particle",
        "aws_resource": {
            "resource_name": "some service"
        }
    }
    particle = PlainParticle(test_particle_def)
    particle.set_desired_state("running")
    assert particle.desired_state == State.running
    particle.set_desired_state("terminated")
    assert particle.desired_state == State.terminated
    particle.set_desired_state("stopped")
    assert particle.desired_state == State.stopped


class ParticlePassingVars(Particle):
    flavor = "particle_flavor_passing_vars"

    UNIQUE_KEYS = ["aws_resource.resource_name"]

    def __init__(self, particle_definition):
        super(ParticlePassingVars, self).__init__(particle_definition)
        self.desired_state_definition = self.particle_definition

    def _terminate(self):
        self.state = State.terminated

    def _update(self):
        pass

    def _start(self):
        pass

    def _stop(self):
        pass

    def sync_state(self):
        if self.name == "parent":
            self.current_state_definition = {"item":"var_to_be_passed", "tags":[{"tag1":"a"}, {"tag2":"b"}], "nested":{"nested_key":"nested_var"}}
            self.desired_state_definition = self.current_state_definition
        self.state = State.running
        self.current_state_definition = self.desired_state_definition

    def _set_unique_keys(self):
        pass

    def _validate_config(self):
        raise InvalidConfigException()

def test_passing_vars():
    test_particle_definition_parent = {
        "pcf_name": "parent",
        "flavor":"particle_flavor_passing_vars",
        "aws_resource": {
            "resource_name": "some service"
        }
    }

    test_particle_definition_child = {
        "pcf_name": "child",
        "flavor":"particle_flavor_passing_vars",
        "parents":["particle_flavor_passing_vars:parent"],
        "parent_var":"$inherit$particle_flavor_passing_vars:parent$item",
        "nested_parent_var":"$inherit$particle_flavor_passing_vars:parent$nested.nested_key",
        "parent_list_var":"$inherit$particle_flavor_passing_vars:parent$tags",
        "no_parent_exists":"$inherit$particle_flavor_passing_vars:does_not_exist$key",
        "no_flavor_exists":"$inherit$does_not_exist:parent$key",
        "no_key_exists":"$inherit$particle_flavor_passing_vars:parent$no_key",
        "aws_resource": {
            "resource_name": "some service"
        }
    }

    test_quasiparticle_base_config ={
        "pcf_name":"quasiparticle",
        "particles":[test_particle_definition_parent,test_particle_definition_child],
        "flavor": "particle_flavor_passing_vars",
        "aws_resource": {
            "resource_name": "some service"
        }
    }

    quasiparticle = Quasiparticle(test_quasiparticle_base_config)
    quasiparticle.set_desired_state(State.running)
    with raises(InvalidValueReplaceException):
        quasiparticle.apply()

    assert(quasiparticle.get_particle("particle_flavor_passing_vars","child").particle_definition["parent_var"] == "var_to_be_passed")
    assert(quasiparticle.get_particle("particle_flavor_passing_vars","child").particle_definition["nested_parent_var"] == "nested_var")
    assert(quasiparticle.get_particle("particle_flavor_passing_vars","child").particle_definition["no_parent_exists"] == "$inherit$particle_flavor_passing_vars:does_not_exist$key")
    assert(quasiparticle.get_particle("particle_flavor_passing_vars","child").particle_definition["no_flavor_exists"] == "$inherit$does_not_exist:parent$key")
    assert(quasiparticle.get_particle("particle_flavor_passing_vars","child").particle_definition["parent_list_var"] == [{"tag1":"a"}, {"tag2":"b"}])
    assert(quasiparticle.get_particle("particle_flavor_passing_vars","child").particle_definition["no_key_exists"] == "$inherit$particle_flavor_passing_vars:parent$no_key")


def test_validate_config():
    test_particle_definition = {
        "pcf_name": "good_particle",
        "flavor":"particle_flavor_passing_vars",
        "required_field": "present",
        "aws_resource": {
            "resource_name": "some service"
        }
    }
    particle = ParticlePassingVars(test_particle_definition)
    particle.set_desired_state(State.running)
    try:
        particle.apply(validate_config=True)
        assert False
    except InvalidConfigException:
        assert True


def test_validate_uid():
    valid_particle_definition = {
        "pcf_name": "valid_particle",
        "flavor": "particle_flavor_passing_vars",
        "required_field": "present",
        "aws_resource": {
            "resource_name": "some service"
        }
    }
    try:
        ParticlePassingVars(valid_particle_definition)
        assert True
    except InvalidUniqueKeysException:
        assert False, "Valid uid triggered error"
    invalid_definitions = [
        {
            "pcf_name": "valid_particle",
            "flavor": "particle_flavor_passing_vars",
            "required_field": "present",
            "aws_resource": {
                "resource_name": ""
            }
        },
        {
            "pcf_name": "valid_particle",
            "flavor": "particle_flavor_passing_vars",
            "required_field": "present",
            "aws_resource": {
                "resource_name": None
            }
        },
        {
            "pcf_name": "valid_particle",
            "flavor": "particle_flavor_passing_vars",
            "required_field": "present",
            "aws_resource": {
            }
        },
        {
            "pcf_name": "valid_particle",
            "flavor": "particle_flavor_passing_vars",
            "required_field": "present",
        }
    ]

    for definition in invalid_definitions:
        try:
            ParticlePassingVars(definition)
            assert False, "Invalid uid did not trigger error"
        except InvalidUniqueKeysException:
            assert True

class CallbackParticle(Particle):
    flavor = "callback_particle"

    def __init__(self, particle_definition):
        super(CallbackParticle, self).__init__(particle_definition)
        self.desired_state_definition = self.particle_definition

    def _terminate(self):
        self.state = State.terminated
        return "terminating"

    def _update(self):
        pass

    def _start(self):
        self.state = State.running
        return "starting"

    def is_state_definition_equivalent(self):
        return True

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


# global x to test callbacks
x = 0
y = 1
z = "first_name"
def test_callbacks():

    def example_start_callback():
        global x
        x = 1
        print("callback triggered after start")

    def example_terminate_callback(particle, arg1):
        global x
        global y
        global z
        x = 2
        y = arg1
        z = particle.name
        print("callback triggered after termination")

    test_callback_definition = {
        "pcf_name":"name",
        "flavor":"callback_particle",
        "callbacks":{"start":{"function":example_start_callback},
                     "terminate":{"function":example_terminate_callback, "kwargs":{"arg1":4,"particle":True}}
                     }
    }

    particle = CallbackParticle(test_callback_definition)
    particle.set_desired_state(State.running)
    particle.apply()
    assert(x == 1)
    particle.set_desired_state(State.terminated)
    particle.apply()
    assert(x == 2)
    assert(y == 4)
    assert(z == "name")


def test_json_particle_definition():
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, 'test_particle_definition.json')
    particle = PlainParticle(filename)
    assert particle.desired_state_definition == {
        "pcf_name": "test_particle",
        "flavor": "plain_particle",
        "aws_resource": {
            "resource_name": "some service",
            "lookup_id": "$lookup$make_sure_commentjson_doesn't_:filter_this_out"
        }
    }

class UpdateParticle(Particle):
    flavor = "update_particle"
    UNIQUE_KEYS = []

    def __init__(self,particle_definition):
        super(UpdateParticle, self).__init__(particle_definition)
        self.desired_state_definition = self.particle_definition

    def sync_state(self):
        self.current_state_definition = {"def":"blank"}
        self.desired_state_definition = self.current_state_definition
        self.state = State.running

    def is_state_definition_equivalent(self):
        return False


def test_update_protection():
    test_update_def = {
        "pcf_name": "update_particle",
        "flavor": "update_particle",
        "persist_on_update":True
    }

    particle = UpdateParticle(test_update_def)
    particle.set_desired_state(State.running)
    particle.apply(sync=False)
    particle.desired_state_definition = {"diff"}
    particle.apply(sync=False)
    assert particle.state == State.running
    assert particle.current_state_definition != particle.desired_state_definition

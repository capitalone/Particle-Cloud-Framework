import moto
import json
import pytest
from pcf.core import State
from pcf.core import particle_flavor_scanner

from pcf.particle.aws.route53 import hosted_zone

with open("testdata.json") as f:
    testdata = json.load(f)

values = testdata.values()
values = [tuple(v) for v in values]


@pytest.mark.parametrize("definition,updated_definition,mototag", values, ids=list(testdata.keys()))
def test_apply(definition, updated_definition, mototag):
    flavor = definition.get("flavor")
    particle_class = particle_flavor_scanner.get_particle_flavor(flavor)
    mock = getattr(moto, mototag)
    with mock():
        particle = particle_class(definition)
        particle.set_desired_state(State.running)
        particle.apply()

        assert particle.get_state() == State.running

        particle = particle_class(updated_definition)
        particle.set_desired_state(State.running)
        particle.apply()

        assert particle.is_state_definition_equivalent()

        particle.set_desired_state(State.terminated)
        particle.apply()

        assert particle.get_state() == State.terminated

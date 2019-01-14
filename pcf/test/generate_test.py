import moto
from pcf.core import State
from pcf.core import particle_flavor_scanner

from pcf.particle.aws.cloudwatch import cloudwatch_log

def generate_test(definition, updated_definition, mototag):
    flavor = definition.get("flavor")
    particle_class = particle_flavor_scanner.get_particle_flavor(flavor)
    mock = getattr(moto, mototag)
    with mock():
        particle = particle_class(definition)
        particle.set_desired_state(State.running)
        particle.apply()
        print(particle.get_state() == State.running)


import moto
import json
import pytest
import boto3
import os
import placebo
from pcf.util import pcf_util
from pcf.core import State
from pcf.core import particle_flavor_scanner
from contextlib import ExitStack

from pcf.particle.aws.route53 import hosted_zone
from pcf.particle.aws.sqs.sqs_queue import SQSQueue
from pcf.particle.aws.cloudfront.cloudfront_distribution import CloudFrontDistribution


directory = os.path.dirname(__file__)
file = os.path.join(directory, 'testdata.json')
with open(file) as f:
    testdata = json.load(f)

values = testdata.values()
values = [tuple(v) for v in values]


@pytest.mark.parametrize("definition,updated_definition,test_type", values, ids=list(testdata.keys()))
def test_apply(definition, updated_definition, test_type):
    flavor = definition.get("flavor")
    particle_class = particle_flavor_scanner.get_particle_flavor(flavor)
    session = None
    with ExitStack() as stack:
        if test_type[0] == "placebo":
            session = boto3.Session()
            dirname = os.path.dirname(__file__)
            filename = os.path.join(dirname, test_type[1])
            pill = placebo.attach(session, data_path=filename)
            pill.playback()
        else:
            for context in test_type:
                stack.enter_context(getattr(moto, context)())

        particle = particle_class(definition, session)
        particle.set_desired_state(State.running)
        particle.apply()

        assert particle.get_state() == State.running
        assert particle.is_state_definition_equivalent()

        if updated_definition:
            updated_definition, diff = pcf_util.update_dict(definition, updated_definition)
            print(updated_definition)
            particle = particle_class(updated_definition)
            particle.set_desired_state(State.running)
            particle.apply()

            assert particle.is_state_definition_equivalent()

        particle.set_desired_state(State.terminated)
        particle.apply()

        assert particle.get_state() == State.terminated

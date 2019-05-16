# Copyright 2019 Capital One Services, LLC
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
from pcf.core import State
from pcf.util.pcf_util import particle_class_from_flavor, update_dict
from pcf.core.pcf_exceptions import MissingInput
import placebo
import boto3
import os
import sys
import json


def run_placebo(definition, updated_def, placebo_conf, action="record"):
    session = boto3.Session()
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, placebo_conf[1])
    pill = placebo.attach(session, data_path=filename)
    if action == "playback":
        pill.playback()
    else:
        pill.record()

    flavor = definition.get("flavor")
    particle_class = particle_class_from_flavor(flavor)

    particle = particle_class(definition, session)

    # Test start

    particle.set_desired_state(State.running)
    particle.apply(sync=True)

    print(particle.get_state() == State.running)
    print(particle.is_state_definition_equivalent())

    # Test update
    if updated_def:
        updated_definition, _ = update_dict(definition, updated_def)
        particle = particle_class(updated_definition, session)
        particle.set_desired_state(State.running)
        particle.apply(sync=True)

        print(particle.is_state_definition_equivalent())

    # Test Terminate

    particle.set_desired_state(State.terminated)
    particle.apply(sync=True)

    print(particle.get_state() == State.terminated)
    pill.stop()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise MissingInput("Missing test name")
    if len(sys.argv) == 3:
        action = sys.argv[2]
    else:
        action = "record"

    test_key = sys.argv[1]

    directory = os.path.dirname(__file__)
    file = os.path.join(directory, 'testdata.json')
    with open(file) as f:
        testdata = json.load(f)

    test_particle = testdata[test_key]
    run_placebo(*test_particle, action=action)

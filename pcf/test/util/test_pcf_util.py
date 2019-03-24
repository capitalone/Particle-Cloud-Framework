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
from pcf.util import pcf_util
from pcf.cli import commands
from pcf.cli.commands import apply, run, stop, terminate
from pcf.particle import aws
from pcf.particle.aws import ec2, s3, iam, cloudwatch
from pcf.particle.aws.ec2 import elb
from pcf.particle.aws.ec2.ec2_instance import EC2Instance
from pcf.quasiparticle.aws.ecs_instance_quasi.ecs_instance_quasi import ECSInstanceQuasi


def test_troll_update_dict_1():
    orig_dict = {
        "lolcats": { "eat": "freefood" }
    }
    updated_dict = { "lolcats": {} }
    new_dict, diff_dict = pcf_util.update_dict(orig_dict, updated_dict)
    assert(new_dict == updated_dict)
    assert(diff_dict == {
        'lolcats': {
            'original': { "eat": "freefood" },
            'updated': {},
        }
    })

def test_troll_update_dict_2():
    orig_dict = {
        "lolcats": { "eat": "freefood" }
    }
    updated_dict = { "lolcats": None }
    new_dict, diff_dict = pcf_util.update_dict(orig_dict, updated_dict)
    assert(new_dict == updated_dict)
    assert(diff_dict == {
        'lolcats': {
            'original': { "eat": "freefood" },
            'updated': None,
        }
    })

def test_troll_update_dict_3():
    orig_dict = {
        "lolcats": { "eat": "freefood" }
    }
    updated_dict = {}
    new_dict, diff_dict = pcf_util.update_dict(orig_dict, updated_dict)
    assert(new_dict == orig_dict)
    assert(diff_dict == {})

def test_troll_update_list():
    orig_dict = {
        "lolcats": ["fly"]
    }
    updated_dict = { "lolcats": [] }
    new_dict, diff_dict = pcf_util.update_dict(orig_dict, updated_dict)
    assert(new_dict == updated_dict)
    assert(diff_dict == {
        'lolcats': {
            'original': ["fly"],
            'updated': [],
        }
    })

def test_troll_update_string():
    orig_dict = {
        "lolcats": "lol"
    }
    updated_dict = { "lolcats": "" }
    new_dict, diff_dict = pcf_util.update_dict(orig_dict, updated_dict)
    assert(new_dict == updated_dict)
    assert(diff_dict == {
        'lolcats': {
            'original':"lol",
            'updated': "",
        }
    })

def test_update_dict():
    orig_dict = {}
    updated_dict = {
        "gg": "wp",
        "lol": {
            "cats": "grumpy"
        },
        "borg": ["resistance", "is", "futile"]
    }

    new_dict, diff_dict = pcf_util.update_dict(orig_dict, updated_dict)

    assert(orig_dict == {})
    assert(new_dict == updated_dict)
    assert(diff_dict == {
        "gg": {
            "new": "wp"
        },
        "lol": {
            "new": {
                "cats": "grumpy"
            }
        },
        "borg": {
            "new": ["resistance", "is", "futile"]
        }
    })

def test_update_dict_1():
    orig_dict = {
        "gg": "wp",
        "lol": {
            "cats": "grumpy"
        },
        "borg": ["resistance", "is", "futile"]
    }
    updated_dict = {
        "gg": "wp",
        "lol": {
            "cats": "grumpy"
        },
        "borg": ["resistance", "is", "futile"]
    }

    new_dict, diff_dict = pcf_util.update_dict(orig_dict, updated_dict)

    assert(new_dict == updated_dict)
    assert(diff_dict == {})

def test_update_dict_2():
    orig_dict = {
        "gg": "wp",
        "lol": {
            "cats": "grumpy"
        }
    }
    updated_dict = {
        "gg": "wp",
        "lol": {
            "cats": "grumpy"
        },
        "borg": ["resistance", "is", "futile"]
    }

    new_dict, diff_dict = pcf_util.update_dict(orig_dict, updated_dict)

    assert(new_dict == updated_dict)
    assert(diff_dict == {"borg": {"new": ["resistance", "is", "futile"]}})

def test_update_dict_3():
    orig_dict = {
        "gg": "wp",
        "lol": {
            "cats": "grumpy"
        },
        "borg": ["resistance"],
        "don't": "touch me"
    }
    updated_dict = {
        "gg": "glhf",
        "lol": {
            "cats": "grumpy",
            "rofl": "copter"
        },
        "borg": ["resistance", "is", "futile"]
    }

    diff_dict = pcf_util.diff_dict(orig_dict, updated_dict)

    assert(orig_dict == {
        "gg": "wp",
        "lol": {
            "cats": "grumpy"
        },
        "borg": ["resistance"],
        "don't": "touch me"
    })
    assert(diff_dict == {"borg": {"original": ["resistance"],
                                  "updated": ["resistance", "is", "futile"]},
                         "lol": {"rofl": {"new": "copter"}},
                         "gg": {"original": "wp", "updated": "glhf"}
                         })


    new_dict, diff_dict = pcf_util.update_dict(orig_dict, updated_dict)

    assert(new_dict == {
        "gg": "glhf",
        "lol": {
            "cats": "grumpy",
            "rofl": "copter"
        },
        "borg": ["resistance", "is", "futile"],
        "don't": "touch me"
    })
    assert(diff_dict == {"borg": {"original": ["resistance"],
                                  "updated": ["resistance", "is", "futile"]},
                         "lol": {"rofl": {"new": "copter"}},
                         "gg": {"original": "wp", "updated": "glhf"}
                         })


def test_diff_dict():
    orig = {'test': 72,'test2':66}
    update = {'test': 72,}
    diff = pcf_util.diff_dict(orig, update)

    assert(diff == {})


class AttrSearch:
    flavor = "hoos"
    value = "wahoo"

    def sync_state(self):
        pass


def test_attr_search():
    particle = AttrSearch()
    assert pcf_util.get_value_from_particles([particle], AttrSearch, "value") == "wahoo"
    try:
        pcf_util.get_value_from_particles([particle, particle], AttrSearch, "value")
        assert False
    except Exception:
        assert True


def test_pkg_submodules():
    """ Ensure submodule lists are returned given a module object or name """
    pkg_submodules = pcf_util.pkg_submodules
    expected_command_modules = (apply, run, stop, terminate)
    commands_result = pkg_submodules(commands)
    assert all(cmd_mod in commands_result for cmd_mod in expected_command_modules)

    expected_aws_modules = (ec2, s3, iam, cloudwatch, elb)
    aws_results = pkg_submodules("pcf.particle.aws")
    assert (aws_mod in aws_results for aws_mod in expected_aws_modules)

def test_pkg_submodules_nonexistent_module():
    """ Ensure an empty list is returned for non-importable/nonexistent modules """
    pkg_submodules = pcf_util.pkg_submodules
    result = pkg_submodules("non-existent-module")
    assert result == []

def test_particle_class_from_flavor():
    """ Ensure Particle/Quasiparticle classes are returned if the flavor exists """
    particle_class_from_flavor = pcf_util.particle_class_from_flavor
    ec2_instance_class = particle_class_from_flavor("ec2_instance")
    ecs_instance_quasi_class = particle_class_from_flavor("ecs_instance_quasi")
    no_particle_class = particle_class_from_flavor("no particle for this flavor")

    assert ec2_instance_class == EC2Instance
    assert ecs_instance_quasi_class == ECSInstanceQuasi
    assert no_particle_class is None

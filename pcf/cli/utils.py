""" Utility functions for the PCF CLI """

import os
import sys
import json
import click
import yaml
import inspect
import pkgutil
import importlib
from math import ceil
from Levenshtein import distance
from pcf.core import State
from pcf.core import pcf_exceptions
from pcf.util.pcf_util import particle_class_from_flavor


def click_options(options):
    """ Decorator used to add a list of click.options to click command functions """

    def _add_options(func):
        for option in options:
            func = option(func)
        return func

    return _add_options


def color(color):
    """ Return the desired color name or None if the NO_COLOR env var is set
        https://no-color.org
    """
    return None if bool(os.environ.get("NO_COLOR")) else color


def fail(error_msg, fg="red"):
    """ Display the error message and fail the CLI """
    click.secho(error_msg, fg=color(fg))
    sys.exit(1)


def similar_strings(given_str, search_list=[]):
    """ Returns a list of similar strings to given_str from an iterable of potentially
        similar strings, search_list.
    """
    threshold = ceil(len(given_str) / 2.5)
    similar = [
        st for st in search_list if distance(given_str.lower(), st.lower()) <= threshold
    ]
    return similar


def did_you_mean(suggestions=[], fg=None, exit_after=True, exit_code=1):
    """ Print the 'Did you mean' message for the given suggestion string(s) in the
        optional color.
    """
    suggestions = list(suggestions)
    suffix = "this" if len(suggestions) == 1 else "one of these"
    cmd_list = "\t" + "\n\t".join(suggestions)
    help_msg = "\nDid you mean {0}?\n{1}".format(suffix, cmd_list)
    click.secho(help_msg, fg=color(fg))

    if exit_after:
        sys.exit(exit_code)


def load_pcf_config_from_file(filename):
    """ Attempts to load and return the config dict as specified in the given file with
        the following default config file precedence:
        1. pcf.json
        2. pcf.yml
        3. pcf.yaml
    """
    file_ext = os.path.splitext(filename)[1]
    basename = os.path.basename(filename)

    if file_ext not in (".json", ".yml", ".yaml"):
        fail(
            (
                "Error: {0} is not a valid PCF config file:\n\nPCF supports JSON and "
                "YAML config files. Valid file extensions are .json, .yml, and .yaml"
            ).format(basename)
        )

    if basename == "pcf.json":
        for default_config_file in ("pcf.json", "pcf.yml", "pcf.yaml"):
            if os.path.isfile(default_config_file):
                return read_config_file(default_config_file)
        fail(
            (
                "Error: could not find a PCF config file.\n\n"
                "If your config file is not named 'pcf.json', 'pcf.yml', or 'pcf.yaml',\n"
                "make sure you are using the '--file' option to specify the name of your "
                "config file, e.g.\n\n\tpcf apply --file my_pcf_config.json"
            )
        )

    if os.path.isfile(filename):
        return read_config_file(filename)
    else:
        fail(
            (
                "Error: could not find PCF config file {0}\n\n"
                "If your config file is not named 'pcf.json', 'pcf.yml', or 'pcf.yaml',\n"
                "make sure you are using the '--file' option to specify the name of your"
                "config file, e.g.\n\n\tpcf apply --file {0}"
            ).format(filename)
        )


def read_config_file(filename):
    """ Loads the JSON/YAML filename and returns it as a dict.
    """
    file_ext = os.path.splitext(filename)[1]
    basename = os.path.basename(filename)

    with open(filename, "r") as config_file:
        try:
            if file_ext == ".json":
                pcf_config = json.load(config_file)
            else:
                pcf_config = yaml.safe_load(config_file.read())

            if isinstance(pcf_config, dict):
                pcf_config = [pcf_config]

            return pcf_config, filename

        except (ValueError, yaml.YAMLError) as error:
            fail("Error reading PCF config file {0}:\n\n{1}".format(filename, error))


def particle_class_instance(flavor, particle_config):
    """ Return a particle class from a flavor or handle CLI error message """
    particle_class = particle_class_from_flavor(str(flavor).strip())
    if particle_class is None:
        fail(
            "Error: {} is not a supported Particle or Quasiparticle flavor ".format(
                flavor
            )
        )
    else:
        return particle_class(particle_config)


def particles_from_file(pcf_name, filename, quiet=False):
    """ Return a list of Particles from a PCF config file, returning only one Particle
        if pcf_name is not None
    """
    pcf_config, used_config_filename = load_pcf_config_from_file(filename)

    user_pcf_names = []
    particles_to_return = []
    for particle in pcf_config:
        if not isinstance(particle, dict):
            continue

        name = particle.get("pcf_name")
        flavor = particle.get("flavor")
        user_pcf_names.append(name)

        if flavor is None:
            fail("Error: No flavor specified in {} configuration".format(name))

        if pcf_name:
            if name.strip() == pcf_name.strip():
                if not quiet:
                    click.secho(
                        "Loading Particle/Quasiparticle flavor {0} for {1}...".format(
                            flavor, pcf_name
                        ),
                        fg=color("blue"),
                    )
                return [particle_class_instance(flavor, particle)]
        else:
            particles_to_return.append(particle_class_instance(flavor, particle))

    if pcf_name:
        click.secho(
            "Error: could not find Particle or Quasiparticle '{0}' in {1}".format(
                pcf_name, os.path.basename(used_config_filename)
            ),
            fg=color("red"),
        )

        similar_names = similar_strings(pcf_name, user_pcf_names)
        if similar_names:
            did_you_mean(similar_names)
        else:
            sys.exit(1)
    else:
        return particles_to_return


def execute_applying_command(
    pcf_name, config_file, desired_state, cascade=False, quiet=False, timeout=None
):
    """ Executes the apply command for the desired particle(s) and state as specified in
        the config_file. Used for apply, run, stop, and terminate commands. Contains
        CLI output for info.
    """
    particles = particles_from_file(pcf_name, config_file, quiet=quiet)
    num_particles = len(particles)

    if num_particles == 0:
        click.secho("No particle or quaisparticle definitions found.")

    elif num_particles > 1:
        with click.progressbar(
            particles,
            label="Applying changes to {} particles".format(num_particles),
            length=num_particles,
        ) as particle_progress:

            for particle in particle_progress:
                pcf_name = particle.name
                particle.set_desired_state(getattr(State, desired_state))

                try:
                    particle.apply(cascade=cascade, max_timeout=timeout)
                except pcf_exceptions.MaxTimeoutException:
                    fail("Error: Max timeout of {0} seconds reached".format(timeout))

    else:
        particle = particles[0]
        pcf_name = particle.name

        if not quiet:
            click.secho(
                "Setting desired state of {0} to {1}...".format(
                    pcf_name, desired_state
                ),
                fg=color("blue"),
            )

        particle.set_desired_state(getattr(State, desired_state))

        if not quiet:
            click.secho("Applying changes to {0}...".format(pcf_name), fg=color("blue"))

        try:
            particle.apply(cascade=cascade, max_timeout=timeout)
        except pcf_exceptions.MaxTimeoutException:
            fail("Error: Max timeout of {0} seconds reached".format(timeout))

        if not quiet:
            click.secho(
                "Successfully applied changes to {0}".format(pcf_name),
                fg=color("green"),
            )

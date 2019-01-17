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


def pkg_submodules(package, recursive=True):
    """ Return a list of all submodules in a given package, recursively by default """
    if isinstance(package, str):
        package = importlib.import_module(package)

    submodules = []
    for _loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + "." + name
        submodules.append(importlib.import_module(full_name))
        if recursive and is_pkg:
            submodules += pkg_submodules(full_name)

    return submodules


def particle_class_from_flavor(flavor):
    """ Return the class object of the given flavor (or None) by searching
        through all particle and quasiparticle submodules in the pcf module
    """

    particle_submodules = pkg_submodules("pcf.particle")
    quasiparticle_submodules = pkg_submodules("pcf.quasiparticle")
    modules = particle_submodules + quasiparticle_submodules

    for module in modules:
        classes = inspect.getmembers(module, inspect.isclass)

        if classes:
            for _name, class_obj in classes:
                if getattr(class_obj, "flavor", None) == flavor:
                    return class_obj

    return None


def particle_from_file(pcf_name, filename):
    """ Search for the Particle class object of the desired flavor as specified in
        the given config file and return it
    """
    pcf_config, used_config_filename = load_pcf_config_from_file(filename)

    user_pcf_names = []
    for particle in pcf_config:
        if not isinstance(particle, dict):
            continue

        name = particle.get("pcf_name")
        user_pcf_names.append(name)

        if name.strip() == pcf_name.strip():
            flavor = particle.get("flavor")
            if flavor is None:
                fail("Error: No flavor specified in {} configuration".format(pcf_name))

            particle_class = particle_class_from_flavor(str(flavor).strip())
            if particle_class is None:
                fail("Error: {} is not a supported Particle or Quasiparticle flavor ".format(flavor))
            else:
                return particle_class(particle)

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


def execute_applying_command(pcf_name, config_file, desired_state, silent=False):
    """ Executes the apply command for the desired particle and state as specified in
        the config_file. Used for apply, run, stop, and terminate commands. Contains
        CLI output for info.
    """
    if not silent:
        click.secho(
            "Loading Particle/Quasiparticle flavor for {0}...".format(pcf_name),
            fg=color("blue"),
        )

    particle = particle_from_file(pcf_name, config_file)

    if not silent:
        click.secho(
            "Setting desired state of {0} to {1}...".format(pcf_name, desired_state),
            fg=color("blue"),
        )

    particle.set_desired_state(getattr(State, desired_state))

    if not silent:
        click.secho("Applying changes to {0}...".format(pcf_name), fg=color("blue"))

    particle.apply()

    if not silent:
        click.secho(
            "Successfully applied changes to {0}".format(pcf_name), fg=color("green")
        )

""" Utility functions for the PCF CLI """

import os
import sys
import click
import inspect
import pkgutil
import importlib
from math import ceil
from Levenshtein import distance


def no_color():
    """ Determine if user has set the NO_COLOR environment variable to any value
        https://no-color.org
    """
    return bool(os.environ.get("NO_COLOR"))


def color(color):
    """ Return the desired color name or None if the NO_COLOR env var is set """
    return None if no_color() else color


def fail(error_msg, fg="red"):
    """ Display the error message and fail the CLI """
    click.secho(error_msg, fg=color(fg))
    sys.exit(1)


def similar_strings(given_str, search_list=[]):
    """ Returns a list of similar strings to given_str from an iterable of potentially
        similar strings, search_list.
    """
    threshold = ceil(len(given_str) / 2.5)
    similar = [st for st in search_list if distance(given_str, st) <= threshold]
    return similar


def did_you_mean(suggestions=[], fg=None, exit_after=True, exit_code=1):
    """ Print the 'Did you mean' message for the given suggestion string(s) in the
        optional color.
    """
    suggestions = list(suggestions)
    suffix = "this" if len(suggestions) == 1 else "one of these"
    cmd_list = "\t" + "\n\t".join(similar_commands)
    help_msg = "\nDid you mean {0}?\n{1}".format(suffix, cmd_list)
    click.secho(help_msg, fg=color(fg))

    if exit_after:
        sys.exit(exit_code)

def pkg_submodules(package, recursive=True):
    """ Return a list of all submodules in a given package, recursively if desired """
    if isinstance(package, str):
        package = importlib.import_module(package)

    submodules = []
    for _loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + "." + name
        submodules.append(importlib.import_module(full_name))
        if recursive and is_pkg:
            submodules.append(import_submodules(full_name))

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

""" Utility functions for the PCF CLI """

import os
import sys
import click

def no_color():
    """ Determine if user has set the NO_COLOR environment variable to any value
        https://no-color.org
    """
    return bool(os.envion.get('NO_COLOR'))

def color(color):
    """ Return the desired color name or None if the NO_COLOR env var is set """
    return None if no_color() else color


def fail(error_msg):
    """ Display the error message and fail the CLI """
    click.secho(error_msg, fg=color("red"))
    sys.exit(1)

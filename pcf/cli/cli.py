""" Top-level CLI module for interacting with PCF Particles and Quasiparticles """

import os
import importlib
import click
from pcf.cli.utils import fail
from pcf import VERSION

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


class PCFCLI(click.MultiCommand):

    command_directory = os.path.join(os.path.dirname(__file__), "commands")

    @staticmethod
    def print_version(ctx):
        """ Print the pcf version """
        click.echo("Particle Cloud Framework\n\nv{}".format(VERSION))

    def get_command(self, ctx, cmd_name):
        """ Attempt to load and return the command provided by the user """
        try:
            mod = importlib.import_module(
                "pcf.cli.commands.{}".format(cmd_name), cmd_name
            )
            return getattr(mod, cmd_name)
        except ModuleNotFoundError:
            fail("'{}' is not a vaild command".format(cmd_name))


@click.command(
    cls=PCFCLI,
    invoke_without_command=True,
    options_metavar="[--version] [--help]",
    subcommand_metavar="<command> [<args>...]",
    context_settings=CONTEXT_SETTINGS,
)
@click.option("-v", "--version", is_flag=True, is_eager=True, help="Show PCF version.")
@click.pass_context
def cli(ctx, version):
    """ Particle Cloud Framework """

    if version:
        ctx.command.print_version(ctx)


if __name__ == "__main__":
    cli()

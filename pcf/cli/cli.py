""" Top-level CLI module for interacting with PCF Particles and Quasiparticles """

import os
import importlib
import click
from pcf.cli.utils import color, fail, similar_strings
from pcf import VERSION
from Levenshtein import distance

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


class PCFCLI(click.MultiCommand):

    command_directory = os.path.join(os.path.dirname(__file__), "commands")
    supported_commands = ["apply"]

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
            error_msg = "'{}' is not a vaild command.".format(cmd_name)
            similar_commands = similar_strings(cmd_name, self.supported_commands)

            if similar_commands:
                suffix = "this" if len(similar_commands) == 1 else "one of these"
                cmd_list = "\t" + "\n\t".join(similar_commands)
                help_msg = "\nDid you mean {0}?\n{1}".format(suffix, cmd_list)
            else:
                help_msg = "\nRun 'pcf --help' for a list of all available commands."

            click.secho(error_msg, fg=color("red"))
            fail(help_msg, fg=None)


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

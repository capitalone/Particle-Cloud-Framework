""" Top-level CLI module for interacting with PCF Particles and Quasiparticles """

import os
import importlib
import click
from pcf.cli.utils import color, fail, did_you_mean, similar_strings
from pcf import VERSION

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


class PCFCLI(click.MultiCommand):

    command_dir = os.path.join(os.path.dirname(__file__), "commands")

    @staticmethod
    def print_version(ctx):
        """ Print the pcf version """
        click.echo("Particle Cloud Framework\n\nv{}".format(VERSION))
        ctx.exit()

    def list_commands(self, ctx=None):
        """ List command names and their descriptions """
        cmds = [
            cmd[:-3]
            for cmd in os.listdir(self.command_dir)
            if cmd.endswith(".py") and cmd != "__init__.py"
        ]
        cmds.sort()
        return cmds

    def get_command(self, ctx, cmd_name):
        """ Attempt to load and return the command provided by the user """
        try:
            mod = importlib.import_module(
                "pcf.cli.commands.{}".format(cmd_name), cmd_name
            )
            return getattr(mod, cmd_name)

        except ModuleNotFoundError:
            error_msg = "'{}' is not a vaild command.".format(cmd_name)
            similar_commands = similar_strings(cmd_name, self.list_commands())

            click.secho(error_msg, fg=color("red"))
            if similar_commands:
                did_you_mean(similar_commands)
            else:
                fail(
                    "\nRun 'pcf --help' for a list of all available commands.", fg=None
                )


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
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.command.get_help(ctx))
        ctx.exit()


if __name__ == "__main__":
    cli()

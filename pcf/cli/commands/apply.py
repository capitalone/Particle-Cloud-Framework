""" Logic for pcf apply command """

import click
from pcf.cli.utils import execute_applying_command, click_options
from pcf.cli.commands import COMMON_OPTIONS


@click.command(name="apply", short_help="Set a desired state and apply changes")
@click.option(
    "-s",
    "--state",
    type=click.Choice(["running", "stopped", "terminated"], case_sensitive=False),
    default="running",
    show_default=True,
    help="The desired state to set for your infrastructure",
)
@click_options(COMMON_OPTIONS)
@click.argument("pcf_name", required=True)
@click.pass_context
def apply(ctx, pcf_name, cascade, quiet, file_, state):
    """ Set a desired state and apply changes to your infrastructure

        PCF_NAME : The deployment name to apply changes to as specified in your
        PCF config file, e.g.

            pcf apply my_ec2_instance
    """

    execute_applying_command(pcf_name, file_, state, cascade=cascade, quiet=quiet)

""" Logic for pcf apply command """

import click
from pcf.cli.utils import execute_applying_command


@click.command(name="apply", short_help="Set a desired state and apply changes")
@click.option(
    "-f",
    "--file",
    "file_",
    type=click.Path(dir_okay=False, resolve_path=True),
    default="pcf.json",
    show_default=True,
    help="The JSON or YAML file defining your infrastructure configuration",
)
@click.option(
    "-s",
    "--state",
    type=click.Choice(["running", "stopped", "terminated"], case_sensitive=False),
    default="running",
    show_default=True,
    help="The desired state to set for your infrastructure",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Execute apply in quiet mode (No output except for errors)",
)
@click.option(
    "-c",
    "--cascade",
    is_flag=True,
    help="Apply state transitions to all family members",
)
@click.argument("pcf_name", required=True)
@click.pass_context
def apply(ctx, pcf_name, cascade, quiet, file_, state):
    """ Set a desired state and apply changes to your infrastructure

        PCF_NAME : The deployment name to apply changes to as specified in your
        PCF config file, e.g.

            pcf apply my_ec2_instance
    """

    execute_applying_command(pcf_name, file_, state, cascade=cascade, quiet=quiet)

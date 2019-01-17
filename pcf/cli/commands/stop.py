""" Logic for pcf stop command """

import click
from pcf.core import State
from pcf.cli.utils import execute_applying_command


@click.command(
    name="stop", short_help="Set desired state to 'stopped' and apply changes"
)
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
    "-q",
    "--quiet",
    is_flag=True,
    help="Execute stop in quiet mode (No output except for errors)",
)
@click.option(
    "-c",
    "--cascade",
    is_flag=True,
    help="Apply state transitions to all family members",
)
@click.argument("pcf_name", required=True)
@click.pass_context
def stop(ctx, pcf_name, cascade, quiet, file_):
    """ Set desired state to 'stopped' and apply changes

        PCF_NAME : The deployment name to apply changes to as specified in your
        PCF config file, e.g.

            pcf stop my_ec2_instance
    """

    execute_applying_command(pcf_name, file_, "stopped", cascade=cascade, quiet=quiet)

""" Logic for pcf run command """

import click
from pcf.core import State
from pcf.cli.utils import execute_applying_command, click_options
from pcf.cli.commands import COMMON_OPTIONS


@click.command(
    name="run", short_help="Set desired state to 'running' and apply changes"
)
@click_options(COMMON_OPTIONS)
@click.argument("pcf_name", required=True)
@click.pass_context
def run(ctx, pcf_name, cascade, quiet, file_):
    """ Set desired state to 'running' and apply changes\n

        PCF_NAME : The deployment name to apply changes to as specified in your
        PCF config file, e.g.

            pcf run my_ec2_instance
    """

    execute_applying_command(pcf_name, file_, "running", cascade=cascade, quiet=quiet)

""" Logic for pcf run command """

import click
from pcf.core import State
from pcf.cli.utils import execute_applying_command, click_options
from pcf.cli.commands import COMMON_APPLY_OPTIONS


@click.command(name="run", short_help="Set desired state to 'running' and apply")
@click_options(COMMON_APPLY_OPTIONS)
@click.argument("pcf_name", required=False)
@click.pass_context
def run(ctx, pcf_name, cascade, quiet, file_, timeout):
    """ Set desired state to 'running' and apply

        PCF_NAME : The deployment name to apply changes to as specified in your
        PCF config file, e.g.

            pcf run my_ec2_instance

        If no PCF_NAME is specified, this command will set the desired state to
        'running' for all Particles and Quasiparticles in your PCF config file.
    """

    execute_applying_command(
        pcf_name, file_, "running", cascade=cascade, quiet=quiet, timeout=timeout
    )

""" Logic for pcf stop command """

import click
from pcf.core import State
from pcf.cli.utils import execute_applying_command, click_options
from pcf.cli.commands import COMMON_APPLY_OPTIONS


@click.command(name="stop", short_help="Set desired state to 'stopped' and apply")
@click_options(COMMON_APPLY_OPTIONS)
@click.argument("pcf_name", required=False)
@click.pass_context
def stop(ctx, pcf_name, cascade, quiet, file_, timeout):
    """ Set desired state to 'stopped' and apply

        PCF_NAME : The deployment name to apply changes to as specified in your
        PCF config file, e.g.

            pcf stop my_ec2_instance

        If no PCF_NAME is specified, this command will set the desired state to
        'stopped' for all Particles and Quasiparticles in your PCF config file.
    """

    execute_applying_command(
        pcf_name, file_, "stopped", cascade=cascade, quiet=quiet, timeout=timeout
    )

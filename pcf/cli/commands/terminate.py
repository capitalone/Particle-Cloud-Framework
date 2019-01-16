""" Logic for pcf stop command """

import click
from pcf.core import State
from pcf.cli.utils import execute_applying_command


@click.command(name="terminate")
@click.option(
    "-f",
    "--file",
    "file_",
    type=click.Path(dir_okay=False, resolve_path=True),
    default="pcf.json",
    show_default=True,
    help="The JSON or YAML file defining your infrastructure configuration",
)
@click.argument("pcf_name", required=True)
@click.pass_context
def terminate(ctx, pcf_name, file_):
    """ Set desired state to 'terminated' and apply changes to your infrastructure\n
        PCF_NAME : The deployment name to apply changes to as specified in your
        PCF config file, e.g.\n\n\tpcf terminate my_ec2_instance
    """

    execute_applying_command(pcf_name, file_, 'terminated')
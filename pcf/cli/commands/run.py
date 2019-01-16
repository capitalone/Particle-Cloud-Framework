""" Logic for pcf run command """

import click
from pcf.core import State
from pcf.cli.utils import execute_applying_command


@click.command(name="run", short_help="Set desired state to 'run' and apply changes")
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
def run(ctx, pcf_name, file_):
    """ Set desired state to 'running' and apply changes\n

        PCF_NAME : The deployment name to apply changes to as specified in your
        PCF config file, e.g.

            pcf run my_ec2_instance
    """

    execute_applying_command(pcf_name, file_, "running")

""" Logic for pcf apply command """

import click
from pcf.cli.utils import execute_applying_command


@click.command(name="apply")
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
@click.argument("pcf_name", required=True)
@click.pass_context
def apply(ctx, pcf_name, file_, state):
    """ Set desired state and apply changes to your infrastructure\n
        PCF_NAME : The deployment name to apply changes to as specified in your
        PCF config file, e.g.\n\n\tpcf apply my_ec2_instance
    """

    execute_applying_command(pcf_name, file_, state)
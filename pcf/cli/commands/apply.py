""" Logic for pcf apply command """

import click


@click.command(name="apply")
@click.pass_context
def apply(ctx):
    """ Set desired state and apply changes """
    click.echo("apply command placeholder")

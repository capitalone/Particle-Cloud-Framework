import click

COMMON_APPLY_OPTIONS = [
    click.option(
        "-f",
        "--file",
        "file_",
        type=click.Path(dir_okay=False, resolve_path=True),
        default="pcf.json",
        show_default=True,
        help="The JSON or YAML file defining your infrastructure configuration",
    ),
    click.option(
        "-q",
        "--quiet",
        is_flag=True,
        help="Execute in quiet mode (No output except for errors)",
    ),
    click.option(
        "-c",
        "--cascade",
        is_flag=True,
        help="Apply state transitions to all family members",
    ),
    click.option(
        "-t",
        "--timeout",
        type=int,
        help="The maximum number of seconds to wait before a timeout error is thrown",
    ),
]

""" Reusable pytest fixtures """

import pytest
from click.testing import CliRunner

@pytest.fixture(scope="module")
def cli_runner():
    """ Provide a convenience CliRunner instance to prevent per-test instantiation """
    return CliRunner()

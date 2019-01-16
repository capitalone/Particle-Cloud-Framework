""" Reusable pytest fixtures """

import os
import shutil
import pytest
from click.testing import CliRunner


@pytest.fixture(scope="module")
def cli_runner():
    """ Provide a convenience CliRunner instance to prevent per-test instantiation """
    return CliRunner()


@pytest.fixture(scope="module")
def copy_pcf_config_file():
    """ Returns a function that moves the specified pcf config files in fixtures/ into
        the current working directory during test execution. This is useful when testing
        within a click.isolated_filesystem to test the CLI
    """

    def move_pcf_config_file(config_filepath="pcf.json"):
        """ Returned function performing the config file move. config_filepath should be
            relative to the fixtures/ directory, e.g. 'pcf.yml' to copy
            pcf/test/fixtures/pcf.yml to the current working directory.
        """
        filename = os.path.split("/")[1]
        filepath = os.path.join(os.path.dirname(__file__), "fixtures", config_filepath)
        shutil.copy(filepath, os.getcwd())

    return move_pcf_config_file

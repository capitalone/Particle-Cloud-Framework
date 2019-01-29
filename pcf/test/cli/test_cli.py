""" Tests for top-level pcf CLI """

import click
import pytest
from pcf import VERSION
from pcf.cli.cli import cli, PCFCLI


class TestCli:
    @pytest.mark.parametrize("flag", ["-v", "--version"])
    def test_cli_prints_version(self, flag, cli_runner):
        result = cli_runner.invoke(cli, [flag])
        assert result.exit_code == 0
        assert "v{}".format(VERSION) in result.output

    @pytest.mark.parametrize("flag", ["-h", "--help", None])
    def test_cli_prints_help(self, flag, cli_runner):
        flag = [flag] if flag is not None else None
        result = cli_runner.invoke(cli, flag)
        assert result.exit_code == 0
        assert "Usage" in result.output
        assert "Options" in result.output
        assert "apply" in result.output

    def test_command_not_found_no_suggestions(self, cli_runner):
        result = cli_runner.invoke(cli, ["excelsior"])
        assert result.exit_code == 1
        assert "excelsior' is not a vaild command" in result.output
        assert "pcf --help" in result.output

    def test_command_not_found_with_suggestions(self, cli_runner):
        result = cli_runner.invoke(cli, ["apple"])
        assert result.exit_code == 1
        assert "Did you mean" in result.output
        assert "apply" in result.output

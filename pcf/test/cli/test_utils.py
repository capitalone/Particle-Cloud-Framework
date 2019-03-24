""" Tests for the utility functions used by the PCF CLI """

import os
import pytest
from mock import patch
from pcf.cli.utils import *
from pcf.cli import commands
from pcf.cli.commands import apply, run, stop, terminate
from pcf.particle import aws
from pcf.particle.aws import ec2, s3, iam, cloudwatch
from pcf.particle.aws.ec2 import elb
from pcf.particle.aws.ec2.ec2_instance import EC2Instance
from pcf.quasiparticle.aws.ecs_instance_quasi.ecs_instance_quasi import ECSInstanceQuasi
from pcf.core.pcf_exceptions import MaxTimeoutException


class TestUtils:
    """ Test class for testing utility functions of the PCF CLI """

    @staticmethod
    def test_color():
        """ Ensure the color() function returns the color name or None if the NO_COLOR
            environment variable is set, repopulating a test-runner's
            NO_COLOR if present at test execution time
        """
        user_no_color = os.environ.get("NO_COLOR")

        os.environ["NO_COLOR"] = "AnyValueAccepted"
        assert color("red") == None

        del os.environ["NO_COLOR"]
        assert color("red") == "red"

        if user_no_color:
            os.environ["NO_COLOR"] = user_no_color

    @staticmethod
    def test_fail():
        """ Ensure the CLI exits with a non-zero code and prints the given message """
        with pytest.raises(SystemExit) as sys_exit:
            fail("foo")
            assert sys_exit.value.code == 1

    @staticmethod
    def test_similar_strings():
        """ Test similar string recommendation """
        assert similar_strings("foo", ["fo", "bar", "foobar"]) == ["fo"]
        assert similar_strings("lego", ["leggo", "my", "eggo"]) == ["leggo", "eggo"]
        assert similar_strings("abba", ["Yabba", "dabba", "do"]) == ["Yabba", "dabba"]

    @staticmethod
    def test_did_you_mean(capsys):
        """ Ensure proper grammar for 'Did you mean...' CLI suggestions """
        with pytest.raises(SystemExit) as sys_exit:
            did_you_mean(["single suggestion"])
            single_stdout, _ = capsys.readouterr()
            assert "Did you mean this?\n\tsingle suggestion" in single_stdout
            assert sys_exit.value.code == 1

        with pytest.raises(SystemExit) as sys_exit:
            did_you_mean(["more", "than", "one", "suggestion"], exit_code=42)
            multiple_stdout, _ = capsys.readouterr()
            assert "Did you mean one of these?" in multiple_stdout
            assert sys_exit.value.code == 42

    @staticmethod
    @pytest.mark.parametrize("filename", ["pcf.json", "pcf.yml", "pcf.yaml"])
    def test_load_pcf_config_from_file_default(
        filename, copy_pcf_config_file, cli_runner
    ):
        """ Ensure default PCF config files are found and loaded """
        with cli_runner.isolated_filesystem():
            copy_pcf_config_file(filename)
            pcf_config, pcf_filename = load_pcf_config_from_file(filename)
            assert isinstance(pcf_config, list)
            assert pcf_filename == filename

    @staticmethod
    @pytest.mark.parametrize("file1", ["pcf.json", "pcf.yml", "pcf.yaml"])
    @pytest.mark.parametrize("file2", ["pcf.json", "pcf.yml", "pcf.yaml"])
    def test_load_pcf_config_respects_default_precedence(
        file1, file2, copy_pcf_config_file, cli_runner, capsys
    ):
        """ Ensure default files are loaded in the right precedence if two+ exist """
        if file1 == file2:
            return
        else:
            if "pcf.json" in (file1, file2):
                expected = "pcf.json"
            elif "pcf.yml" in (file1, file2):
                expected = "pcf.yml"
            else:
                expected = "pcf.yaml"

            with cli_runner.isolated_filesystem():
                copy_pcf_config_file(file1)
                copy_pcf_config_file(file2)
                pcf_config, loaded_file = load_pcf_config_from_file("pcf.json")
                assert loaded_file == expected

    @staticmethod
    @pytest.mark.parametrize("filename", ["custom.json", "custom.yml", "custom.yaml"])
    def test_load_custom_pcf_files(filename, copy_pcf_config_file, cli_runner):
        """ Ensure valid pcf config files with custom names are loadable """
        with cli_runner.isolated_filesystem():
            copy_pcf_config_file(filename)
            pcf_config, pcf_filename = load_pcf_config_from_file(filename)
            assert isinstance(pcf_config, list)
            assert pcf_filename == filename

    @staticmethod
    def test_load_invalid_pcf_file_extension(capsys, cli_runner):
        """ Ensure an error is thrown when no valid file extension is found """
        with cli_runner.isolated_filesystem():
            with pytest.raises(SystemExit) as sys_exit:
                load_pcf_config_from_file("foo.bar")
                stdout = capsys.readouterr()
                assert sys_exit.value.code == 1
                assert "Error: foo.bar is not a valid PCF config file" in stdout

    @staticmethod
    def test_no_pcf_file_found(capsys, cli_runner):
        """ Ensure an error is thrown when no default file is found or the user has
            provided a config filename we can't find
        """
        with cli_runner.isolated_filesystem():
            with pytest.raises(SystemExit) as sys_exit:
                load_pcf_config_from_file("pcf.json")
                stdout, _ = capsys.readouterr()
                assert sys_exit.value.code == 1
                assert "Error: could not find a PCF config file." in stdout

            with pytest.raises(SystemExit) as sys_exit:
                load_pcf_config_from_file("custom.json")
                stdout, _ = capsys.readouterr()
                assert sys_exit.value.code == 1
                assert "Error: could not find PCF config file custom.json" in stdout

    @staticmethod
    @pytest.mark.parametrize("filename", ["pcf.json", "pcf.yml", "pcf.yaml"])
    def test_read_good_config_file(filename, copy_pcf_config_file, cli_runner):
        """ Ensures well-formed pcf configs are loaded from JSON/YAML files as lists """
        with cli_runner.isolated_filesystem():
            copy_pcf_config_file(filename)
            pcf_config, used_filename = read_config_file(filename)
            assert isinstance(pcf_config, list)
            assert "pcf_name" in pcf_config[0]
            assert used_filename == filename

    @staticmethod
    @pytest.mark.parametrize("filename", ["bad.json", "bad.yml", "bad.yaml"])
    def test_read_bad_config_file_exception(
        filename, copy_pcf_config_file, cli_runner, capsys
    ):
        """ Ensure error message shown for ill-formed pcf config files """
        with cli_runner.isolated_filesystem():
            copy_pcf_config_file(filename)

            with pytest.raises(SystemExit) as sys_exit:
                read_config_file(filename)
                stdout, _ = capsys.readouterr()
                assert sys_exit.value.code == 1
                assert "Error reading PCF config file" in stdout

    @staticmethod
    @pytest.mark.parametrize("filename", ["pcf.json", "pcf.yml", "pcf.yaml"])
    def test_particle_from_file(filename, copy_pcf_config_file, cli_runner):
        """ Ensure individual Particle/Quasiparticle configs are loaded from files
            given a pcf_name and filename to look in
        """
        with cli_runner.isolated_filesystem():
            copy_pcf_config_file(filename)
            particle_instance = particles_from_file("test_ec2", filename)[0]
            assert isinstance(particle_instance, EC2Instance)

    @staticmethod
    def test_particle_from_file_no_flavor(copy_pcf_config_file, cli_runner, capsys):
        """ Ensure an error is shown when a particle has no flavor specified """
        with cli_runner.isolated_filesystem():
            copy_pcf_config_file("pcf.yml")

            with pytest.raises(SystemExit) as sys_exit:
                particles_from_file("no_flavor_particle", "pcf.yml")
                stdout, _ = capsys.readouterr()
                assert sys_exit.value.code == 1
                assert "Error: No flavor specified in no_flavor_particle" in stdout

    @staticmethod
    def test_particle_from_file_unsupported_flavor(
        copy_pcf_config_file, cli_runner, capsys
    ):
        """ Ensure an error is shown when a particle specifies an unsupported flavor """
        with cli_runner.isolated_filesystem():
            copy_pcf_config_file("no_flavor.yml")

            with pytest.raises(SystemExit) as sys_exit:
                particles_from_file("unsupported_flavor_particle", "no_flavor.yml")
                stdout, _ = capsys.readouterr()
                assert sys_exit.value.code == 1
                assert "unsupported_flavor is not a supported" in stdout

    @staticmethod
    def test_particle_from_no_pcf_name(copy_pcf_config_file, cli_runner, capsys):
        """ Ensure an error is shown when a user passes a nonexistent pcf_name """
        with cli_runner.isolated_filesystem():
            copy_pcf_config_file("pcf.yml")

            with pytest.raises(SystemExit) as sys_exit:
                particles_from_file("unspecified", "pcf.yml")
                stdout, _ = capsys.readouterr()
                assert sys_exit.value.code == 1
                assert (
                    "could not find Particle or Quasiparticle 'unspecified'" in stdout
                )

    @staticmethod
    def test_particle_from_suggest_pcf_name(copy_pcf_config_file, cli_runner, capsys):
        """ Ensure similar pcf_names in config file are recommended for close typos """
        with cli_runner.isolated_filesystem():
            copy_pcf_config_file("pcf.yml")

            with pytest.raises(SystemExit) as sys_exit:
                particles_from_file("test_ec3", "pcf.yml")
                stdout, _ = capsys.readouterr()
                assert sys_exit.value.code == 1
                assert "could not find Particle or Quasiparticle 'test_ec3'" in stdout
                assert "Did you mean" in stdout
                assert "test_ec2" in stdout

    @staticmethod
    @patch.object(EC2Instance, "apply", return_value=None)
    @pytest.mark.parametrize("filename", ["pcf.json", "pcf.yml", "pcf.yaml"])
    @pytest.mark.parametrize("state", ["running", "stopped", "terminated"])
    def test_execute_applying_command(
        apply_mock, filename, state, cli_runner, copy_pcf_config_file, capsys
    ):
        """ Ensure the commands that call a Particle's apply() function will set the
            desired state and execute apply()
        """

        with cli_runner.isolated_filesystem():
            copy_pcf_config_file(filename)
            execute_applying_command("test_ec2", filename, state)
            stdout, _ = capsys.readouterr()
            expected = "Setting desired state of {0} to {1}".format("test_ec2", state)
            assert expected in stdout
            assert apply_mock.called

    @staticmethod
    @patch.object(EC2Instance, "apply", return_value=None)
    def test_execute_applying_command_quiet(
        apply_mock, cli_runner, copy_pcf_config_file, capsys
    ):
        """ Ensure no output when the quiet option is passed to apply execution
        """
        with cli_runner.isolated_filesystem():
            copy_pcf_config_file("pcf.json")
            execute_applying_command("test_ec2", "pcf.json", "running", quiet=True)
            stdout, _ = capsys.readouterr()
            assert "" == stdout
            assert apply_mock.called

    @staticmethod
    @patch.object(EC2Instance, "apply", side_effect=MaxTimeoutException())
    def test_execute_applying_command_timeout(
        apply_mock, cli_runner, copy_pcf_config_file, capsys
    ):
        """ Ensure errors thrown when max timeouts are reached """
        with cli_runner.isolated_filesystem():
            copy_pcf_config_file("pcf.json")

            with pytest.raises(SystemExit) as sys_exit:
                execute_applying_command(
                    "test_ec2", "pcf.json", "running", quiet=True, timeout=50
                )
                stdout, _ = capsys.readouterr()
                assert sys_exit.value.code == 1
                assert apply_mock.called
                assert "Error: Max timeout of 50 seconds reached" in stdout

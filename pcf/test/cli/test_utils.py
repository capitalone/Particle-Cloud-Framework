""" Tests for the utility functions used by the PCF CLI """

import pytest
from pcf.cli.utils import *

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
            os.environ['NO_COLOR'] = user_no_color

    @staticmethod
    def test_fail():
        """ Ensure the CLI exits with a non-zero code and prints the given message """
        with pytest.raises(SystemExit) as sys_exit:
            fail("foo")
        assert sys_exit.type == SystemExit
        assert sys_exit.value.code == 1

    @staticmethod
    def test_similar_strings():
        """ Test similar string recommendation """
        assert similar_strings("foo", ["fo", "bar", "foobar"]) == ["fo"]
        assert similar_strings("lego", ["leggo", "my", "eggo"]) == ["leggo", "eggo"]
        assert similar_strings("abba", ["Yabba", "dabba", "do"]) == ["Yabba", "dabba"]

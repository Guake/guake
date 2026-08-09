import re

import pytest

from guake.globals import QUICK_OPEN_MATCHERS
from guake.quick_open import build_quick_open_argv
from guake.quick_open import build_quick_open_command_line
from textwrap import dedent


def test_quick_open():
    chunk = dedent(
        """
        Traceback (most recent call last):
          File "./test.py", line 5, in <module>
              os.path('/bad/path')
          TypeError: 'module' object is not callable
        """
    )

    found = _execute_quick_open(chunk)
    assert found == [("./test.py", "5")]


def _execute_quick_open(chunk):
    found = []

    for line in chunk.split("\n"):
        for _1, _2, r in QUICK_OPEN_MATCHERS:
            g = re.compile(r).match(line)
            if g:
                found.append((g.group(1), g.group(2)))
    return found


def test_quick_open_command_keeps_filepath_as_one_argument():
    filepath = "/tmp/report; touch /tmp/quick-open-pwned"

    argv = build_quick_open_argv("gedit %(file_path)s:%(line_number)s", filepath, 12)

    assert argv == ["gedit", f"{filepath}:12"]


def test_quick_open_shell_command_quotes_filepath():
    filepath = "/tmp/report; touch /tmp/quick-open-pwned"

    command_line = build_quick_open_command_line("gedit %(file_path)s", filepath, None)

    assert command_line == "gedit '/tmp/report; touch /tmp/quick-open-pwned'"


def test_quick_open_command_rejects_empty_template():
    with pytest.raises(ValueError, match="empty"):
        build_quick_open_argv("", "/tmp/report", 1)


def test_quick_open_command_omits_zero_line_number():
    argv = build_quick_open_argv("editor %(file_path)s:%(line_number)s", "/tmp/report", 0)

    assert argv == ["editor", "/tmp/report:"]


def test_quick_open_command_rejects_unknown_placeholder():
    with pytest.raises(ValueError, match="Invalid"):
        build_quick_open_argv("editor %(unknown)s", "/tmp/report", 1)

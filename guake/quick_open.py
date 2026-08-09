"""Helpers for safely expanding and executing Quick Open commands."""

import shlex


def build_quick_open_argv(command_line, filepath, line_number):
    """Expand a Quick Open command template into an argument vector."""
    values = {
        "file_path": str(filepath),
        "line_number": "" if not line_number else str(line_number),
    }
    command = shlex.split(command_line)
    if not command:
        raise ValueError("Quick Open command is empty")
    try:
        return [argument % values for argument in command]
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Invalid Quick Open command template") from error


def build_quick_open_command_line(command_line, filepath, line_number):
    """Expand a Quick Open command template for execution in a terminal shell."""
    return shlex.join(build_quick_open_argv(command_line, filepath, line_number))

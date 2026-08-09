# -*- coding: utf-8; -*-

from guake import terminal


def test_build_terminal_environment_restores_original_language(mocker):
    mocker.patch.dict(
        terminal.os.environ,
        {"LANGUAGE": "uk:en", "GDK_BACKEND": "wayland", "TERM": "xterm"},
        clear=True,
    )
    mocker.patch.object(terminal, "ORIGINAL_LANGUAGE", "en_US.UTF-8")

    environment = terminal.build_terminal_environment()

    assert "LANGUAGE=en_US.UTF-8" in environment
    assert "GDK_BACKEND=wayland" not in environment
    assert "TERM=xterm" in environment


def test_build_terminal_environment_omits_language_when_original_was_unset(mocker):
    mocker.patch.dict(
        terminal.os.environ,
        {"LANGUAGE": "uk", "TERM": "xterm"},
        clear=True,
    )
    mocker.patch.object(terminal, "ORIGINAL_LANGUAGE", None)

    environment = terminal.build_terminal_environment()

    assert not any(value.startswith("LANGUAGE=") for value in environment)
    assert "TERM=xterm" in environment

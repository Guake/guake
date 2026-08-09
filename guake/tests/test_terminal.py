# -*- coding: utf-8; -*-

from types import SimpleNamespace

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


def test_kill_before_pid_marks_terminal_for_deferred_kill():
    terminal_instance = type("Terminal", (), {"pid": None, "_kill_requested": False})()

    terminal.GuakeTerminal.kill(terminal_instance)

    assert terminal_instance._kill_requested is True


def test_kill_with_pid_starts_shell_termination(mocker):
    terminal_instance = type(
        "Terminal",
        (),
        {"pid": 123, "delete_shell": mocker.Mock()},
    )()
    thread = mocker.patch("guake.terminal.threading.Thread")

    terminal.GuakeTerminal.kill(terminal_instance)

    thread.assert_called_once_with(target=terminal_instance.delete_shell, args=(123,))
    thread.return_value.start.assert_called_once_with()


def test_quick_open_logs_spawn_error_without_raising(mocker, caplog):
    settings = mocker.Mock()
    settings.general.get_string.return_value = "missing-editor %(file_path)s"
    settings.general.get_boolean.return_value = False
    terminal_instance = type("Terminal", (), {"guake": SimpleNamespace(settings=settings)})()
    mocker.patch("guake.terminal.subprocess.Popen", side_effect=OSError("not found"))

    terminal.GuakeTerminal._execute_quick_open(terminal_instance, "/tmp/file", 1)

    assert "Unable to execute Quick Open command" in caplog.text

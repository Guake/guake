import gconf
import gtk
import mock
import pytest

from guake.globals import KEY
from guake.prefs import PrefsDialog


@pytest.fixture
def prefs():
    obj = mock.Mock(PrefsDialog)
    obj.client = mock.Mock(gconf.Client)
    return obj


@pytest.fixture
def widget():
    obj = mock.Mock(gtk.Widget)
    obj.set_active = mock.Mock()
    obj.set_text = mock.Mock()
    return obj


def test__load_hooks_settings__works(prefs, widget):
    hook_show_command = "on_show.sh"
    prefs.client.get_string.return_value = hook_show_command
    prefs.get_widget.return_value = widget
    PrefsDialog._load_hooks_settings(prefs)
    prefs.client.get_string.assert_any_call(KEY("/hooks/show"))
    prefs.get_widget.assert_any_call("hook_show")
    widget.set_text.assert_called_once_with(hook_show_command)


def test__load_hooks_settings__no_widget(prefs):
    hook_show_command = "on_show.sh"
    prefs.client.get_string.return_value = hook_show_command
    prefs.get_widget.return_value = None
    PrefsDialog._load_hooks_settings(prefs)
    prefs.client.get_string.assert_any_call(KEY("/hooks/show"))
    prefs.get_widget.assert_any_call("hook_show")


def test__load_hooks_settings__no_setting(prefs, widget):
    prefs.client.get_string.return_value = None
    prefs.get_widget.return_value = widget
    PrefsDialog._load_hooks_settings(prefs)
    prefs.client.get_string.assert_any_call(KEY("/hooks/show"))
    prefs.get_widget.assert_any_call("hook_show")
    assert not widget.set_active.called


def test__load_hooks_settings__called(prefs):
    def se(key):
        """side effect for correctly mocking load_configs"""
        if key == KEY('/general/window_halignment'):
            return 0
        return None
    prefs.client.get_int.side_effect = se
    prefs.client.get_string.return_value = ''
    PrefsDialog.load_configs(prefs)
    assert prefs._load_hooks_settings.called
    assert prefs._load_default_shell_settings.called
    assert prefs._load_screen_settings.called

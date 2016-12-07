import pytest
import mock
import gtk
import gconf

from guake.prefs import PrefsDialog
from guake.globals import KEY

@pytest.fixture
def prefs():
    obj = mock.Mock(PrefsDialog)
    obj.client = mock.Mock(gconf.Client)
    return obj

@pytest.fixture
def widget():
    obj = mock.Mock(gtk.Widget)
    obj.set_active = mock.Mock()
    return obj


def test__load_hooks_settings__works(prefs, widget):
    hook_show_command = "on_show.sh"
    prefs.client.get_string.return_value = hook_show_command
    prefs.get_widget.return_value = widget
    PrefsDialog._load_hooks_settings(prefs)
    prefs.client.get_string.assert_any_call(KEY("/hooks/show"))
    prefs.get_widget.assert_any_call("hook_show")
    widget.set_active.assert_called_once_with(hook_show_command)

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

# def test__load_hooks_settings__called(prefs):
#     PrefsDialog.load_configs(prefs)
#     assert prefs._load_hooks_settings.called

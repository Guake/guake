import pytest
import mock
import subprocess
import gconf
import logging
import gtk
import time

from guake.guake_app import Guake
from guake import guake_app
from guake.globals import KEY

@pytest.fixture
def app():
    app = mock.Mock(Guake)
    app.client = mock.Mock(gconf.Client)
    app.notebook = mock.Mock()
    app.window = mock.Mock()
    app.selected_color = mock.Mock()
    app.is_fullscreen = mock.Mock()
    return app



def test__find_hook__works(app):
    hookname = 'hook.sh'
    app.client.get_string.return_value = hookname
    assert app.find_hook(app, 'show') == hookname
    app.client.get_string.assert_called_once_with(KEY("/hooks/show"))


@mock.patch("subprocess.Popen")
def test__execute_hook__works_correctly(popen_mckd):
    hookname = 'hook.sh -a'
    guake_mckd = mock.MagicMock(spec=Guake)
    guake_mckd.execute_hook = Guake.execute_hook
    guake_mckd.find_hook.return_value = hookname
    guake_mckd.execute_hook(guake_mckd, hookname)
    guake_mckd.find_hook.assert_called_once_with(hookname)
    popen_mckd.assert_called_once_with(hookname.split())


@mock.patch("subprocess.Popen")
def test__execute_hook__no_calls(popen_mckd):
    hookname = None
    guake_mckd = mock.MagicMock(spec=Guake)
    guake_mckd.execute_hook = Guake.execute_hook
    guake_mckd.find_hook.return_value = hookname
    guake_mckd.execute_hook(guake_mckd, hookname)
    guake_mckd.find_hook.assert_called_once_with(hookname)
    assert popen_mckd.call_count == 0

@mock.patch("gtk.gdk.x11_get_server_time")
def test__hook_show__called(x11_get_server_time, app):
    x11_get_server_time.return_value = time.time()
    Guake.show(app)
    app.execute_hook.assert_called_once_with("show")

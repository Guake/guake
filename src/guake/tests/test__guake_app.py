import pytest
import mock
import subprocess
import gconf
import logging

from guake.guake_app import Guake
from guake import guake_app

@mock.patch("gconf.Value")
def test__find_hook__works_correctly(value_mckd):
    hookname = 'hook.sh'
    guake_mckd = mock.MagicMock(spec=Guake)
    guake_mckd.find_hook = Guake.find_hook
    guake_mckd.client = mock.MagicMock(spec=gconf.Client)
    guake_mckd.client.get.return_value = value_mckd
    value_mckd.get_string.return_value = hookname
    hook = guake_mckd.find_hook(guake_mckd, 'show')
    guake_mckd.client.get.assert_called_once()
    value_mckd.get_string.assert_called_once()
    assert isinstance(hook, (str, unicode))
    assert hook == hookname

def test__find_hook__no_such_value():
    hookname = None
    guake_mckd = mock.MagicMock(spec=Guake)
    guake_mckd.find_hook = Guake.find_hook
    guake_mckd.client = mock.MagicMock(spec=gconf.Client)
    guake_mckd.client.get.return_value = hookname
    hook = guake_mckd.find_hook(guake_mckd, 'show')
    assert hook is None

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

# TODO: fix this test
# @mock.patch("guake_app.log")
# @mock.patch("subprocess.Popen")
# def test__execute_hook__handles_error(popen_mckd, log_mckd):
#     hookname = 'hook.sh'
#     guake_mckd = mock.MagicMock(spec=Guake)
#     guake_mckd.execute_hook = Guake.execute_hook
#     guake_mckd.find_hook.return_value = hookname
    
#     popen_mckd.side_effect = Exception("no way!")
#     guake_mckd.execute_hook(guake_mckd, hookname)
#     guake_mckd.find_hook.assert_called_once_with(hookname)
#     assert popen_mckd.call_count == 1
#     assert log_mckd.error.call_count == 1



def test__show__works_correctly():
    guake_mckd = mock.MagicMock(spec=Guake)
    guake_mckd.notebook = mock.MagicMock()
    guake_mckd.window = mock.MagicMock()
    guake_mckd.selected_color = mock.MagicMock()
    guake_mckd.is_fullscreen = mock.MagicMock()
    guake_mckd.client = mock.MagicMock()
    guake_mckd.show = Guake.show
    guake_mckd.show(guake_mckd)
    guake_mckd.execute_hook.assert_called_once_with("show")

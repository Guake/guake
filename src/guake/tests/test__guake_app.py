import pytest
import mock
import subprocess
import gconf
import logging

from guake.guake_app import Guake

def test__find_hook__works_correctly():
    hookname = 'hook.sh'
    guake_mckd = mock.MagicMock(spec=Guake)
    guake_mckd.find_hook = Guake.find_hook
    guake_mckd.client = mock.MagicMock(spec=gconf.Client)
    guake_mckd.client.get.return_value = hookname
    hook = guake_mckd.find_hook(guake_mckd, 'show')
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

@mock.patch("subprocess.call")
def test__execute_hook__works_correctly(subprocess_call):
    hookname = 'hook.sh -a'
    guake_mckd = mock.MagicMock(spec=Guake)
    guake_mckd.execute_hook = Guake.execute_hook
    guake_mckd.find_hook.return_value = hookname
    guake_mckd.execute_hook(guake_mckd, hookname)
    guake_mckd.find_hook.assert_called_once_with(hookname)
    subprocess_call.assert_called_once_with(hookname.split())


@mock.patch("subprocess.call")
def test__execute_hook__no_calls(subprocess_call):
    hookname = None
    guake_mckd = mock.MagicMock(spec=Guake)
    guake_mckd.execute_hook = Guake.execute_hook
    guake_mckd.find_hook.return_value = hookname
    guake_mckd.execute_hook(guake_mckd, hookname)
    guake_mckd.find_hook.assert_called_once_with(hookname)
    assert subprocess_call.call_count == 0

# TODO: fix this test
# @mock.patch("subprocess.call")
# def test__execute_hook__handles_error(subprocess_call):
#     hookname = 'hook.sh'
#     guake_mckd = mock.MagicMock(spec=Guake)
#     guake_mckd.execute_hook = Guake.execute_hook
#     guake_mckd.find_hook.return_value = hookname
    
#     subprocess_call.side_effect = Exception("no way!")
#     guake_mckd.execute_hook(guake_mckd, hookname)
#     guake_mckd.find_hook.assert_called_once_with(hookname)
#     assert subprocess_call.call_count == 1

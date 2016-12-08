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

# find_hook_fixtures = (
#     ("hook.sh", "hook.sh"),
#     (None, None),
# )

# @pytest.mark.parametrize("inputted, expected", find_hook_fixtures)
# def test__find_hook__works(inputted, expected, app):
#     app.client.get_string.return_value = inputted
#     assert Guake.find_hook(app, 'show') == expected
#     # app.client.get_string.assert_called_once_with(KEY("/hooks/show"))

execute_hook_fixtures = (
    ("show", "hook.sh arg1", ["hook.sh", "arg1"]),
    ("show", None, False,)
)


@pytest.mark.parametrize("event, cmd, expected", execute_hook_fixtures)
def test__execute_hook__works(event, cmd, expected, app):
    """
    execute_hook should exec command from setting /hook/<event> if it is string
    or do nothing if its NoneType
    """
    app.client.get_string.return_value = cmd
    with mock.patch("subprocess.Popen") as popen:
        Guake.execute_hook(app, event)
        if isinstance(cmd, (str, unicode)):
            popen.assert_called_once_with(expected)
        if cmd is None:
            assert popen.called == expected


def test__hook_show__called(app):
    Guake.show(app)
    app.execute_hook.assert_called_once_with("show")

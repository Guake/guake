import gconf
import mock
import pytest

from guake.guake_app import Guake


@pytest.fixture
def app():
    ap = mock.Mock(Guake)
    ap.client = mock.Mock(gconf.Client)
    ap.notebook = mock.Mock()
    ap.window = mock.Mock()
    ap.selected_color = mock.Mock()
    ap.is_fullscreen = mock.Mock()
    return ap

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

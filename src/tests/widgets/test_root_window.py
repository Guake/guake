import pytest
from unittest import mock
from guake.widgets.root_window import RootWindowMixin

@pytest.fixture
def root_window_mixin():
    mocked = mock.Mock(RootWindowMixin)
    return mocked

def test__prepare_to_draw__works(root_window_mixin):
    RootWindowMixin.prepare_to_draw(root_window_mixin)
    assert root_window_mixin._set_window_position.call_count == 1
    assert root_window_mixin._set_window_size.call_count == 1

def test___set_window_size__works():
    

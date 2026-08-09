# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name
import os

from types import SimpleNamespace

import pytest

from guake.utils import FileManager
from guake.utils import TabNameUtils
from guake.utils import get_process_name
from guake.utils import save_tabs_when_changed


def test_file_manager(fs):
    fs.create_file("/foo/bar", contents="test")
    fm = FileManager()
    assert fm.read("/foo/bar") == "test"


def test_file_manager_hit(fs):
    f = fs.create_file("/foo/bar", contents="test")

    fm = FileManager(delta=9999)
    assert fm.read("/foo/bar") == "test"
    f.set_contents("changed")
    assert fm.read("/foo/bar") == "test"


def test_file_manager_miss(fs):
    f = fs.create_file("/foo/bar", contents="test")

    fm = FileManager(delta=0.0)
    assert fm.read("/foo/bar") == "test"
    f.set_contents("changed")
    assert fm.read("/foo/bar") == "changed"


def test_file_manager_clear(fs):
    f = fs.create_file("/foo/bar", contents="test")

    fm = FileManager(delta=9999)
    assert fm.read("/foo/bar") == "test"
    f.set_contents("changed")
    assert fm.read("/foo/bar") == "test"
    fm.clear()
    assert fm.read("/foo/bar") == "changed"


def test_process_name():
    assert get_process_name(os.getpid())


def test_save_tabs_when_changed_schedules_save_for_guake_object(mocker):
    settings = SimpleNamespace(general=SimpleNamespace(get_boolean=lambda key: True))
    guake = SimpleNamespace(settings=settings, schedule_tabs_save=mocker.Mock())
    renamed = []

    class Target:
        def __init__(self):
            self.guake = guake
            self.renamed = renamed

        @save_tabs_when_changed
        def rename(self, value):
            result = value.upper()
            self.renamed.append(result)
            return result

    target = Target()
    assert target.rename("tab") == "TAB"

    assert renamed == ["TAB"]
    guake.schedule_tabs_save.assert_called_once_with()


@pytest.mark.parametrize(
    ("use_vte_titles", "max_name_length", "text", "expected"),
    [
        (False, 5, "terminal", "terminal"),
        (True, 0, "terminal", "terminal"),
        (True, 5, "terminal", "...minal"),
        (True, 20, "terminal", "terminal"),
    ],
)
def test_tab_name_shorten_respects_settings(
    mocker, use_vte_titles, max_name_length, text, expected
):
    settings = mocker.Mock()
    settings.general.get_boolean.return_value = use_vte_titles
    settings.general.get_int.return_value = max_name_length

    assert TabNameUtils.shorten(text, settings) == expected

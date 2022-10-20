# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name
import os

from guake.utils import FileManager
from guake.utils import get_process_name


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

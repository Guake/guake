# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name

import os
import pytest

from guake import guake_version
from guake.about import AboutDialog


@pytest.fixture
def dialog(mocker):
    mocker.patch('guake.simplegladeapp.Gtk.Widget.show_all')
    try:
        old_os_environ = os.environ
        os.environ["LANGUAGE"] = "en_US.UTF-8"
        ad = AboutDialog()
        yield ad
    finally:
        os.environ = old_os_environ


def test_version_test(dialog):
    assert dialog.get_widget('aboutdialog').get_version() == guake_version()


def test_title(dialog):
    assert dialog.get_widget('aboutdialog').get_title() == 'About Guake'

# -*- coding: utf-8 -*-

import pytest

from guake import guake_version
from guake.about import AboutDialog
from locale import gettext as _


@pytest.fixture
def dialog(mocker):
    mocker.patch('guake.simplegladeapp.Gtk.Widget.show_all')
    ad = AboutDialog()
    return ad


def test_version_test(dialog):
    assert dialog.get_widget('aboutdialog').get_version() == guake_version()


def test_title(dialog):
    assert dialog.get_widget('aboutdialog').get_title() == _('About Guake')

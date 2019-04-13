# -*- coding: utf-8 -*-

import pytest

from guake import guake_version
from guake.about import AboutDialog
from locale import gettext as _


class TestAboutDialog:

    @classmethod
    def setup_class(cls):
        cls.ad = AboutDialog()
        cls.dialog = cls.ad.get_widget('aboutdialog')

    @classmethod
    def teardown_class(cls):
        cls.dialog.destroy()

    @pytest.mark.dialog
    def test_version_text(self):
        assert self.dialog.get_version() == guake_version()

    @pytest.mark.dialog
    def test_title(self):
        assert self.dialog.get_title() == _('About Guake')

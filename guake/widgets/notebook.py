# -*- coding: utf-8; -*-
"""
Copyright (C) 2007-2013 Guake authors

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public
License along with this program; if not, write to the
Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
Boston, MA 02110-1301 USA
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

# pylint: disable=wrong-import-position,wrong-import-order,unused-import
from guake import gi
assert gi  # hack to "use" the import so pep8/pyflakes are happy

# from gi.repository import Gdk
from gi.repository import Gtk
# pylint: enable=wrong-import-position,wrong-import-order,unused-import
from guake.widgets.terminal import GuakeTerminal

logger = logging.getLogger(__name__)


class GuakeNotebook(Gtk.Notebook):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: choose from settings
        self.set_tab_pos(Gtk.PositionType.BOTTOM)
        self.new_page_button = self._get_new_page_button()
        self._add_new_page()

    def _add_new_page(self):
        pages_number = self.get_n_pages()
        position = 0 if pages_number < 2 else pages_number - 1
        self.insert_page(GuakeTerminal(), Gtk.Label("Terminal"), position)
        self.show_all()
        return

    def _get_new_page_button(self):
        button = Gtk.Button("+")
        self.append_page(Gtk.Frame(), button)
        button.connect("clicked", self.new_page_handler)
        return button

    def new_page_handler(self,  *args):
        self._add_new_page()

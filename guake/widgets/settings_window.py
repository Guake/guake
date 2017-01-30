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

from gi.repository import Gdk
from gi.repository import Gtk
# pylint: enable=wrong-import-position,wrong-import-order,unused-import

from guake.widgets.widget import GuakeWidget


logger = logging.getLogger(__name__)


class GuakeSettingsWindow(GuakeWidget, Gtk.Window):


    def __init__(self, gtkbuilder, *args, **kwargs):
        self.show_all()
        self.connect("delete_event", self.close_handler)


    def close_handler(self, *args):
        import ipdb; ipdb.set_trace()
        return self.hide() or True


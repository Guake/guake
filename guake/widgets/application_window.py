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

from guake.widgets.notebook import GuakeNotebook
# from guake.widgets.settings_window import GuakeSettingsWindow
from guake.widgets.widget import GuakeWidget


logger = logging.getLogger(__name__)


class GuakeApplicationWindow(GuakeWidget, Gtk.ApplicationWindow):

    _visible = False

    def __init__(self, gtkbuilder, *args, **kwargs):
        app = kwargs.get("application")
        if app is not None:
            self.set_application(app)
        self._set_window_position()
        self._set_window_size()
        self.gtkbuilder = gtkbuilder
        self.note = GuakeNotebook(gtkbuilder)
        self.resizer = gtkbuilder.get_object("GuakeResizer")
        self.resizer.connect("motion-notify-event", self.change_size_handler)
        self.connect("button-press-event", self.right_button_handler)
        self.visible = kwargs.get("visible", False)

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, value):
        self._visible = value
        if value:
            self._set_window_position()
            self.show_all()
            return
        self.hide()
        return

    def _select_screen(self):
        # TODO: get tagret screen from settings
        return Gdk.Screen.get_default()

    def _get_screen_size(self):
        screen = self._select_screen()
        return (screen.get_width(), screen.get_height())

    def _set_window_size(self):
        """
            - get window height from the settings
            - set window width as screen width
            - set window height

        """
        # TODO: read height_setting from settings
        height_rate = 0.6
        screen_width, screen_height = self._get_screen_size()
        self.set_default_size(screen_width, screen_height * height_rate)

    def _set_window_position(self):
        # TODO: get window position from settings
        self.move(0, 0)

    # handlers
    def show_hide_handler(self, *args):
        self.visible = not self.visible
        return

    def change_size_handler(self, widget, event):
        # got from
        # http://stackoverflow.com/questions/13638782/resize-borderless-window-with-vpaned-in-pythongtk3
        if Gdk.ModifierType.BUTTON1_MASK & event.get_state() != 0:
            _, _, mouse_y = event.device.get_position()
            _, root_y = self.get_position()
            new_height = mouse_y - root_y
            if new_height > 0:
                self.resize(self.get_allocation().width, new_height)
                self.show_all()

    def right_button_handler(self, widget, event):
        if not event.button == 3:
            return
        # settings_window = GuakeSettingsWindow(self.gtkbuilder)
        # import ipdb; ipdb.set_trace()

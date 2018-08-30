# -*- coding: utf-8; -*-
"""
Copyright (C) 2007-2012 Lincoln de Sousa <lincoln@minaslivre.org>
Copyright (C) 2007 Gabriel Falcão <gabrielteratos@gmail.com>

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
import datetime
import time

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GdkX11


def get_server_time(widget):
    try:
        return GdkX11.x11_get_server_time(widget.get_window())
    except (TypeError, AttributeError):
        # Issue: https://github.com/Guake/guake/issues/1071
        # Wayland does not seem to like `x11_get_server_time`.
        # Use local timestamp instead
        ts = time.time()
        return ts

class TabNameUtils():
    @classmethod
    def shorten(cls, text, settings):
        use_vte_titles = settings.general.get_boolean('use-vte-titles')
        if not use_vte_titles:
            return text
        max_name_length = settings.general.get_int("max-tab-name-length")
        if max_name_length != 0 and len(text) > max_name_length:
            text = "..." + text[-max_name_length:]
        return text

class FullscreenManager():

    def __init__(self, window):
        self.window = window
        self.is_in_fullscreen = False

    def is_fullscreen(self):
        return getattr(self.window, 'is_fullscreen', False)

    def fullscreen(self):
        self.window.fullscreen()
        setattr(self.window, 'is_fullscreen', True)

    def unfullscreen(self):
        # TODO do we still need this fix with gtk3?
        # Fixes "Guake cannot restore from fullscreen" (#628)
        self.window.unmaximize()
        self.window.unfullscreen()
        setattr(self.window, 'is_fullscreen', False)

    def toggle(self):
        if self.is_fullscreen():
            self.unfullscreen()
        else:
            self.fullscreen()

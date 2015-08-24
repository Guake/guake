#!/usr/bin/env python3
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

import os

from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Vte

from guake.dbus_manager import createDbusRemote
from guake.dconf_handler import DconfHandler
from guake.terminal import Terminal


class MyWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Hello World")

        terminal = Terminal()
        terminal.fork_command_full(
            Vte.PtyFlags.DEFAULT,
            os.environ['HOME'],
            ["/bin/bash"],
            [],
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None,
            None,
        )
        self.add(terminal)
        self.dconf_handler = DconfHandler()
        self.dconf_handler.registerSettingCallback("general",
                                                   "debug-mode",
                                                   "boolean",
                                                   self.on_debug_mode_changed)

    def on_debug_mode_changed(self, key, value):
        print("debug mode {} changed to {}".format(key, value))


def createGuake():
    win = MyWindow()
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    return win

remote_object = createDbusRemote(createGuake)
Gtk.main()

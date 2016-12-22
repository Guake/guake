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

# from guake.gi.repository import GLib
from guake.gi.repository import Gio
from guake.gi.repository import Gtk
from guake.logging import setupBasicLogging
from guake.logging import setupLogging


logger = logging.getLogger(__name__)


def guakeInit():
    setupBasicLogging()
    setupLogging()
    logger.info("Guake starts")


class GuakeApplication(Gtk.Application):

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            application_id="org.guake",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            **kwargs
        )
        self.builder = None
        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)

    def do_command_line(self, command_line):
        # options = command_line.get_options_dict()
        self.activate()
        return 0

    def do_activate(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("data/gtkobjects/app.ui")
        self.window = self.builder.get_object("window-root")
        self.window.present()
        Gtk.main()

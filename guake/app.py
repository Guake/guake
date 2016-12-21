from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from guake import gi
from gi.repository import GLib, Gio, Gtk

import logging
from guake.logging import setupBasicLogging, setupLogging


class GuakeApplication(Gtk.Application):

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            application_id="org.guake",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            **kwargs
        )

    def do_startup(self):
        Gtk.Application.do_startup(self)

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        self.activate()
        return 0

    def do_activate(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("data/gtkobjects/app.ui")
        self.window = self.builder.get_object("window-root")
        self.window.present()
        Gtk.main()

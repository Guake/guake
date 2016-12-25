from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import os
from time import sleep
from gi.repository import GLib
from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import Vte
from guake import gi

from guake.logging import setupBasicLogging
from guake.logging import setupLogging

from guake.terminal import GuakeTerminal

from guake.widgets.application_window import GuakeApplicationWindow

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
        self.window = GuakeApplicationWindow()
        self.window.set_application(self)
        self.window.prepare_to_draw()
        self.window.show_hide_handler()
        self.window.show_hide_handler()

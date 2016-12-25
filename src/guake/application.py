from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import os
from time import sleep
from guake import gi
from gi.repository import GLib
from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import Vte
from gi.repository import Keybinder

from guake.logging import setupBasicLogging
from guake.logging import setupLogging

from guake.terminal import GuakeTerminal

from guake.widgets.application_window import GuakeApplicationWindow

logger = logging.getLogger(__name__)


class GuakeApplication(Gtk.Application):

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            application_id="org.guake",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            **kwargs
        )
        self.add_main_option(
            "show",
            ord("s"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            "Show terminal on startup",
            None
        )
        # TODO: set this param from settings
        self.startup_visibility = False

    def do_startup(self):
        Gtk.Application.do_startup(self)

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        self.startup_visibility = True if options.contains("show") else False
        self.activate()
        return 0

    def do_activate(self):
        self.window = GuakeApplicationWindow(application=self, visible=self.startup_visibility)
        keystr = "F2"
        Keybinder.init()
        Keybinder.bind(keystr, self.window.show_hide_handler, "")

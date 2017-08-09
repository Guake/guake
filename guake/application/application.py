# -*- coding: utf-8; -*-
"""
Copyright (C) 2007-2017 Guake authors

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
import os


# from time import sleep

# pylint: disable=wrong-import-position,wrong-import-order,unused-import
from guake import gi

assert gi  # hack to "use" the import so pep8/pyflakes are happy

from gi.repository import GLib
from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import Keybinder
# pylint: enable=wrong-import-position,wrong-import-order,unused-import
from guake.application.keybindings import GuakeKeybindingsRepository
from guake.widgets.application_window import GuakeApplicationWindow
from guake.widgets.settings.settings_window import GuakeSettingsWindow
from guake.widgets.notebook import GuakeNotebook
from guake.widgets import GuakePopupMenu

logger = logging.getLogger(__name__)


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
        self.add_main_option(
            "show",
            ord("s"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            "Show terminal on startup",
            None
        )
        # TODO: set this param from settings
        self.show_on_start = False

    def do_startup(self):
        Gtk.Application.do_startup(self)
        Keybinder.init()
        self.keybinder = Keybinder
        self.keybindings = GuakeKeybindingsRepository(self)
        self.add_actions()
        self.add_keybindings(self.keybindings)

        datapath = "./data"
        appui = os.path.join(datapath, "ui", "app.ui")
        settingsui = os.path.join(datapath, "ui", "settings.ui")
        menusui = os.path.join(datapath, "ui", "menus.ui")
        self.builder = Gtk.Builder()
        self.builder.add_from_file(appui)
        self.builder.add_from_file(settingsui)
        self.builder.add_from_file(menusui)
        self.window = GuakeApplicationWindow(self.builder, application=self)
        self.settings_window = GuakeSettingsWindow(self.builder, application=self)
        self.notebook = GuakeNotebook(self.builder)
        self.main_menu = GuakePopupMenu(self.builder)
        self.builder.connect_signals(self)

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        self.show_on_start = options.contains("show")
        self.activate()
        return 0

    def do_activate(self):
        self.window.visible = self.show_on_start

    def add_actions(self):
        for action_dict in self.keybindings.application_actions:
            gio_action = Gio.SimpleAction.new(action_dict['key'], None)
            gio_action.connect("activate", getattr(self, action_dict['handler']))
            self.add_action(gio_action)

    def add_keybindings(self, giosettings, key=None):
        keys = [key] if key is not None else giosettings.keys()
        for key in keys:
            action_dict = giosettings.get_application_action(key)
            if action_dict is None:
                continue
            if action_dict.get('global', False):
                self.keybinder.bind(
                    self.keybindings.get_string(key),
                    getattr(self, action_dict['handler'])
                )
            else:
                self.add_accelerator(
                    self.keybindings.get_string(key),
                    'app.%s' % key,
                    None
                )
        return

    def change_keybinding_handler(self, giosettings, key):
        self.remove_accelerator('app.%s' % key, None)
        self.add_keybindings(giosettings, key)

    def new_page_handler(self, *args):
        self.notebook.new_page_handler()

    def close_page_handler(self, *args):
        self.notebook.close_page_handler()

    def show_hide_handler(self, *args, **kwargs):
        self.window.show_hide_handler(args, kwargs)

    def settings_handler(self, *args, **kwargs):
        self.settings_window.show_all()

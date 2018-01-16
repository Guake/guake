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
import logging

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio

log = logging.getLogger(__name__)


class Settings():

    def __init__(self, schema_source):
        Settings.enhanceSetting()

        self.guake = Gio.Settings.new_full(
            Gio.SettingsSchemaSource.lookup(schema_source, "guake", False), None, None
        )
        self.guake.initEnhancements()
        self.guake.connect("changed", self.guake.triggerOnChangedValue)

        self.general = Gio.Settings.new_full(
            Gio.SettingsSchemaSource.lookup(schema_source, "guake.general", False), None, None
        )
        self.general.initEnhancements()
        self.general.connect("changed", self.general.triggerOnChangedValue)

        self.keybindings = Gio.Settings.new_full(
            Gio.SettingsSchemaSource.lookup(schema_source, "guake.keybindings", False), None, None
        )
        self.keybindings.initEnhancements()
        self.keybindings.connect("changed", self.keybindings.triggerOnChangedValue)

        self.keybindingsGlobal = Gio.Settings.new_full(
            Gio.SettingsSchemaSource.lookup(schema_source, "guake.keybindings.global", False), None,
            None
        )
        self.keybindingsGlobal.initEnhancements()
        self.keybindingsGlobal.connect("changed", self.keybindingsGlobal.triggerOnChangedValue)

        self.keybindingsLocal = Gio.Settings.new_full(
            Gio.SettingsSchemaSource.lookup(schema_source, "guake.keybindings.local", False), None,
            None
        )
        self.keybindingsLocal.initEnhancements()
        self.keybindingsLocal.connect("changed", self.keybindingsLocal.triggerOnChangedValue)

        self.styleBackground = Gio.Settings.new_full(
            Gio.SettingsSchemaSource.lookup(schema_source, "guake.style.background", False), None,
            None
        )
        self.styleBackground.initEnhancements()
        self.styleBackground.connect("changed", self.styleBackground.triggerOnChangedValue)

        self.styleFont = Gio.Settings.new_full(
            Gio.SettingsSchemaSource.lookup(schema_source, "guake.style.font", False), None, None
        )
        self.styleFont.initEnhancements()
        self.styleFont.connect("changed", self.styleFont.triggerOnChangedValue)

        self.style = Gio.Settings.new_full(
            Gio.SettingsSchemaSource.lookup(schema_source, "guake.style", False), None, None
        )
        self.style.initEnhancements()
        self.style.connect("changed", self.style.triggerOnChangedValue)

        self.hooks = Gio.Settings.new_full(
            Gio.SettingsSchemaSource.lookup(schema_source, "guake.hooks", False), None, None
        )
        self.hooks.initEnhancements()
        self.hooks.connect("changed", self.hooks.triggerOnChangedValue)

    def enhanceSetting():

        def initEnhancements(self):
            self.listeners = dict()

        def onChangedValue(self, key, user_func):
            if key not in self.listeners:
                self.listeners[key] = list()
            self.listeners[key].append(user_func)

        def triggerOnChangedValue(self, settings, key, user_data=None):
            if key in self.listeners:
                for func in self.listeners[key]:
                    func(settings, key, user_data)

        gi.repository.Gio.Settings.initEnhancements = initEnhancements
        gi.repository.Gio.Settings.onChangedValue = onChangedValue
        gi.repository.Gio.Settings.triggerOnChangedValue = triggerOnChangedValue

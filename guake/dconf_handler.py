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

from gi.repository import Gio


class DconfHandler(object):
    GSETTINGS_NAMES = {
        "general",
        "shell",
        "appearance",
        "quick-open",
        "sessions",
        "keybindings",
        "custom-commands",
    }

    GSETTING_TYPE_TO_GET = {
        "boolean": "get_boolean",
    }
    GSETTING_TYPE_TO_SET = {
        "boolean": "set_boolean",
    }

    def __init__(self):
        # setup a check button and associate it with a GSettings key
        self.settings = {}
        for name in self.GSETTINGS_NAMES:
            self.settings[name] = Gio.Settings.new("guake.{0}".format(name))

    def registerCheckBoxHandler(self,
                                settingCategory,
                                settingName,
                                checkboxGtk):
        signal_name = "changed::{}".format(settingName)
        self.settings[settingCategory].connect(signal_name,
                                               self.onMySettingChanged,
                                               checkboxGtk)
        self.settings[settingCategory].setting.bind(settingName,
                                                    checkboxGtk,
                                                    "toggled",
                                                    Gio.SettingsBindFlags.DEFAULT)
        return self.settings[settingCategory].get_boolean(settingName)

    def onMySettingChanged(self, settings, key, checkboxGtk):
        checkboxGtk.set_active(settings.get_boolean(key))

    def onCheckButtonToggled(self, button, settingCategory, settingName):
        self.settings[settingCategory].set_boolean(settingName, button.get_active())

    def registerSettingCallback(self, settingCategory, settingName, settingType,
                                settingChangedCallback):
        self.settings[settingCategory].connect("changed::{}".format(settingName),
                                               self.onSettingChanged,
                                               settingType,
                                               settingChangedCallback)
        return getattr(self.settings[settingCategory],
                       self.GSETTING_TYPE_TO_GET[settingType])(settingName)

    def onSettingChanged(self, settings, key, settingType, settingChangedCallback):
        settingChangedCallback(key,
                               getattr(settings,
                                       self.GSETTING_TYPE_TO_GET[settingType])(key))

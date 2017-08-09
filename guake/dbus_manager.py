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

import dbus
import dbus.glib
import dbus.service


dbus.glib.threads_init()

DBUS_PATH = '/org/guake/RemoteControl'
DBUS_NAME = 'org.guakegt3.RemoteControl'


class DbusManager(dbus.service.Object):

    def __init__(self, guakeinstance):
        self.guake = guakeinstance
        self.bus = dbus.SessionBus()
        bus_name = dbus.service.BusName(DBUS_NAME, bus=self.bus)
        self.alreadyRunning = False
        super(DbusManager, self).__init__(bus_name, DBUS_PATH)

    @dbus.service.method(DBUS_NAME)
    def show_hide(self):
        self.guake.show_hide()

    @dbus.service.method(DBUS_NAME)
    def show(self):
        self.guake.show()
        self.guake.setTerminalFocus()

    @dbus.service.method(DBUS_NAME)
    def showFromRemote(self):
        self.guake.showFromRemote()
        self.guake.setTerminalFocus()

    @dbus.service.method(DBUS_NAME)
    def hide(self):
        self.guake.hide()

    @dbus.service.method(DBUS_NAME)
    def hideFromRemote(self):
        self.guake.hideFromRemote()

    @dbus.service.method(DBUS_NAME)
    def fullscreen(self):
        self.guake.fullscreen()

    @dbus.service.method(DBUS_NAME, in_signature='s')
    def addTab(self, directory=''):
        self.guake.addTab(directory)

    @dbus.service.method(DBUS_NAME, in_signature='i')
    def selectTab(self, tabIndex=0):
        return self.guake.selectTab(int(tabIndex))

    @dbus.service.method(DBUS_NAME, out_signature='i')
    def getSelectedTab(self):
        return self.guake.getSelectedTab()

    @dbus.service.method(DBUS_NAME, out_signature='i')
    def getTabCount(self):
        return len(self.guake.notebook.term_list)

    @dbus.service.method(DBUS_NAME, in_signature='s')
    def setBgcolor(self, bgcolor):
        self.guake.setBgcolor(bgcolor)

    @dbus.service.method(DBUS_NAME, in_signature='s')
    def setFgcolor(self, fgcolor):
        self.guake.setFgcolor(fgcolor)

    @dbus.service.method(DBUS_NAME, in_signature='s')
    def executeCommand(self, command):
        self.guake.executeCommand(command)

    @dbus.service.method(DBUS_NAME, in_signature='i', out_signature='s')
    def getTabName(self, tabIndex=0):
        return self.guake.notebook.term_list[int(tabIndex)].get_window_title() or ''

    @dbus.service.method(DBUS_NAME, in_signature='is')
    def renameTab(self, tabIndex, newText):
        self.guake.renameTab(tabIndex, newText)

    @dbus.service.method(DBUS_NAME, in_signature='s')
    def renameCurrentTab(self, newText):
        self.guake.renameCurrentTab(newText)

    @dbus.service.method(DBUS_NAME)
    def showAbout(self):
        self.guake.showAbout()

    @dbus.service.method(DBUS_NAME)
    def showPrefs(self):
        self.guake.showPrefs()

    @dbus.service.method(DBUS_NAME)
    def quit(self):
        self.guake.quit()

    @dbus.service.method(DBUS_NAME, in_signature='i', out_signature='s')
    def get_gtktab_name(self, tabIndex=0):
        return self.guake.tabs.getChildren()[tabIndex].get_label()


def createDbusRemote(instanceCreator):
    # Trying to get an already running instance of guake. If it is not
    # possible, lets create a new instance. This function will return
    # a boolean value depending on this decision.
    print("heho")
    try:
        bus = dbus.SessionBus()
        remote_object = bus.get_object(DBUS_NAME, DBUS_PATH)
        remote_object.alreadyRunning = True
    except dbus.DBusException:
        print("creating instance")
        instance = instanceCreator()
        remote_object = DbusManager(instance)
        remote_object.alreadyRunning = False
    return remote_object

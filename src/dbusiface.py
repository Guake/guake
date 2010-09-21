# -*- coding: utf-8; -*-
"""
Copyright (C) 2007-2009 Lincoln de Sousa <lincoln@minaslivre.org>
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
Free Software Foundation, Inc., 59 Temple Place - Suite 330,
Boston, MA 02111-1307, USA.
"""
import dbus
import dbus.service
import dbus.glib
import gtk
import guake.common
dbus.glib.threads_init()

DBUS_PATH = '/org/guake/RemoteControl'
DBUS_NAME = 'org.guake.RemoteControl'

class DbusManager(dbus.service.Object):
    def __init__(self, guakeinstance):
        self.guake = guakeinstance
        self.bus = dbus.SessionBus()
        bus_name = dbus.service.BusName(DBUS_NAME, bus=self.bus)
        super(DbusManager, self).__init__(bus_name, DBUS_PATH)

    @dbus.service.method(DBUS_NAME)
    def show_hide(self):
        self.guake.show_hide()

    @dbus.service.method(DBUS_NAME, in_signature='s')
    def add_tab(self, directory=''):
        self.guake.add_tab(directory)

    @dbus.service.method(DBUS_NAME, in_signature='i')
    def select_tab(self, tab_index=0):
        self.guake.select_tab(int(tab_index))

    @dbus.service.method(DBUS_NAME, out_signature='i')
    def get_selected_tab(self):
        return self.guake.get_selected_tab()

    @dbus.service.method(DBUS_NAME, in_signature='s')
    def execute_command(self, command):
        self.guake.execute_command(command)

    @dbus.service.method(DBUS_NAME, in_signature='s')
    def rename_current_tab(self, new_text):
        self.guake.rename_current_tab(new_text)

    @dbus.service.method(DBUS_NAME)
    def show_about(self):
        self.guake.show_about()

    @dbus.service.method(DBUS_NAME)
    def show_prefs(self):
        self.guake.show_prefs()

    @dbus.service.method(DBUS_NAME)
    def quit(self):
        self.guake.quit()

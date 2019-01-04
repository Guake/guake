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

import logging

import dbus
import dbus.glib
import dbus.service

log = logging.getLogger(__name__)

dbus.glib.threads_init()

DBUS_PATH = '/org/guake3/RemoteControl'
DBUS_NAME = 'org.guake3.RemoteControl'


class DbusManager(dbus.service.Object):

    def __init__(self, guakeinstance):
        self.guake = guakeinstance
        self.bus = dbus.SessionBus()
        bus_name = dbus.service.BusName(DBUS_NAME, bus=self.bus)
        super(DbusManager, self).__init__(bus_name, DBUS_PATH)

    @dbus.service.method(DBUS_NAME)
    def show_hide(self):
        self.guake.show_hide()

    @dbus.service.method(DBUS_NAME)
    def show(self):
        self.guake.show()
        self.guake.set_terminal_focus()

    @dbus.service.method(DBUS_NAME)
    def show_from_remote(self):
        self.guake.show_from_remote()
        self.guake.set_terminal_focus()

    @dbus.service.method(DBUS_NAME)
    def hide(self):
        self.guake.hide()

    @dbus.service.method(DBUS_NAME)
    def hide_from_remote(self):
        self.guake.hide_from_remote()

    @dbus.service.method(DBUS_NAME)
    def fullscreen(self):
        self.guake.fullscreen()

    @dbus.service.method(DBUS_NAME, in_signature='s')
    def add_tab(self, directory=''):
        return self.guake.add_tab(directory)

    @dbus.service.method(DBUS_NAME, in_signature='i')
    def select_tab(self, tab_index=0):
        return self.guake.get_notebook().set_current_page(int(tab_index))

    @dbus.service.method(DBUS_NAME, out_signature='i')
    def get_selected_tab(self):
        return self.guake.get_notebook().get_current_page()

    @dbus.service.method(DBUS_NAME, out_signature='s')
    def get_selected_tablabel(self):
        return self.guake.get_notebook(
        ).get_tab_text_index(self.guake.get_notebook().get_current_page())

    @dbus.service.method(DBUS_NAME, out_signature='i')
    def get_tab_count(self):
        return len(self.guake.notebook_manager.get_terminals())

    @dbus.service.method(DBUS_NAME, in_signature='s')
    def set_bgcolor(self, bgcolor):
        return self.guake.set_bgcolor(bgcolor)

    @dbus.service.method(DBUS_NAME, in_signature='s')
    def set_fgcolor(self, fgcolor):
        return self.guake.set_fgcolor(fgcolor)

    @dbus.service.method(DBUS_NAME, in_signature='s')
    def change_palette_name(self, palette_name):
        self.guake.change_palette_name(palette_name)

    @dbus.service.method(DBUS_NAME, in_signature='s')
    def execute_command(self, command):
        self.guake.execute_command(command)

    @dbus.service.method(DBUS_NAME, in_signature='i', out_signature='s')
    def get_tab_name(self, tab_index=0):
        return self.guake.get_notebook().get_tab_text_index(tab_index)

    @dbus.service.method(DBUS_NAME, in_signature='ss')
    def rename_tab_uuid(self, tab_uuid, new_text):
        self.guake.rename_tab_uuid(tab_uuid, new_text, True)

    @dbus.service.method(DBUS_NAME, in_signature='is')
    def rename_tab(self, tab_index, new_text):
        self.guake.get_notebook().rename_page(tab_index, new_text, True)

    @dbus.service.method(DBUS_NAME, in_signature='s')
    def rename_current_tab(self, new_text):
        self.guake.rename_current_tab(new_text, True)

    @dbus.service.method(DBUS_NAME)
    def show_about(self):
        self.guake.show_about()

    @dbus.service.method(DBUS_NAME)
    def show_prefs(self):
        self.guake.show_prefs()

    @dbus.service.method(DBUS_NAME)
    def quit(self):
        self.guake.quit()

    @dbus.service.method(DBUS_NAME, in_signature='i', out_signature='s')
    def get_gtktab_name(self, tab_index=0):
        return self.guake.get_notebook().get_tab_text_index(tab_index)

    @dbus.service.method(DBUS_NAME, out_signature='s')
    def get_selected_uuidtab(self):
        return self.guake.get_selected_uuidtab()

    @dbus.service.method(DBUS_NAME, in_signature='ss')
    def execute_command_by_uuid(self, tab_uuid, command):
        self.guake.execute_command_by_uuid(tab_uuid, command)

    @dbus.service.method(DBUS_NAME)
    def v_split_current_terminal(self):
        self.guake.get_notebook().get_current_terminal().get_parent().split_v()

    @dbus.service.method(DBUS_NAME)
    def h_split_current_terminal(self):
        self.guake.get_notebook().get_current_terminal().get_parent().split_h()

    @dbus.service.method(DBUS_NAME, in_signature='s')
    def execute_command_current_termbox(self, command):
        self.guake.get_notebook().get_current_terminal().execute_command(command)

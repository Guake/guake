# -*- coding: utf-8; -*-
"""
Copyright (C) 2007 Gabriel Falcão <gabrielteratos@gmail.com>
Copyright (C) 2007 Lincoln de Sousa <lincoln@archlinux-br.org>

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
import common
dbus.glib.threads_init()


class DaemonDBus(dbus.service.Object):
    def __init__(self, bus_name, guakeinstance):
        self.guake = guakeinstance
        object_path = '/DBusInterface'
        super(DaemonDBus, self).__init__(bus_name, object_path)

    @dbus.service.method('org.gnome.Guake.DBusInterface')
    def show_hide(self):
        self.guake.show_hide()

    @dbus.service.method('org.gnome.Guake.DBusInterface')
    def add_tab(self):
        self.guake.add_tab()

    @dbus.service.method('org.gnome.Guake.DBusInterface')
    def show_about(self):
        self.guake.show_about()

    @dbus.service.method('org.gnome.Guake.DBusInterface')
    def show_prefs(self):
        self.guake.show_prefs()

    @dbus.service.method('org.gnome.Guake.DBusInterface')
    def quit(self):
        self.guake.quit()


def dbus_init(guakeinstance):
    try:
        session_bus = dbus.SessionBus()
        name = dbus.service.BusName('org.gnome.Guake.DBus', bus=session_bus)
        return DaemonDBus(name, guakeinstance)
    except dbus.DBusException:
        import sys
        sys.stderr.write(_('Could not connect to dbus session bus.'
            ' dbus will be unavailable.\n'))
        return None

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
import gtk
import gconf
import sys
import os
import locale
import gettext
import time
import guake_globals

# Internationalization purposes.
_ = gettext.gettext

__all__ = ['_', 'ShowableError', 'test_dbus', 'test_gconf',
           'pixmapfile', 'gladefile', 'hexify_color']

class ShowableError(Exception):
    def __init__(self, title, msg, exit_code=1):
        d = gtk.MessageDialog(type=gtk.MESSAGE_ERROR,
                buttons=gtk.BUTTONS_CLOSE)
        d.set_markup('<b><big>%s</big></b>' % title)
        d.format_secondary_markup(msg)
        d.run()
        d.destroy()
        if exit_code != -1:
            sys.exit(exit_code)

def test_dbus(bus, interface):
    obj = bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
    dbus_iface = dbus.Interface(obj, 'org.freedesktop.DBus')
    avail = dbus_iface.ListNames()
    return interface in avail

def test_gconf():
    c = gconf.client_get_default()
    return c.dir_exists('/apps/guake')

def pixmapfile(x):
    f = os.path.join(guake_globals.image_dir, x)
    if not os.path.exists(f):
        raise IOError('No such file or directory: %s' % f)
    return os.path.abspath(f)

def gladefile(x):
    f = os.path.join(guake_globals.glade_dir, x)
    if not os.path.exists(f):
        raise IOError('No such file or directory: %s' % f)
    return os.path.abspath(f)

def hexify_color(c):
    h = lambda x: hex(x).replace('0x', '').zfill(4)
    return '#%s%s%s' % (h(c.red), h(c.green), h(c.blue))

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


def guake_version():
    # Do not import in the module root to speed up the dbus communication as much as possible
    import pbr.version
    return pbr.version.VersionInfo('guake').version_string()


def vte_version():
    import gi
    gi.require_version('Vte', '2.91')

    from gi.repository import Vte
    s = "{}.{}.{}".format(
        Vte.MAJOR_VERSION,
        Vte.MINOR_VERSION,
        Vte.MICRO_VERSION,
    )
    return s


def vte_runtime_version():
    import gi
    gi.require_version('Vte', '2.91')

    from gi.repository import Vte
    return "{}.{}.{}".format(
        Vte.get_major_version(), Vte.get_minor_version(), Vte.get_micro_version()
    )


def gtk_version():
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    return "{}.{}.{}".format(Gtk.MAJOR_VERSION, Gtk.MINOR_VERSION, Gtk.MICRO_VERSION)

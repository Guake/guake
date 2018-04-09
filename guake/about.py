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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject
from gi.repository import Gtk

from guake import guake_version
from guake.common import gladefile
from guake.common import pixmapfile
from guake.simplegladeapp import SimpleGladeApp
from locale import gettext as _


class AboutDialog(SimpleGladeApp):

    """The About Guake dialog class
    """

    def __init__(self):
        super(AboutDialog, self).__init__(gladefile('about.glade'), root='aboutdialog')
        dialog = self.get_widget('aboutdialog')

        # images
        # ipath = pixmapfile('guake-notification.png')
        # img = gtk.gdk.pixbuf_new_from_file(ipath)

        # img = pixmapfile('guake-notification.png')
        image = Gtk.Image()
        image.set_from_file(pixmapfile('guake-notification.png'))
        pixbuf = image.get_pixbuf()

        dialog.set_property('logo', pixbuf)

        dialog.set_name(_('Guake Terminal'))
        dialog.set_version(guake_version())
        dialog.connect("response", lambda x, y: dialog.destroy())

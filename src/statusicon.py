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
import common
from common import _


class NoStatusIconAvailable(Exception):
    """
    Exception raised when there isn't an available way to
    put this on the tray.
    """
    pass


class GuakeStatusIcon(object):
    """
    Pygtk>=2.10 already includes C{gtk.StatusIcon}, so we wrotte this code to
    make this program available to systems that has older versions (but it must
    has C{egg} extension!)

    Factory that tries to find an available backend to put the program on the
    tray, At this moment only C{egg.trayicon} and C{gtk.StatusIcon} are
    available, but I think no other is needed...

    This proviedes an interface to use all supported widgets, as in the
    following example:

        >>> def callback(*args):
        ...     print args
        >>>
        >>> icon = GuakeStatusIconFactory(imgpath)
        >>> icon.connect('popup-menu', callback)
        >>> icon.connect('activate', callback)
        >>> icon.show() # after a gtk.main() this goes directly to the tray!

    TODO: This class should inherit from GObject to improve the signal handling
    and etc...
    """
    def __init__(self):

        self.icon = None
        self.style = None

        img = common.pixmapfile('statusicon_out.png')
        tooltip = _('Guake-Terminal')
        try:
            self.icon = gtk.status_icon_new_from_file(img)
            self.icon.set_tooltip(tooltip)
            self.style = 'gtk'
        except AttributeError:
            pass

        if self.icon is None:
            try:
                from egg.trayicon import TrayIcon
                tooltips = gtk.Tooltips()
                self.evtbox = gtk.EventBox()
                imgwidget = gtk.Image()
                tooltips.set_tip(self.evtbox, tooltip)
                imgwidget.set_from_file(img)
                self.evtbox.add(imgwidget)
                self.icon = TrayIcon('GuakeRox!')
                self.icon.add(self.evtbox)
                self.style = 'egg'
            except ImportError:
                pass

        if self.icon is None:
            raise NoStatusIconAvailable

    def get_widget(self):
        return self.icon

    def show(self):
        if hasattr(self.icon, 'show'):
            self.icon.show()

    def show_all(self):
        if hasattr(self.icon, 'show_all'):
            self.icon.show_all()
        else:
            self.show()

    def connect(self, signal, callback, user_data=None):
        # TODO: hammer a lot!
        if signal == 'popup-menu':
            if self.style == 'gtk':
                self.icon.connect(signal, callback, user_data)
            else:
                self.evtbox.connect('button-press-event', callback, user_data)

        elif signal == 'activate':
            if self.style == 'gtk':
                self.icon.connect(signal, callback, user_data)
            else:
                self.evtbox.connect('button-press-event', callback, user_data)

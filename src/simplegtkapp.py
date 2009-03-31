"""
Copyright (C) 2009 Aleksandar Krsteski <alekrsteski@gmail.com>

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

import pygtk
pygtk.require('2.0')

import gtk

class SimpleGtkApp(object):
    """
    Basic GtkBuilder wrapper that implements the functions from
    simplegladeapp.py used by Guake with the purpose to minimize
    the changes required in Guake while porting it to GtkBuilder.
    """
    def __init__(self, path, callbacks_proxy=None):
        """
        Load a GtkBuilder ui definition file specified by path.
        If callbacks_proxy is specified it will be used as object to
        to connect the signals, otherwise self will be used.
        """        
        self.builder = gtk.Builder()
        self.builder.add_from_file(path)
        if callbacks_proxy:
            self.builder.connect_signals(callbacks_proxy)
        else:
            self.builder.connect_signals(self)

    def quit(self):
        """
        Quit processing of gtk events.
        """
        gtk.main_quit()

    def run(self):
        """
        Starts the main gtk loop.
        """
        gtk.main()

    def get_widget(self, name):
        """
        Returns the unterface widget specified by the name.
        """
        return self.builder.get_object(name)

    def get_widgets(self):
        """
        Returns all the interface widgets.
        """
        return self.builder.get_objects()

    # -- predefined callbacks --
    
    def gtk_main_quit(self, *args):
        """
        Calls self.quit()
        """
        self.quit()

    def gtk_widget_destroy(self, widget, *args):
        """
        Destroyes the widget.
        """
        widget.destroy()

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

from gi.repository import Gtk


def bindtextdomain(app_name, locale_dir=None):
    """
    Bind the domain represented by app_name to the locale directory locale_dir.
    It has the effect of loading translations, enabling applications for different
    languages.

    app_name:
        a domain to look for translations, typically the name of an application.

    locale_dir:
        a directory with locales like locale_dir/lang_isocode/LC_MESSAGES/app_name.mo
        If omitted or None, then the current binding for app_name is used.
    """
    try:
        import locale
        import gettext
        # FIXME: Commented to avoid problems with a .utf8 LANG variable...
        # locale.setlocale(locale.LC_ALL, "")
        gettext.bindtextdomain(app_name, locale_dir)
        gettext.textdomain(app_name)
        gettext.install(app_name, locale_dir, unicode=1)
    except (IOError, locale.Error) as e:
        print("Warning", app_name, e)
        __builtins__.__dict__["_"] = lambda x: x


class SimpleGtk3App(object):

    """
    Basic GtkBuilder wrapper that implements the functions from
    simplegladeapp.py used by Guake with the purpose to minimize
    the changes required in Guake while porting it to GtkBuilder.
    """

    def __init__(self, path):
        """
        Load a GtkBuilder ui definition file specified by path.
        Self will be used as object to to connect the signals.
        """
        self.builder = Gtk.Builder()
        self.builder.add_from_file(path)
        self.builder.connect_signals(self)

    def quit(self):
        """
        Quit processing of gtk events.
        """
        Gtk.main_quit()

    def run(self):
        """
        Starts the main gtk loop.
        """
        Gtk.main()

    def get_widget(self, name):
        """
        Returns the interface widget specified by the name.
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

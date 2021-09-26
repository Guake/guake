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
import os
import re
import sys

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import tokenize


class SimpleGladeApp:
    def __init__(self, path, root=None, domain=None):
        """
        Load a glade file specified by glade_filename, using root as
        root widget and domain as the domain for translations.

        If it receives extra named arguments (argname=value), then they are used
        as attributes of the instance.

        path:
            path to a glade filename.
            If glade_filename cannot be found, then it will be searched in the
            same directory of the program (sys.argv[0])

        root:
            the name of the widget that is the root of the user interface,
            usually a window or dialog (a top level widget).
            If None or ommited, the full user interface is loaded.

        domain:
            A domain to use for loading translations.
            If None or ommited, no translation is loaded.
        """
        if os.path.isfile(path):
            self.glade_path = path
        else:
            glade_dir = os.path.dirname(sys.argv[0])
            self.glade_path = os.path.join(glade_dir, path)

        self.glade = None

        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.glade_path)

        if root:
            self.main_widget = self.builder.get_object(root)
            self.main_widget.show_all()
        else:
            self.main_widget = None

        # self.glade = self.create_glade(self.glade_path, root, domain)

        self.normalize_names()
        # Widgets are loaded and can be refered as self.widget_name

    def __repr__(self):
        class_name = self.__class__.__name__
        if self.main_widget:
            root = Gtk.Widget.get_name(self.main_widget)
            return f'{class_name}(path="{self.glade_path}", root="{root}")'
        return f'{class_name}(path="{self.glade_path}")'

    def add_callbacks(self, callbacks_proxy):
        """
        It uses the methods of callbacks_proxy as callbacks.
        The callbacks are specified by using:
            Properties window -> Signals tab
            in glade-2 (or any other gui designer like gazpacho).

        Methods of classes inheriting from SimpleGladeApp are used as
        callbacks automatically.

        callbacks_proxy:
            an instance with methods as code of callbacks.
            It means it has methods like on_button1_clicked, on_entry1_activate, etc.
        """
        self.builder.connect_signals(callbacks_proxy)

    def normalize_names(self):
        """
        It is internally used to normalize the name of the widgets.
        It means a widget named foo:vbox-dialog in glade
        is refered self.vbox_dialog in the code.

        It also sets a data "prefixes" with the list of
        prefixes a widget has for each widget.
        """
        for widget in self.get_widgets():
            if isinstance(widget, Gtk.Buildable):
                widget_name = Gtk.Buildable.get_name(widget)
                prefixes_name_l = widget_name.split(":")
                prefixes = prefixes_name_l[:-1]
                widget_api_name = prefixes_name_l[-1]
                widget_api_name = "_".join(re.findall(tokenize.Name, widget_api_name))
                widget_name = Gtk.Buildable.set_name(widget, widget_api_name)
                if hasattr(self, widget_api_name):
                    raise AttributeError(
                        f"instance {self} already has an attribute {widget_api_name}"
                    )
                setattr(self, widget_api_name, widget)
                if prefixes:
                    # TODO is is a guess
                    Gtk.Buildable.set_data(widget, "prefixes", prefixes)

    def custom_handler(self, glade, function_name, widget_name, str1, str2, int1, int2):
        """
        Generic handler for creating custom widgets, internally used to
        enable custom widgets (custom widgets of glade).

        The custom widgets have a creation function specified in design time.
        Those creation functions are always called with str1,str2,int1,int2 as
        arguments, that are values specified in design time.

        Methods of classes inheriting from SimpleGladeApp are used as
        creation functions automatically.

        If a custom widget has create_foo as creation function, then the
        method named create_foo is called with str1,str2,int1,int2 as arguments.
        """
        try:
            handler = getattr(self, function_name)
            return handler(str1, str2, int1, int2)
        except AttributeError:
            return None

    def gtk_widget_show(self, widget, *args):
        """
        Predefined callback.
        The widget is showed.
        Equivalent to widget.show()
        """
        widget.show()

    def gtk_widget_hide(self, widget, *args):
        """
        Predefined callback.
        The widget is hidden.
        Equivalent to widget.hide()
        """
        widget.hide()
        return True

    def gtk_widget_grab_focus(self, widget, *args):
        """
        Predefined callback.
        The widget grabs the focus.
        Equivalent to widget.grab_focus()
        """
        widget.grab_focus()

    def gtk_widget_destroy(self, widget, *args):
        """
        Predefined callback.
        The widget is destroyed.
        Equivalent to widget.destroy()
        """
        widget.destroy()

    def gtk_window_activate_default(self, widget, *args):
        """
        Predefined callback.
        The default widget of the window is activated.
        Equivalent to window.activate_default()
        """
        widget.activate_default()

    def gtk_true(self, *args):
        """
        Predefined callback.
        Equivalent to return True in a callback.
        Useful for stopping propagation of signals.
        """
        return True

    def gtk_false(self, *args):
        """
        Predefined callback.
        Equivalent to return False in a callback.
        """
        return False

    def gtk_main_quit(self, *args):
        """
        Predefined callback.
        Equivalent to self.quit()
        """
        self.quit()

    def main(self):
        """
        Starts the main loop of processing events.
        The default implementation calls gtk.main()

        Useful for applications that needs a non gtk main loop.
        For example, applications based on gstreamer needs to override
        this method with gst.main()

        Do not directly call this method in your programs.
        Use the method run() instead.
        """
        Gtk.main()

    def quit(self, *args):
        """
        Quit processing events.
        The default implementation calls gtk.main_quit()

        Useful for applications that needs a non gtk main loop.
        For example, applications based on gstreamer needs to override
        this method with gst.main_quit()
        """
        Gtk.main_quit()

    def run(self):
        """
        Starts the main loop of processing events checking for Control-C.

        The default implementation checks wheter a Control-C is pressed,
        then calls on_keyboard_interrupt().

        Use this method for starting programs.
        """
        try:
            self.main()
        except KeyboardInterrupt:
            sys.exit()

    def get_widget(self, widget_name):
        return self.builder.get_object(widget_name)

    def get_widgets(self):
        return self.builder.get_objects()

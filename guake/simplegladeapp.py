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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import tokenize


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
        gettext.install(app_name, locale_dir)
    except (IOError, locale.Error) as e:
        print("Warning", app_name, e)
        __builtins__.__dict__["_"] = lambda x: x


class SimpleGladeApp(object):

    def __init__(self, path, root=None, domain=None, **kwargs):
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

        **kwargs:
            a dictionary representing the named extra arguments.
            It is useful to set attributes of new instances, for example:
                glade_app = SimpleGladeApp("ui.glade", foo="some value", bar="another value")
            sets two attributes (foo and bar) to glade_app.
        """
        if os.path.isfile(path):
            self.glade_path = path
        else:
            glade_dir = os.path.dirname(sys.argv[0])
            self.glade_path = os.path.join(glade_dir, path)
        for key, value in kwargs.items():
            try:
                setattr(self, key, weakref.proxy(value))
            except TypeError:
                setattr(self, key, value)

        self.glade = None

        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.glade_path)
        # TODO PORT connect
        # self.builder.connect_signals(self.custom_handler)

        if root:
            # TODO PORT remove the next line is not needed Guake shuold not pass an root parameter
            # this would mess stuff up
            # self.main_widget = self.builder.get_object("window-root")
            self.main_widget = self.builder.get_object(root)
            self.main_widget.show_all()
        else:
            self.main_widget = None

        # self.glade = self.create_glade(self.glade_path, root, domain)

        self.normalize_names()
        self.new()

    def __repr__(self):
        class_name = self.__class__.__name__
        if self.main_widget:
            root = gtk.Widget.get_name(self.main_widget)
            repr = '%s(path="%s", root="%s")' % (class_name, self.glade_path, root)
        else:
            repr = '%s(path="%s")' % (class_name, self.glade_path)
        return repr

    def new(self):
        """
        Method called when the user interface is loaded and ready to be used.
        At this moment, the widgets are loaded and can be refered as self.widget_name
        """
        pass

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
        # TODO PORT connect

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
                        "instance %s already has an attribute %s" % (self, widget_api_name)
                    )
                else:
                    setattr(self, widget_api_name, widget)
                    if prefixes:
                        # TODO is is a guess
                        Gtk.Buildable.set_data(widget, "prefixes", prefixes)

    def add_prefix_actions(self, prefix_actions_proxy):
        """
        By using a gui designer (glade-2, gazpacho, etc)
        widgets can have a prefix in theirs names
        like foo:entry1 or foo:label3
        It means entry1 and label3 has a prefix action named foo.

        Then, prefix_actions_proxy must have a method named prefix_foo which
        is called everytime a widget with prefix foo is found, using the found widget
        as argument.

        prefix_actions_proxy:
            An instance with methods as prefix actions.
            It means it has methods like prefix_foo, prefix_bar, etc.
        """
        prefix_s = "prefix_"
        prefix_pos = len(prefix_s)

        def is_method(t):
            return callable(t[1])

        def is_prefix_action(t):
            return t[0].startswith(prefix_s)

        def drop_prefix(k, w):
            return (k[prefix_pos:], w)

        members_t = inspect.getmembers(prefix_actions_proxy)
        methods_t = filter(is_method, members_t)
        prefix_actions_t = filter(is_prefix_action, methods_t)
        prefix_actions_d = dict(map(drop_prefix, prefix_actions_t))

        for widget in self.get_widgets():
            prefixes = gtk.Widget.get_data(widget, "prefixes")
            if prefixes:
                for prefix in prefixes:
                    if prefix in prefix_actions_d:
                        prefix_action = prefix_actions_d[prefix]
                        prefix_action(widget)

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
        gtk.main()

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
            self.on_keyboard_interrupt()

    def on_keyboard_interrupt(self):
        """
        This method is called by the default implementation of run()
        after a program is finished by pressing Control-C.
        """
        pass

    def install_custom_handler(self, custom_handler):
        gtk.glade.set_custom_handler(custom_handler)

    def create_glade(self, glade_path, root, domain):
        return gtk.glade.XML(glade_path, root, domain)

    def get_widget(self, widget_name):
        return self.builder.get_object(widget_name)

    def get_widgets(self):
        return self.builder.get_objects()


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
        # TODO PORT connect
        # self.builder.connect_signals(self)

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

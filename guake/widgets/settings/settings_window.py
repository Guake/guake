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

import logging
import traceback

# pylint: disable=wrong-import-position,wrong-import-order,unused-import
from guake import gi
assert gi  # hack to "use" the import so pep8/pyflakes are happy

# from gi.repository import Gdk
from gi.repository import Gtk
# pylint: enable=wrong-import-position,wrong-import-order,unused-import

from guake.widgets.widget import GuakeWidget


logger = logging.getLogger(__name__)

class GuakeSettingsWindow(GuakeWidget, Gtk.ApplicationWindow):

    def __init__(self, gtkbuilder, application, *args, **kwargs):
        super().__init__(application, *args, **kwargs)
        self.set_application(application)
        keyboard_shortcuts_store = Gtk.ListStore(str, str)
        [keyboard_shortcuts_store.append([key, application.keybindings.get_string(key)]) for key in application.keybindings.keys()]
        self.treeview = GuakeKeyboardShortcutsTreeView(gtkbuilder, application)
        self.treeview.set_model(keyboard_shortcuts_store)
        self.connect("delete_event", self.delete_handler)
        self.show_all()



    def delete_handler(self, *args):
        return self.hide() or True



class GuakeKeyboardShortcutsTreeView(GuakeWidget, Gtk.TreeView):

    def __init__(self, gtkbuilder, application, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.application = application
        self.append_column(Gtk.TreeViewColumn("Action", Gtk.CellRendererText(), text=0))
        self.append_column(Gtk.TreeViewColumn("Shortcut", GuakeKeybindingRenderer(self), text=1))

    def get_application(self):
        return self.application


class GuakeKeybindingRenderer(Gtk.CellRendererAccel):

    def __init__(self, treeview, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.treeview = treeview
        self.props.editable = True
        self.connect("accel-edited", self.accel_edited_handler)

    def accel_edited_handler(self, renderer, cell, keycode, modifier, hardcode):
        application = self.treeview.get_application()
        model = self.treeview.get_model()
        cell_iterator = model.get_iter(cell)
        keybinding_name, keybinding_value = model.get_value(cell_iterator, 0), model.get_value(cell_iterator, 1)
        keybinding_value_new = Gtk.accelerator_name(keycode, modifier)
        try:
            application.keybindings.set_string(keybinding_name, keybinding_value_new)
            model.set_value(model.get_iter(cell), 1, keybinding_value_new)
        except Exception as e:
            logger.error(traceback.format_exc())


#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class CellRendererAccel(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self)
        self.set_title("CellRendererAccel")
        self.connect("destroy", Gtk.main_quit)

        self.liststore = Gtk.ListStore(str, str)
        self.liststore.append(["New", "<Primary>n"])
        self.liststore.append(["Open", "<Primary>o"])
        self.liststore.append(["Save", "<Primary>s"])

        treeview = Gtk.TreeView()
        treeview.set_model(self.liststore)
        self.add(treeview)

        cellrenderertext = Gtk.CellRendererText()

        treeviewcolumn = Gtk.TreeViewColumn("Action")
        treeview.append_column(treeviewcolumn)
        treeviewcolumn.pack_start(cellrenderertext, True)
        treeviewcolumn.add_attribute(cellrenderertext, "text", 0)

        cellrendereraccel = Gtk.CellRendererAccel()
        cellrendereraccel.set_property("editable", True)
        cellrendereraccel.connect("accel-edited", self.on_accel_edited)
        cellrendereraccel.connect("accel-cleared", self.on_accel_cleared)

        treeviewcolumn = Gtk.TreeViewColumn("Accelerator")
        treeview.append_column(treeviewcolumn)
        treeviewcolumn.pack_start(cellrendereraccel, True)
        treeviewcolumn.add_attribute(cellrendereraccel, "text", 1)

    def on_accel_edited(self, cellrendereraccel, path, key, mods, hwcode):
        accelerator = Gtk.accelerator_name(key, mods)
        self.liststore[path][1] = accelerator

    def on_accel_cleared(self, cellrendereraccel, path):
        self.liststore[path][1] = "None"


window = CellRendererAccel()
window.show_all()

Gtk.main()

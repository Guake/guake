#!/usr/bin/env python3
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

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91') 

from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Vte

#from guake.dbus_manager import createDbusRemote
#from guake.dconf_handler import DconfHandler
from guake.terminal import Terminal
import cairo



class MyWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Hello World")

        terminal = Terminal()
        
        #help(terminal) 
        terminal.spawn_sync(
            Vte.PtyFlags.DEFAULT,
            os.environ['HOME'],
            ["/bin/bash"],
            [],
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None,
            None,
        )
        transparency = 50
        
        bgcolor = Gdk.RGBA(.2,.5,.8,0.5)
       # bgcolor.alpha = 1/100*transparency
        
        terminal.set_color_background(bgcolor)
        
        
        
        
        
        
        
        self.add(terminal)
        #self.dconf_handler = DconfHandler()
        #self.dconf_handler.registerSettingCallback("general",
        #                                           "debug-mode",
        #                                           "boolean",
        #                                           self.on_debug_mode_changed)
        
        
        
        
        
        
        def draw_callback(widget,cr):
            if widget.transparency:
                cr.set_source_rgba(0,0,0,0)
            else:
                cr.set_source_rgb(0,0,0)   
            cr.set_operator(cairo.OPERATOR_SOURCE)
            cr.paint()
            cr.set_operator(cairo.OPERATOR_OVER)
        self.set_app_paintable(True)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        self.transparency = False
        if visual and screen.is_composited():
            self.set_visual(visual)
            self.transparency = True
        else:
            print('System doesn\'t support transparency')
            self.set_visual(screen.get_system_visual)
        self.connect('draw', draw_callback)
        
        
        
        
        
        
        

    def on_debug_mode_changed(self, key, value):
        print("debug mode {} changed to {}".format(key, value))


def createGuake():
    win = MyWindow()
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    return win
createGuake()
#remote_object = createDbusRemote(createGuake)
Gtk.main()

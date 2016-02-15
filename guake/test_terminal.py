#!/usr/bin/env python

# import gi
import os

from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Vte


def test():
    # gi.require_version('Gtk', '3.0')

    terminal = Vte.Terminal()
    terminal.fork_command_full(
        Vte.PtyFlags.DEFAULT,
        os.environ['HOME'],
        ["/bin/bash"],
        [],
        GLib.SpawnFlags.DO_NOT_REAP_CHILD,
        None,
        None,
    )

    win = Gtk.Window()
    win.connect('delete-event', Gtk.main_quit)
    win.add(terminal)
    win.show_all()

    Gtk.main()

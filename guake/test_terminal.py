# -*- coding: utf-8; -*-
"""
Copyright (C) 2007-2017 Guake authors

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
import os

# pylint: disable=wrong-import-position,wrong-import-order,unused-import
from guake import gi
assert gi  # hack to "use" the import so pep8/pyflakes are happy

from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Vte
# pylint: enable=wrong-import-position,wrong-import-order,unused-import

from guake.widgets.terminal import GuakeTerminal

logger = logging.getLogger(__name__)


def main():
    terminal = GuakeTerminal()
    terminal.spawn_sync(
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


if __name__ == '__main__':
    main()

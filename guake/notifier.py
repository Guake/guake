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

import gi
gi.require_version('Notify', '0.7')
from gi.repository import GLib
from gi.repository import Notify

Notify.init("Guake")

__all__ = ['showMessage']


def showMessage(brief, body=None, icon=None):
    try:
        notification = Notify.Notification.new(brief, body, icon)
        notification.show()
    # pylint: disable=catching-non-exception
    except GLib.GError:
        pass
    # pylint: enable=catching-non-exception

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

from testwrap import dedent

from gi.repository import GLib
from gi.repository import Notify

Notify.init("Guake")

__all__ = ['showMessage']


RETRY_INTERVAL = 3  # seconds
retry_limit = 5  # tries


def showMessage(brief, body=None, icon=None):
    try:
        notification = Notify.Notification.new(brief, body, icon)
        notification.show()
    # pylint: disable=catching-non-exception
    except GLib.GError:
        printWarning()
        GLib.timeout_add_seconds(RETRY_INTERVAL, lambda: retry(brief, body, icon))

# pylint: enable=catching-non-exception


def retry(*args):
    global retry_limit

    if retry_limit <= 0:
        return False

    retry_limit -= 1
    showMessage(*args)


def printWarning():
    if not hasattr(printWarning, 'alreadyPrinted'):
        print(dedent('''
            Notification service is not running (yet). Guake can't display notifications!
              We'll retry a few times more a bit later, but you can use
              the following command to disable the startup notification:
            $ gconftool-2 --type bool --set /apps/guake/general/use_popup false
        ''').strip())
        printWarning.alreadyPrinted = True

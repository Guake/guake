"""
Copyright (C) 2013 Maxim Ivanov <ulidtko@gmail.com>

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
Free Software Foundation, Inc., 59 Temple Place - Suite 330,
Boston, MA 02111-1307, USA.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import glib
import logging

import pynotify

from textwrap import dedent

log = logging.getLogger(__name__)
pynotify.init("Guake")

__all__ = ['show_message']

RETRY_INTERVAL = 3  # seconds

retry_limit = 5  # tries


def show_message(brief, body=None, icon=None):
    try:
        notification = pynotify.Notification(brief, body, icon)
        notification.show()
    except glib.GError:
        print_warning()
        glib.timeout_add_seconds(RETRY_INTERVAL, lambda: retry(brief, body, icon))


def retry(*args):
    global retry_limit

    if retry_limit <= 0:
        return False

    retry_limit -= 1
    show_message(*args)


def print_warning():
    if not hasattr(print_warning, 'already_printed'):
        log.info(dedent('''
            Notification service is not running (yet). Guake can't display notifications!
              We'll retry a few times more a bit later, but you can use
              the following command to disable the startup notification:
            $ gconftool-2 --type bool --set /apps/guake/general/use_popup false
        ''').strip())
        print_warning.already_printed = True

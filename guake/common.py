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

import logging
import os
import sys

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')  # vte-0.38
from gi.repository import Gtk

from guake.paths import GLADE_DIR
from guake.paths import IMAGE_DIR

log = logging.getLogger(__name__)

__all__ = [
    'get_binaries_from_path',
    'gladefile',
    'hexify_color',
    'pixmapfile',
    'ShowableError',
    'bindtextdomain',
]


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

    import locale
    from locale import gettext as _

    log.info("Local binding for app '%s', local dir: %s", app_name, locale_dir)

    locale.bindtextdomain(app_name, locale_dir)
    locale.textdomain(app_name)


def ShowableError(parent, title, msg, exit_code=1):
    d = Gtk.MessageDialog(
        parent, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        Gtk.MessageType.WARNING, Gtk.ButtonsType.CLOSE
    )
    d.set_markup('<b><big>%s</big></b>' % title)
    d.format_secondary_markup(msg)
    d.run()
    d.destroy()


def pixmapfile(x):
    f = os.path.join(IMAGE_DIR, x)
    if not os.path.exists(f):
        raise IOError('No such file or directory: %s' % f)
    return os.path.abspath(f)


def gladefile(x):
    f = os.path.join(GLADE_DIR, x)
    if not os.path.exists(f):
        raise IOError('No such file or directory: %s' % f)
    return os.path.abspath(f)


def hexify_color(c):

    def h(x):
        return hex(x).replace('0x', '').zfill(4)

    return '#%s%s%s' % (h(c.red), h(c.green), h(c.blue))


def get_binaries_from_path(compiled_re):
    ret = []
    for i in os.environ.get('PATH', '').split(os.pathsep):
        if os.path.isdir(i):
            for j in os.listdir(i):
                if compiled_re.match(j):
                    ret.append(os.path.join(i, j))
    return ret


def shell_quote(text):
    """ quote text (filename) for inserting into a shell """
    return r"\'".join("'%s'" % p for p in text.split("'"))


def clamp(value, lower, upper):
    return max(min(value, upper), lower)

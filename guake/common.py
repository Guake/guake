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

import os
import sys

import gettext

import gconf
import gtk

# Internationalization purposes.
_ = gettext.gettext

__all__ = ['_', 'ShowableError', 'test_gconf',
           'pixmapfile', 'gladefile', 'hexify_color',
           'get_binaries_from_path']


class ShowableError(Exception):

    def __init__(self, title, msg, exit_code=1):
        d = gtk.MessageDialog(type=gtk.MESSAGE_ERROR,
                              buttons=gtk.BUTTONS_CLOSE)
        d.set_markup('<b><big>%s</big></b>' % title)
        d.format_secondary_markup(msg)
        d.run()
        d.destroy()
        if exit_code != -1:
            sys.exit(exit_code)
        super().__init__(msg)


def test_gconf():
    c = gconf.client_get_default()
    return c.dir_exists('/apps/guake')


def imageDir():
    return NotImplementedError()


def gladeDir():
    return NotImplementedError()


def pixmapfile(x):
    f = os.path.join(imageDir(), x)
    if not os.path.exists(f):
        raise IOError('No such file or directory: %s' % f)
    return os.path.abspath(f)


def gladefile(x):
    f = os.path.join(gladeDir(), x)
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

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

import inspect
import os

import gettext

# Internationalization purposes.
_ = gettext.gettext

__all__ = [
    '_',
    'ALIGN_BOTTOM',
    'ALIGN_CENTER',
    'ALIGN_LEFT',
    'ALIGN_RIGHT',
    'ALIGN_TOP',
    'ALWAYS_ON_PRIMARY',
    'GLADE_DIR',
    'IMAGE_DIR',
    'LOCALE_DIR',
    'NAME',
    'SCHEMA_DIR',
]


def is_run_from_git_workdir():
    self_path = os.path.abspath(inspect.getfile(inspect.currentframe()))
    return os.path.exists('%s.in' % self_path)


NAME = 'guake'
SRC_DIR = os.path.dirname(os.path.realpath(__file__))
DATADIR = os.environ.get("GUAKE_DATA_DIR", os.path.join(SRC_DIR, 'data'))

IMAGE_DIR = os.path.join(DATADIR, 'pixmaps')
GLADE_DIR = DATADIR
SCHEMA_DIR = DATADIR
LOCALE_DIR = "/usr/share/locale"

ALIGN_CENTER, ALIGN_LEFT, ALIGN_RIGHT = range(3)
ALIGN_TOP, ALIGN_BOTTOM = range(2)
ALWAYS_ON_PRIMARY = -1

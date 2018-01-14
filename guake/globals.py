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

import guake

__all__ = [
    'NAME', 'VERSION', 'IMAGE_DIR', 'GLADE_DIR', 'SCHEMA_DIR', 'LOCALE_DIR', 'ALIGN_CENTER',
    'ALIGN_RIGHT', 'ALIGN_LEFT', 'ALIGN_TOP', 'ALIGN_BOTTOM', 'ALWAYS_ON_PRIMARY'
]


def is_run_from_git_workdir():
    self_path = os.path.abspath(inspect.getfile(inspect.currentframe()))
    return os.path.exists('%s.in' % self_path)


NAME = 'guake'
VERSION = guake.__version__
DATADIR = os.environ.get("GUAKE_DATA_DIR")

SRC_DIR = os.path.dirname(os.path.realpath(__file__))
IMAGE_DIR = os.path.join(SRC_DIR, 'data/pixmaps')
GLADE_DIR = os.path.join(SRC_DIR, 'data')
SCHEMA_DIR = os.path.join(SRC_DIR, 'data')
LOCALE_DIR = "/usr/share/locale"

ALIGN_CENTER, ALIGN_LEFT, ALIGN_RIGHT = range(3)
ALIGN_TOP, ALIGN_BOTTOM = range(2)
ALWAYS_ON_PRIMARY = -1

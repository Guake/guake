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

import inspect
import os

import guake

__all__ = [
    'NAME', 'VERSION', 'IMAGE_DIR', 'GLADE_DIR', 'SCHEMA_DIR', 'LOCALE_DIR', 'GCONF_PATH', 'KEY',
    'ALIGN_CENTER', 'ALIGN_RIGHT', 'ALIGN_LEFT', 'ALIGN_TOP', 'ALIGN_BOTTOM', 'ALWAYS_ON_PRIMARY'
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

# TODO port dead!?
# Gconf stuff. Yep, it is hardcoded =)
GCONF_PATH = '/apps/guake'


def KEY(x):
    return (GCONF_PATH + x)


# Stuff used to build the treeview that will allow the user to change
# keybindings in the preferences window.


def LKEY(x):
    return GCONF_PATH + '/keybindings/local/' + x


def GKEY(x):
    return GCONF_PATH + '/keybindings/global/' + x


ALIGN_CENTER, ALIGN_LEFT, ALIGN_RIGHT = range(3)
ALIGN_TOP, ALIGN_BOTTOM = range(2)
ALWAYS_ON_PRIMARY = -1

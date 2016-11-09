#!/usr/bin/env python2
# -*- coding: utf-8; -*-
"""
Copyright (C) 2007-2012 Lincoln de Sousa <lincoln@minaslivre.org>
Copyright (C) 2007 Gabriel Falcão <gabrielteratos@gmail.com>

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

import dbus
import gtk
import logging
import os
import subprocess
import sys
import uuid

from optparse import OptionParser

from guake.common import ShowableError
from guake.common import _
from guake.common import test_gconf
from guake.dbusiface import DBUS_NAME
from guake.dbusiface import DBUS_PATH
from guake.dbusiface import DbusManager
from guake.globals import KEY
from guake.globals import VERSION
from guake.guake_app import Guake


log = logging.getLogger(__name__)


def main():
    """Parses the command line parameters and decide if dbus methods
    should be called or not. If there is already a guake instance
    running it will be used and a True value will be returned,
    otherwise, false will be returned.
    """

    # COLORTERM is an environment variable set by some terminal emulators such as gnome-terminal.
    # To avoid confusing applications running inside Guake, clean up COLORTERM at startup.
    if "COLORTERM" in os.environ:
        del os.environ['COLORTERM']

    # Force to xterm-256 colors for compatibility with some old command line programs
    os.environ["TERM"] = "xterm-256color"

    parser = OptionParser(version='Guake Terminal %s' % VERSION)
    parser.add_option('-f', '--fullscreen', dest='fullscreen',
                      action='store_true', default=False,
                      help=_('Put Guake in fullscreen mode'))

    parser.add_option('-t', '--toggle-visibility', dest='show_hide',
                      action='store_true', default=False,
                      help=_('Toggles the visibility of the terminal window'))

    parser.add_option('--show', dest="show",
                      action='store_true', default=False,
                      help=_('Shows Guake main window'))

    parser.add_option('--hide', dest='hide',
                      action='store_true', default=False,
                      help=_('Hides Guake main window'))

    parser.add_option('-p', '--preferences', dest='show_preferences',
                      action='store_true', default=False,
                      help=_('Shows Guake preference window'))

    parser.add_option('-a', '--about', dest='show_about',
                      action='store_true', default=False,
                      help=_('Shows Guake\'s about info'))

    parser.add_option('-n', '--new-tab', dest='new_tab',
                      action='store', default='',
                      help=_('Add a new tab (with current directory set to NEW_TAB)'))

    parser.add_option('-s', '--select-tab', dest='select_tab',
                      action='store', default='',
                      help=_('Select a tab (SELECT_TAB is the index of the tab)'))

    parser.add_option('-g', '--selected-tab', dest='selected_tab',
                      action='store_true', default=False,
                      help=_('Return the selected tab index.'))

    parser.add_option('-e', '--execute-command', dest='command',
                      action='store', default='',
                      help=_('Execute an arbitrary command in the selected tab.'))

    parser.add_option('-i', '--tab-index', dest='tab_index',
                      action='store', default='0',
                      help=_('Specify the tab to rename. Default is 0.'))

    parser.add_option('--bgimg', dest='bgimg',
                      action='store', default='',
                      help=_('Set the background image of '
                             'the selected tab.'))

    parser.add_option('--bgcolor', dest='bgcolor',
                      action='store', default='',
                      help=_('Set the hexadecimal (#rrggbb) background color of '
                             'the selected tab.'))

    parser.add_option('--fgcolor', dest='fgcolor',
                      action='store', default='',
                      help=_('Set the hexadecimal (#rrggbb) foreground color of the '
                             'selected tab.'))

    parser.add_option('--rename-tab', dest='rename_tab',
                      metavar='TITLE',
                      action='store', default='',
                      help=_('Rename the specified tab. Reset to default if TITLE is '
                             'a single dash "-".'))

    parser.add_option('-r', '--rename-current-tab', dest='rename_current_tab',
                      metavar='TITLE',
                      action='store', default='',
                      help=_('Rename the current tab. Reset to default if TITLE is a '
                             'single dash "-".'))

    parser.add_option('-q', '--quit', dest='quit',
                      action='store_true', default=False,
                      help=_('Says to Guake go away =('))

    parser.add_option('-u', '--no-startup-script', dest='execute_startup_script',
                      action='store_false', default=True,
                      help=_('Do not execute the start up script'))

    options = parser.parse_args()[0]

    instance = None

    # Trying to get an already running instance of guake. If it is not
    # possible, lets create a new instance. This function will return
    # a boolean value depending on this decision.
    try:
        bus = dbus.SessionBus()
        remote_object = bus.get_object(DBUS_NAME, DBUS_PATH)
        already_running = True
    except dbus.DBusException:
        instance = Guake()
        remote_object = DbusManager(instance)
        already_running = False

    only_show_hide = True

    if options.fullscreen:
        remote_object.fullscreen()

    if options.show:
        remote_object.show_from_remote()

    if options.hide:
        remote_object.hide_from_remote()

    if options.show_preferences:
        remote_object.show_prefs()
        only_show_hide = False

    if options.new_tab:
        remote_object.add_tab(options.new_tab)
        only_show_hide = False

    if options.select_tab:
        selected = int(options.select_tab)
        i = remote_object.select_tab(selected)
        if i is None:
            sys.stdout.write('invalid index: %d\n' % selected)
        only_show_hide = False

    if options.selected_tab:
        selected = remote_object.get_selected_tab()
        sys.stdout.write('%d\n' % selected)
        only_show_hide = False

    if options.command:
        remote_object.execute_command(options.command)
        only_show_hide = False

    if options.tab_index and options.rename_tab:
        try:
            remote_object.rename_tab_uuid(str(uuid.UUID(options.tab_index)), options.rename_tab)
        except ValueError:
            remote_object.rename_tab(int(options.tab_index), options.rename_tab)
        only_show_hide = False

    if options.bgimg:
        remote_object.set_bg_image(options.bgimg)
        only_show_hide = False

    if options.bgcolor:
        remote_object.set_bgcolor(options.bgcolor)
        only_show_hide = False

    if options.fgcolor:
        remote_object.set_fgcolor(options.fgcolor)
        only_show_hide = False

    if options.rename_current_tab:
        remote_object.rename_current_tab(options.rename_current_tab)
        only_show_hide = False

    if options.show_about:
        remote_object.show_about()
        only_show_hide = False

    if already_running and only_show_hide:
        # here we know that guake was called without any parameter and
        # it is already running, so, lets toggle its visibility.
        remote_object.show_hide()

    if options.execute_startup_script:
        if not already_running:
            startup_script = instance.client.get_string(KEY("/general/startup_script"))
            if startup_script:
                log.info("Calling startup script: %s", startup_script)
                pid = subprocess.Popen([startup_script], shell=True, stdin=None, stdout=None,
                                       stderr=None, close_fds=True)
                log.info("Startup script started with pid: %s", pid)
                # Please ensure this is the last line !!!!
    else:
        log.info("--no-startup-script argument defined, so don't execute the startup script")
    return already_running


def exec_main():
    if not test_gconf():
        raise ShowableError(_('Guake can not init!'),
                            _('Gconf Error.\n'
                              'Have you installed <b>guake.schemas</b> properly?'))

    if not main():
        gtk.main()

if __name__ == '__main__':
    exec_main()

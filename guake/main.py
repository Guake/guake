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
# You can put calls to p() everywhere in this page to inspect timing
#
# import inspect
# import time
# g_start = time.time()
# def p():
#     print(time.time() - g_start, __file__, inspect.currentframe().f_back.f_lineno)

import builtins
import logging
import os
import signal
import subprocess
import sys
import uuid

from locale import gettext

builtins.__dict__["_"] = gettext

from optparse import OptionParser

log = logging.getLogger(__name__)

# Force use X11 backend under wayland before any import of GDK through dependencies.
# This could fix weird problems under Wayland.
# But if user set the environment variable GUAKE_ENABLE_WAYLAND, then force
# use Wayland backend.
os.environ["GDK_BACKEND"] = "x11"
if "GUAKE_ENABLE_WAYLAND" in os.environ:
    os.environ["GDK_BACKEND"] = "wayland"

from guake.globals import NAME
from guake.globals import bindtextdomain
from guake.support import print_support
from guake.utils import restore_preferences
from guake.utils import save_preferences

# When we are in the document generation on readthedocs,
# we do not have paths.py generated
try:
    from guake.paths import LOCALE_DIR

    bindtextdomain(NAME, LOCALE_DIR)
except:  # pylint: disable=bare-except
    pass

# pylint: disable=import-outside-toplevel


def main():
    """Parses the command line parameters and decide if dbus methods
    should be called or not. If there is already a guake instance
    running it will be used and a True value will be returned,
    otherwise, false will be returned.
    """
    # Force to xterm-256 colors for compatibility with some old command line programs
    os.environ["TERM"] = "xterm-256color"

    # do not use version keywords here, pbr might be slow to find the version of Guake module
    parser = OptionParser()
    parser.add_option(
        "-V",
        "--version",
        dest="version",
        action="store_true",
        default=False,
        help=_("Show Guake version number and exit"),
    )

    parser.add_option(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        default=False,
        help=_("Enable verbose logging"),
    )

    parser.add_option(
        "-f",
        "--fullscreen",
        dest="fullscreen",
        action="store_true",
        default=False,
        help=_("Put Guake in fullscreen mode"),
    )

    parser.add_option(
        "--unfullscreen",
        dest="unfullscreen",
        action="store_true",
        default=False,
        help=_("Put Guake out from fullscreen mode"),
    )

    parser.add_option(
        "-t",
        "--toggle-visibility",
        dest="show_hide",
        action="store_true",
        default=False,
        help=_("Toggles the visibility of the terminal window"),
    )

    parser.add_option(
        "--is-visible",
        dest="is_visible",
        action="store_true",
        default=False,
        help=_("Return 1 if Guake is visible, 0 otherwise"),
    )

    parser.add_option(
        "--show",
        dest="show",
        action="store_true",
        default=False,
        help=_("Shows Guake main window"),
    )

    parser.add_option(
        "--hide",
        dest="hide",
        action="store_true",
        default=False,
        help=_("Hides Guake main window"),
    )

    parser.add_option(
        "-p",
        "--preferences",
        dest="show_preferences",
        action="store_true",
        default=False,
        help=_("Shows Guake preference window"),
    )

    parser.add_option(
        "-a",
        "--about",
        dest="show_about",
        action="store_true",
        default=False,
        help=_("Shows Guake's about info"),
    )

    parser.add_option(
        "-n",
        "--new-tab",
        dest="new_tab",
        action="store",
        default="",
        help=_("Add a new tab (with current directory set to NEW_TAB)"),
    )

    parser.add_option(
        "-s",
        "--select-tab",
        dest="select_tab",
        action="store",
        default="",
        help=_("Select a tab (SELECT_TAB is the index of the tab)"),
    )

    parser.add_option(
        "-g",
        "--selected-tab",
        dest="selected_tab",
        action="store_true",
        default=False,
        help=_("Return the selected tab index."),
    )

    parser.add_option(
        "-l",
        "--selected-tablabel",
        dest="selected_tablabel",
        action="store_true",
        default=False,
        help=_("Return the selected tab label."),
    )

    parser.add_option(
        "-S",
        "--select-terminal",
        dest="select_terminal",
        metavar="TERMINAL_INDEX",
        action="store",
        default="",
        help=_(
            "Select a specific terminal in a split tab. "
            + "Only useful with split terminals (TERMINAL_INDEX is the index of the tab)"
        ),
    )

    parser.add_option(
        "--selected-terminal",
        dest="selected_terminal",
        action="store_true",
        default=False,
        help=_("Return the selected terminal index."),
    )

    parser.add_option(
        "--split-vertical",
        dest="split_vertical",
        action="store_true",
        default=False,
        help=_("Split the selected tab vertically."),
    )

    parser.add_option(
        "--split-horizontal",
        dest="split_horizontal",
        action="store_true",
        default=False,
        help=_("Split the selected tab horizontally."),
    )

    parser.add_option(
        "-e",
        "--execute-command",
        dest="command",
        action="store",
        default="",
        help=_("Execute an arbitrary command in the selected tab."),
    )

    parser.add_option(
        "-i",
        "--tab-index",
        dest="tab_index",
        action="store",
        default="0",
        help=_("Specify the tab to rename. Default is 0. Can be used to select tab by UUID."),
    )

    parser.add_option(
        "--bgcolor",
        dest="bgcolor",
        action="store",
        default="",
        help=_("Set the hexadecimal (#rrggbb) background color of " "the selected tab."),
    )

    parser.add_option(
        "--fgcolor",
        dest="fgcolor",
        action="store",
        default="",
        help=_("Set the hexadecimal (#rrggbb) foreground color of the " "selected tab."),
    )

    parser.add_option(
        "--bgcolor-current",
        dest="bgcolor_current",
        action="store",
        default="",
        help=_("Set the hexadecimal (#rrggbb) background color of " "the current terminal."),
    )

    parser.add_option(
        "--fgcolor-current",
        dest="fgcolor_current",
        action="store",
        default="",
        help=_("Set the hexadecimal (#rrggbb) foreground color of " "the current terminal."),
    )

    parser.add_option(
        "--change-palette",
        dest="palette_name",
        action="store",
        default="",
        help=_("Change Guake palette scheme"),
    )

    parser.add_option(
        "--reset-colors",
        dest="reset_colors",
        action="store_true",
        default=False,
        help=_("Set colors from settings."),
    )

    parser.add_option(
        "--reset-colors-current",
        dest="reset_colors_current",
        action="store_true",
        default=False,
        help=_("Set colors of the current terminal from settings."),
    )

    parser.add_option(
        "--rename-tab",
        dest="rename_tab",
        metavar="TITLE",
        action="store",
        default="",
        help=_(
            "Rename the specified tab by --tab-index. Reset to default if TITLE is "
            'a single dash "-".'
        ),
    )

    parser.add_option(
        "-r",
        "--rename-current-tab",
        dest="rename_current_tab",
        metavar="TITLE",
        action="store",
        default="",
        help=_("Rename the current tab. Reset to default if TITLE is a " 'single dash "-".'),
    )

    parser.add_option(
        "-q",
        "--quit",
        dest="quit",
        action="store_true",
        default=False,
        help=_("Says to Guake go away =("),
    )

    parser.add_option(
        "-u",
        "--no-startup-script",
        dest="execute_startup_script",
        action="store_false",
        default=True,
        help=_("Do not execute the start up script"),
    )

    parser.add_option(
        "--save-preferences",
        dest="save_preferences",
        action="store",
        default=None,
        help=_("Save Guake preferences to this filename"),
    )

    parser.add_option(
        "--restore-preferences",
        dest="restore_preferences",
        action="store",
        default=None,
        help=_("Restore Guake preferences from this file"),
    )

    parser.add_option(
        "--support",
        dest="support",
        action="store_true",
        default=False,
        help=_("Show support information"),
    )

    # checking mandatory dependencies

    missing_deps = False
    try:
        import gi

        gi.require_version("Gtk", "3.0")
        gi.require_version("Gdk", "3.0")
    except ValueError:
        print("[ERROR] missing mandatory dependency: GtK 3.0")
        missing_deps = True

    try:
        gi.require_version("Vte", "2.91")  # vte-0.42
    except ValueError:
        print("[ERROR] missing mandatory dependency: Vte >= 0.42")
        missing_deps = True

    try:
        gi.require_version("Keybinder", "3.0")
    except ValueError:
        print("[ERROR] missing mandatory dependency: Keybinder 3")
        missing_deps = True

    if missing_deps:
        print(
            "[ERROR] missing at least one system dependencies. "
            "You need to install additional packages for Guake to run"
        )
        print(
            "[ERROR] On Debian/Ubuntu you need to install the following libraries:\n"
            "    sudo apt-get install -y --no-install-recommends \\\n"
            "        gir1.2-keybinder-3.0 \\\n"
            "        gir1.2-notify-0.7 \\\n"
            "        gir1.2-vte-2.91 \\\n"
            "        gir1.2-wnck-3.0 \\\n"
            "        libkeybinder-3.0-0 \\\n"
            "        libutempter0 \\\n"
            "        python3 \\\n"
            "        python3-dbus \\\n"
            "        python3-gi \\\n"
            "        python3-pip"
        )
        sys.exit(1)

    options = parser.parse_args()[0]
    if options.version:
        from guake import gtk_version
        from guake import guake_version
        from guake import vte_version
        from guake import vte_runtime_version

        print(f"Guake Terminal: {guake_version()}")
        print(f"VTE: {vte_version()}")
        print(f"VTE runtime: {vte_runtime_version()}")
        print(f"Gtk: {gtk_version()}")
        sys.exit(0)

    if options.save_preferences and options.restore_preferences:
        parser.error("options --save-preferences and --restore-preferences are mutually exclusive")
    if options.save_preferences:
        save_preferences(options.save_preferences)
        sys.exit(0)
    elif options.restore_preferences:
        restore_preferences(options.restore_preferences)
        sys.exit(0)

    if options.support:
        print_support()
        sys.exit(0)

    import dbus

    from guake.dbusiface import DBUS_NAME
    from guake.dbusiface import DBUS_PATH
    from guake.dbusiface import DbusManager
    from guake.guake_logging import setupLogging

    instance = None

    # Trying to get an already running instance of guake. If it is not
    # possible, lets create a new instance. This function will return
    # a boolean value depending on this decision.
    try:
        bus = dbus.SessionBus()
        remote_object = bus.get_object(DBUS_NAME, DBUS_PATH)
        already_running = True
    except dbus.DBusException:
        # can now configure the logging
        setupLogging(options.verbose)

        # COLORTERM is an environment variable set by some terminal emulators such as
        # gnome-terminal.
        # To avoid confusing applications running inside Guake, clean up COLORTERM at startup.
        if "COLORTERM" in os.environ:
            del os.environ["COLORTERM"]

        log.info("Guake not running, starting it")
        # late loading of the Guake object, to speed up dbus comm
        from guake.guake_app import Guake

        instance = Guake()
        remote_object = DbusManager(instance)
        already_running = False

    only_show_hide = True

    if options.fullscreen:
        remote_object.fullscreen()

    if options.unfullscreen:
        remote_object.unfullscreen()

    if options.show:
        remote_object.show_from_remote()

    if options.hide:
        remote_object.hide_from_remote()

    if options.is_visible:
        visibility = remote_object.get_visibility()
        sys.stdout.write(f"{visibility}\n")
        only_show_hide = options.show

    if options.show_preferences:
        remote_object.show_prefs()
        only_show_hide = options.show

    if options.new_tab:
        remote_object.add_tab(options.new_tab)
        only_show_hide = options.show

    if options.select_tab:
        selected = int(options.select_tab)
        tab_count = int(remote_object.get_tab_count())
        if 0 <= selected < tab_count:
            remote_object.select_tab(selected)
        else:
            sys.stderr.write(f"invalid index: {selected}\n")
        only_show_hide = options.show

    if options.selected_tab:
        selected = remote_object.get_selected_tab()
        sys.stdout.write(f"{selected}\n")
        only_show_hide = options.show

    if options.selected_tablabel:
        selectedlabel = remote_object.get_selected_tablabel()
        sys.stdout.write(f"{selectedlabel}\n")
        only_show_hide = options.show

    if options.split_vertical:
        remote_object.v_split_current_terminal()
        only_show_hide = options.show

    if options.split_horizontal:
        remote_object.h_split_current_terminal()
        only_show_hide = options.show

    if options.selected_terminal:
        selected = remote_object.get_selected_terminal()
        sys.stdout.write(f"{selected}\n")
        only_show_hide = options.show

    if options.select_terminal:
        selected = int(options.select_terminal)
        term_count = int(remote_object.get_term_count())
        if 0 <= selected < term_count:
            remote_object.select_terminal(selected)
        else:
            sys.stderr.write(f"invalid index: {selected}\n")
        only_show_hide = options.show

    if options.command:
        remote_object.execute_command(options.command)
        only_show_hide = options.show

    if options.tab_index and options.rename_tab:
        try:
            remote_object.rename_tab_uuid(str(uuid.UUID(options.tab_index)), options.rename_tab)
        except ValueError:
            remote_object.rename_tab(int(options.tab_index), options.rename_tab)
        only_show_hide = options.show

    if options.bgcolor:
        remote_object.set_bgcolor(options.bgcolor)
        only_show_hide = options.show

    if options.fgcolor:
        remote_object.set_fgcolor(options.fgcolor)
        only_show_hide = options.show

    if options.bgcolor_current:
        remote_object.set_bgcolor_current_terminal(options.bgcolor_current)
        only_show_hide = options.show

    if options.fgcolor_current:
        remote_object.set_fgcolor_current_terminal(options.fgcolor_current)
        only_show_hide = options.show

    if options.palette_name:
        remote_object.change_palette_name(options.palette_name)
        only_show_hide = options.show

    if options.reset_colors:
        remote_object.reset_colors()
        only_show_hide = options.show

    if options.reset_colors_current:
        remote_object.reset_colors_current()
        only_show_hide = options.show

    if options.rename_current_tab:
        remote_object.rename_current_tab(options.rename_current_tab)
        only_show_hide = options.show

    if options.show_about:
        remote_object.show_about()
        only_show_hide = options.show

    if options.quit:
        try:
            remote_object.quit()
            return True
        except dbus.DBusException:
            return True

    if already_running and only_show_hide:
        # here we know that guake was called without any parameter and
        # it is already running, so, lets toggle its visibility.
        remote_object.show_hide()

    if options.execute_startup_script:
        if not already_running:
            startup_script = instance.settings.general.get_string("startup-script")
            if startup_script:
                log.info("Calling startup script: %s", startup_script)
                with subprocess.Popen(
                    [startup_script],
                    shell=True,
                    stdin=None,
                    stdout=None,
                    stderr=None,
                    close_fds=True,
                ) as pid:
                    log.info("Startup script started with pid: %s", pid)
                # Please ensure this is the last line !!!!
    else:
        log.info("--no-startup-script argument defined, so don't execute the startup script")
    if already_running:
        log.info("Guake is already running")
    return already_running


def exec_main():
    if not main():
        log.debug("Running main gtk loop")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        # Load gi pretty late, to speed up as much as possible the parsing of the option for DBus
        # comm through command line
        import gi

        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        Gtk.main()


if __name__ == "__main__":
    exec_main()

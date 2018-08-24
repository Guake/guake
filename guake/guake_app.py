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
import json
import logging
import os
import platform
import subprocess
import sys
import traceback
import uuid

from pathlib import Path
from textwrap import dedent
from urllib.parse import quote_plus
from xml.sax.saxutils import escape as xml_escape

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Vte', '2.91')  # vte-0.42
gi.require_version('Keybinder', '3.0')
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gdk
from gi.repository import GdkX11
from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import Keybinder
from gi.repository import Vte

import cairo

from guake import gtk_version
from guake import guake_version
from guake import notifier
from guake import vte_version
from guake.about import AboutDialog
from guake.common import gladefile
from guake.common import pixmapfile
from guake.globals import ALIGN_BOTTOM
from guake.globals import ALIGN_CENTER
from guake.globals import ALIGN_LEFT
from guake.globals import ALIGN_RIGHT
from guake.globals import ALIGN_TOP
from guake.globals import ALWAYS_ON_PRIMARY
from guake.globals import NAME
from guake.gsettings import GSettingHandler
from guake.guake_logging import setupLogging
from guake.keybindings import Keybindings
from guake.notebook import TerminalNotebook
from guake.paths import LOCALE_DIR
from guake.paths import SCHEMA_DIR
from guake.paths import try_to_compile_glib_schemas
from guake.prefs import PrefsDialog
from guake.prefs import refresh_user_start
from guake.settings import Settings
from guake.simplegladeapp import SimpleGladeApp
from guake.terminal import GuakeTerminal
from guake.theme import get_gtk_theme
from guake.theme import select_gtk_theme
from guake.utils import get_server_time
from locale import gettext as _

libutempter = None
try:
    # this allow to run some commands that requires libuterm to
    # be injected in current process, as: wall
    from atexit import register as at_exit_call
    from ctypes import cdll
    libutempter = cdll.LoadLibrary('libutempter.so.0')
    if libutempter is not None:
        # We absolutely need to remove the old tty from the utmp !!!
        at_exit_call(libutempter.utempter_remove_added_record)
except Exception as e:
    libutempter = None
    sys.stderr.write("[WARN] ===================================================================\n")
    sys.stderr.write("[WARN] Unable to load the library libutempter !\n")
    sys.stderr.write(
        "[WARN] Some feature might not work:\n"
        "[WARN]  - 'exit' command might freeze the terminal instead of closing the tab\n"
        "[WARN]  - the 'wall' command is know to work badly\n"
    )
    sys.stderr.write("[WARN] Error: " + str(e) + '\n')
    sys.stderr.write(
        "[WARN] ===================================================================²\n"
    )

log = logging.getLogger(__name__)

instance = None
RESPONSE_FORWARD = 0
RESPONSE_BACKWARD = 1

# Disable find feature until python-vte hasn't been updated
enable_find = False

GObject.threads_init()

# Setting gobject program name
GObject.set_prgname(NAME)

GDK_WINDOW_STATE_WITHDRAWN = 1
GDK_WINDOW_STATE_ICONIFIED = 2
GDK_WINDOW_STATE_STICKY = 8
GDK_WINDOW_STATE_ABOVE = 32

# Transparency max level (should be always 100)
MAX_TRANSPARENCY = 100


class PromptQuitDialog(Gtk.MessageDialog):

    """Prompts the user whether to quit/close a tab.
    """

    def __init__(self, parent, procs, tabs):
        super(PromptQuitDialog, self).__init__(
            parent, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO
        )

        if tabs == -1:
            primary_msg = _("Do you want to close the tab?")
            tab_str = ''
        else:
            primary_msg = _("Do you really want to quit Guake?")
            if tabs == 1:
                tab_str = _(" and one tab open")
            else:
                tab_str = _(" and {0} tabs open").format(tabs)

        if procs == 0:
            proc_str = _("There are no processes running")
        elif procs == 1:
            proc_str = _("There is a process still running")
        else:
            proc_str = _("There are {0} processes still running").format(procs)

        self.set_markup(primary_msg)
        self.format_secondary_markup("<b>{0}{1}.</b>".format(proc_str, tab_str))


class Guake(SimpleGladeApp):

    """Guake main class. Handles specialy the main window.
    """

    def __init__(self):

        def load_schema():
            return Gio.SettingsSchemaSource.new_from_directory(
                SCHEMA_DIR, Gio.SettingsSchemaSource.get_default(), False
            )

        try:
            schema_source = load_schema()
        except GLib.Error:  # pylint: disable=catching-non-exception
            log.exception("Unable to load the GLib schema, try to compile it")
            try_to_compile_glib_schemas()
            schema_source = load_schema()
        self.settings = Settings(schema_source)
        select_gtk_theme(self.settings)

        super(Guake, self).__init__(gladefile('guake.glade'))

        self._patch_theme()
        self.add_callbacks(self)

        self.debug_mode = self.settings.general.get_boolean('debug-mode')
        setupLogging(self.debug_mode)
        log.info('Guake Terminal %s', guake_version())
        log.info('VTE %s', vte_version())
        log.info('Gtk %s', gtk_version())

        self.prompt_dialog = None
        self.hidden = True
        self.forceHide = False
        self.preventHide = False

        self.custom_command_menuitem = None

        # trayicon! Using SVG handles better different OS trays
        # img = pixmapfile('guake-tray.svg')
        # trayicon!
        img = pixmapfile('guake-tray.png')
        try:
            import appindicator
        except ImportError:
            self.tray_icon = Gtk.StatusIcon()
            self.tray_icon.set_from_file(img)
            self.tray_icon.set_tooltip_text(_("Guake Terminal"))
            self.tray_icon.connect('popup-menu', self.show_menu)
            self.tray_icon.connect('activate', self.show_hide)
        else:
            # TODO PORT test this on a system with app indicator
            self.tray_icon = appindicator.Indicator(
                _("guake-indicator"), _("guake-tray"), appindicator.CATEGORY_OTHER
            )
            self.tray_icon.set_icon(img)
            self.tray_icon.set_status(appindicator.STATUS_ACTIVE)
            menu = self.get_widget('tray-menu')
            show = Gtk.MenuItem(_('Show'))
            show.set_sensitive(True)
            show.connect('activate', self.show_hide)
            show.show()
            menu.prepend(show)
            self.tray_icon.set_menu(menu)

        # important widgets
        self.window = self.get_widget('window-root')
        self.window.set_keep_above(True)
        self.mainframe = self.get_widget('mainframe')
        self.mainframe.remove(self.get_widget('notebook-teminals'))
        self.notebook = TerminalNotebook(self)
        self.notebook.set_name("notebook-teminals")

        # help(Gtk.PositionType)
        self.notebook.set_tab_pos(Gtk.PositionType.BOTTOM)
        self.notebook.set_property("show-tabs", True)
        self.notebook.set_property("enable-popup", False)
        self.notebook.set_property("scrollable", True)
        self.notebook.set_property("show-border", False)
        self.notebook.set_property("visible", True)
        self.notebook.set_property("has-focus", True)
        self.notebook.set_property("can-focus", True)
        self.notebook.set_property("is-focus", True)
        self.notebook.set_property("expand", True)
        self.mainframe.add(self.notebook)
        self.set_tab_position()

        self.toolbar = self.get_widget('toolbar')
        self.mainframe = self.get_widget('mainframe')

        # check and set ARGB for real transparency
        color = self.window.get_style_context().get_background_color(Gtk.StateFlags.NORMAL)
        self.window.set_app_paintable(True)

        def draw_callback(widget, cr):
            if widget.transparency:
                cr.set_source_rgba(color.red, color.green, color.blue, 1)
            else:
                cr.set_source_rgb(0, 0, 0)
            cr.set_operator(cairo.OPERATOR_SOURCE)
            cr.paint()
            cr.set_operator(cairo.OPERATOR_OVER)

        screen = self.window.get_screen()
        visual = screen.get_rgba_visual()

        if visual and screen.is_composited():
            self.window.set_visual(visual)
            self.window.transparency = True
        else:
            log.warn('System doesn\'t support transparency')
            self.window.transparency = False
            self.window.set_visual(screen.get_system_visual())

        self.window.connect('draw', draw_callback)

        # It's intended to know which tab was selected to
        # close/rename. This attribute will be set in
        # self.show_tab_menu
        self.selected_tab = None

        # holds fullscreen status
        self.is_fullscreen = False

        # holds the timestamp of the losefocus event
        self.losefocus_time = 0

        # holds the timestamp of the previous show/hide action
        self.prev_showhide_time = 0

        # Controls the transparency state needed for function accel_toggle_transparency
        self.transparency_toggled = False

        # load cumstom command menu and menuitems from config file
        self.custom_command_menuitem = None
        self.load_custom_commands()

        # store the default window title to reset it when update is not wanted
        self.default_window_title = self.window.get_title()

        self.abbreviate = False

        # Flag to prevent guake hide when window_losefocus is true and
        # user tries to use the context menu.
        self.showing_context_menu = False

        def hide_context_menu(menu):
            """Turn context menu flag off to make sure it is not being
            shown.
            """
            self.showing_context_menu = False

        self.get_widget('context-menu').connect('hide', hide_context_menu)

        # setting up the TabContextMenuHelper
        self.tab_context_menu_helper = TabContextMenuHelper(self.get_widget('tab-menu'))

        self.window.connect('focus-out-event', self.on_window_losefocus)

        # Handling the delete-event of the main window to avoid
        # problems when closing it.
        def destroy(*args):
            self.hide()
            return True

        def window_event(*args):
            return self.window_event(*args)

        self.window.connect('delete-event', destroy)
        self.window.connect('window-state-event', window_event)

        # this line is important to resize the main window and make it
        # smaller.
        # TODO PORT do we still need this?
        # self.window.set_geometry_hints(min_width=1, min_height=1)

        # special trick to avoid the "lost guake on Ubuntu 'Show Desktop'" problem.
        # DOCK makes the window foundable after having being "lost" after "Show
        # Desktop"
        self.window.set_type_hint(Gdk.WindowTypeHint.DOCK)
        # Restore back to normal behavior
        self.window.set_type_hint(Gdk.WindowTypeHint.NORMAL)

        # loading and setting up configuration stuff
        GSettingHandler(self)
        Keybinder.init()
        self.hotkeys = Keybinder
        Keybindings(self)
        self.load_config()

        # adding the first tab on guake
        self.add_tab()

        self.get_widget("context_find_tab").set_visible(enable_find)

        if self.settings.general.get_boolean('start-fullscreen'):
            self.fullscreen()

        refresh_user_start(self.settings)

        # Pop-up that shows that guake is working properly (if not
        # unset in the preferences windows)
        if self.settings.general.get_boolean('use-popup'):
            key = self.settings.keybindingsGlobal.get_string('show-hide')
            keyval, mask = Gtk.accelerator_parse(key)
            label = Gtk.accelerator_get_label(keyval, mask)
            filename = pixmapfile('guake-notification.png')
            notifier.showMessage(
                _("Guake Terminal"),
                _("Guake is now running,\n"
                  "press <b>{!s}</b> to use it.").format(xml_escape(label)), filename
            )

        log.info("Guake initialized")

    def _patch_theme(self):
        theme_name, variant = get_gtk_theme(self.settings)

        def rgba_to_hex(color):
            return "#{0:02x}{1:02x}{2:02x}".format(
                int(color.red * 255), int(color.green * 255), int(color.blue * 255)
            )

        style_context = self.get_widget("window-root").get_style_context()
        # for n in [
        #     "inverted_bg_color",
        #     "inverted_fg_color",
        #     "selected_bg_color",
        #     "selected_fg_color",
        #     "theme_inverted_bg_color",
        #     "theme_inverted_fg_color",
        #     "theme_selected_bg_color",
        #     "theme_selected_fg_color",
        #     ]:
        #     s = style_context.lookup_color(n)
        #     print(n, s, rgba_to_hex(s[1]))
        selected_fg_color = rgba_to_hex(style_context.lookup_color("theme_selected_fg_color")[1])
        selected_bg_color = rgba_to_hex(style_context.lookup_color("theme_selected_bg_color")[1])
        log.debug(
            "Patching theme '%s' (prefer dark = '%r'), overriding tab 'checked' state': "
            "foreground: %r, background: %r", theme_name, "yes"
            if variant == "dark" else "no", selected_fg_color, selected_bg_color
        )
        css_data = dedent(
            """
            .custom_tab:checked {{
              color: {selected_fg_color};
              background: {selected_bg_color};
            }}
            """.format(selected_bg_color=selected_bg_color, selected_fg_color=selected_fg_color)
        ).encode()
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css_data)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    # load the custom commands infrastucture
    def load_custom_commands(self):
        if self.custom_command_menuitem:
            self.get_widget('context-menu').remove(self.custom_command_menuitem)
        custom_commands_menu = Gtk.Menu()
        if not self.get_custom_commands(custom_commands_menu):
            return
        menu = Gtk.MenuItem(_("Custom Commands"))
        menu.set_submenu(custom_commands_menu)
        menu.show()
        self.custom_command_menuitem = menu
        context_menu = self.get_widget('context-menu')
        context_menu.insert(self.custom_command_menuitem, self.context_menu_get_insert_pos())

    # returns position where the custom cmd must be placed on the context-menu
    def context_menu_get_insert_pos(self):
        # assuming that the quit menuitem is always the last one and with a
        # separator before him
        return len(self.get_widget('context-menu').get_children()) - 2

    # function to read commands stored at /general/custom_command_file and
    # launch the context menu builder
    def get_custom_commands(self, menu):
        """
        Example for a custom commands file
        [
            {
                "type": "menu",
                "description": "dir listing",
                "items": [
                    {
                        "description": "la",
                        "cmd":["ls", "-la"]
                    },
                    {
                        "description": "tree",
                        "cmd":["tree", ""]
                    }
                ]
            },
            {
                "description": "less ls",
                "cmd": ["ls | less", ""]
            }
        ]
        """
        custom_command_file_path = self.settings.general.get_string('custom-command-file')
        if not custom_command_file_path:
            return False
        file_name = os.path.expanduser(custom_command_file_path)
        if not file_name:
            return False
        try:
            with open(file_name) as f:
                data_file = f.read()
        except Exception as e:
            data_file = None
        if not data_file:
            return False

        try:
            custom_commands = json.loads(data_file)
            for json_object in custom_commands:
                self.parse_custom_commands(json_object, menu)
            return True

        except Exception:
            log.exception("Invalid custom command file %s. Exception:", data_file)
            return False

    # function to build the custom commands menu and menuitems
    def parse_custom_commands(self, json_object, menu):
        if json_object.get('type') == "menu":
            newmenu = Gtk.Menu()
            newmenuitem = Gtk.MenuItem(json_object['description'])
            newmenuitem.set_submenu(newmenu)
            newmenuitem.show()
            menu.append(newmenuitem)
            for item in json_object['items']:
                self.parse_custom_commands(item, newmenu)
        else:
            menu_item = Gtk.MenuItem(json_object['description'])
            custom_command = ""
            space = ""
            for command in json_object['cmd']:
                custom_command += (space + command)
                space = " "

            menu_item.connect("activate", self.execute_context_menu_cmd, custom_command)
            menu.append(menu_item)
            menu_item.show()

    # execute contextual menu call
    def execute_context_menu_cmd(self, item, cmd):
        self.execute_command(cmd)

    # new color methods should be moved to the GuakeTerminal class

    def _load_palette(self):
        colorRGBA = Gdk.RGBA(0, 0, 0, 0)
        paletteList = list()
        for color in self.settings.styleFont.get_string("palette").split(':'):
            colorRGBA.parse(color)
            paletteList.append(colorRGBA.copy())
        return paletteList

    def _get_background_color(self, palette_list):
        if len(palette_list) > 16:
            bg_color = palette_list[17]
        else:
            bg_color = Gdk.RGBA(0, 0, 0, 0.9)

        return self._apply_transparency_to_color(bg_color)

    def _apply_transparency_to_color(self, bg_color):
        transparency = self.settings.styleBackground.get_int('transparency')
        if not self.transparency_toggled:
            bg_color.alpha = 1 / 100 * transparency
        else:
            bg_color.alpha = 1
        return bg_color

    def set_background_color_from_settings(self):
        self.set_colors_from_settings()

    def get_bgcolor(self):
        palette_list = self._load_palette()
        return self._get_background_color(palette_list)

    def get_fgcolor(self):
        palette_list = self._load_palette()
        if len(palette_list) > 16:
            font_color = palette_list[16]
        else:
            font_color = Gdk.RGBA(0, 0, 0, 0)
        return font_color

    def set_colors_from_settings(self):
        bg_color = self.get_bgcolor()
        font_color = self.get_fgcolor()
        palette_list = self._load_palette()

        for i in self.notebook.iter_terminals():
            i.set_color_foreground(font_color)
            i.set_color_bold(font_color)
            i.set_colors(font_color, bg_color, palette_list[:16])

    def set_bgcolor(self, bgcolor):
        if isinstance(bgcolor, str):
            c = Gdk.RGBA(0, 0, 0, 0)
            log.debug("Building Gdk Color from: %r", bgcolor)
            c.parse("#" + bgcolor)
            bgcolor = c
        if not isinstance(bgcolor, Gdk.RGBA):
            raise TypeError("color should be Gdk.RGBA, is: {!r}".format(bgcolor))
        bgcolor = self._apply_transparency_to_color(bgcolor)
        log.debug("setting background color to: %r", bgcolor)
        page_num = self.notebook.get_current_page()
        terminal = self.notebook.get_nth_page(page_num).terminal
        terminal.set_color_background(bgcolor)


#        self.notebook.get_current_terminal().set_color_background(bgcolor)

    def set_fgcolor(self, fgcolor):
        if isinstance(fgcolor, str):
            c = Gdk.RGBA(0, 0, 0, 0)
            log.debug("Building Gdk Color from: %r", fgcolor)
            c.parse("#" + fgcolor)
            fgcolor = c
        if not isinstance(fgcolor, Gdk.RGBA):
            raise TypeError("color should be Gdk.RGBA, is: {!r}".format(fgcolor))
        log.debug("setting background color to: %r", fgcolor)
        page_num = self.notebook.get_current_page()
        terminal = self.notebook.get_nth_page(page_num).terminal
        # TODO this should be fgcolor right?
        terminal.set_color_foreground(bgcolor)
        # self.notebook.get_current_terminal().set_color_foreground(fgcolor)

    def execute_command(self, command, tab=None):
        """Execute the `command' in the `tab'. If tab is None, the
        command will be executed in the currently selected
        tab. Command should end with '\n', otherwise it will be
        appended to the string.
        """
        if not self.notebook.has_page():
            self.add_tab()

        if command[-1] != '\n':
            command += '\n'

        index = self.notebook.get_current_page()
        index = tab or self.notebook.get_current_page()
        for terminal in self.notebook.get_terminals_for_page(index):
            terminal.feed_child(command)
            break

    def execute_command_by_uuid(self, tab_uuid, command):
        """Execute the `command' in the tab whose terminal has the `tab_uuid' uuid
        """
        if command[-1] != '\n':
            command += '\n'
        try:
            tab_uuid = uuid.UUID(tab_uuid)
            page_index, = (
                index for index, t in enumerate(self.notebook.iter_terminals())
                if t.get_uuid() == tab_uuid
            )
        except ValueError:
            pass
        else:
            terminals = self.notebook.get_terminals_for_page(page_index)
            for current_vte in terminals:
                current_vte.feed_child(command)

    # TODO this is dead: 2eae380b1a91a24f6c1eb68c13dac33db98a6ea2 and
    # 3f8c344519c9228deb9ca5f181cbdd5ef1d6acc0
    def on_resizer_drag(self, widget, event):
        """Method that handles the resize drag.

        It does not actually move the main window. It just sets the new window size in gconf.
        """

        mod = event.get_state()
        if 'GDK_BUTTON1_MASK' not in mod.value_names:
            return

        screen = self.window.get_screen()
        win, x, y, _ = screen.get_root_window().get_pointer()
        screen_no = screen.get_monitor_at_point(x, y)
        valignment = self.settings.general.get_int('window-valignment')

        max_height = screen.get_monitor_geometry(screen_no).height
        if valignment == ALIGN_BOTTOM:
            percent = 100 * (max_height - y) / max_height
        else:
            percent = 100 * y / max_height

        if percent < 1:
            percent = 1

        window_rect = self.window.get_size()
        window_pos = self.window.get_position()
        if valignment == ALIGN_BOTTOM:
            self.window.resize(window_rect[0], max_height - y)
            log.debug(
                "Resizing on resizer drag to : %r, and moving to: %r, y: %r",
                (window_rect[0], max_height - y), window_pos[0], y
            )
            self.window.move(window_pos[0], y)
        else:
            self.window.resize(window_rect[0], y)
            log.debug("Just moving on resizer drag to: %r, y=%r", window_rect[0], y)
        self.settings.general.set_int('window-height', int(percent))

    def on_window_losefocus(self, window, event):
        """Hides terminal main window when it loses the focus and if
        the window_losefocus gconf variable is True.
        """
        if self.showing_context_menu:
            return

        if self.prompt_dialog is not None:
            return

        if self.preventHide:
            return

        value = self.settings.general.get_boolean('window-losefocus')
        visible = window.get_property('visible')
        self.losefocus_time = get_server_time(self.window)
        if visible and value:
            log.info("Hiding on focus lose")
            self.hide()

    def show_menu(self, status_icon, button, activate_time):
        """Show the tray icon menu.
        """
        menu = self.get_widget('tray-menu')

        menu.popup(None, None, None, Gtk.StatusIcon.position_menu, button, activate_time)

    def show_context_menu(self, terminal, event):
        """Show the context menu, only with a right click on a vte
        Terminal.
        """
        if event.button != 3:
            return False

        if event.get_state() & Gdk.ModifierType.SHIFT_MASK:
            # Force showing contextual menu on Ctrl+right click
            self.showing_context_menu = True
        else:
            # First send to background process if handled, do nothing else
            if Vte.Terminal.do_button_press_event(terminal, event):
                log.info("Background app captured the right click event")
                return True

        log.debug("showing context menu")
        self.showing_context_menu = True

        guake_clipboard = Gtk.Clipboard.get_default(self.window.get_display())
        if not guake_clipboard.wait_is_text_available():
            self.get_widget('context_paste').set_sensitive(False)
        else:
            self.get_widget('context_paste').set_sensitive(True)

        current_selection = ''
        current_term = self.notebook.get_current_terminal()
        if current_term.get_has_selection():
            current_term.copy_clipboard()
            guake_clipboard = Gtk.Clipboard.get_default(self.window.get_display())
            current_selection = guake_clipboard.wait_for_text()
            if current_selection:
                current_selection.rstrip()

            if current_selection and len(current_selection) > 20:
                current_selection = current_selection[:17] + "..."

        self.get_widget('separator_search').set_visible(False)
        if current_selection:
            self.get_widget('context_search_on_web'
                            ).set_label(_("Search on Web: '%s'") % current_selection)
            self.get_widget('context_search_on_web').set_visible(True)
            self.get_widget('separator_search').set_visible(True)
        else:
            self.get_widget('context_search_on_web').set_label(_("Search on Web (no selection)"))
            self.get_widget('context_search_on_web').set_visible(False)

        filename = None
        if current_selection:
            filename = self.get_current_terminal_filename_under_cursor(current_selection)

        if filename:
            self.get_widget('context_quick_open').set_visible(True)
            filename_str = str(filename)
            if len(filename_str) >= 28:
                self.get_widget('context_quick_open'
                                ).set_label(_("Quick Open: {!s}...").format(filename_str[:25]))
            else:
                self.get_widget('context_quick_open'
                                ).set_label(_("Quick Open: {!s}").format(filename_str))
            self.get_widget('separator_search').set_visible(True)
        else:
            self.get_widget('context_quick_open').set_label(_("Quick Open..."))
            self.get_widget('context_quick_open').set_visible(False)

        link = self.get_current_terminal_link_under_cursor()
        if link:
            self.get_widget('context_browse_on_web').set_visible(True)
            if len(link) >= 28:
                self.get_widget('context_browse_on_web'
                                ).set_label(_("Open Link: {!s}...").format(link[:25]))
            else:
                self.get_widget('context_browse_on_web'
                                ).set_label(_("Open Link: {!s}").format(link))
            self.get_widget('separator_search').set_visible(True)
        else:
            self.get_widget('context_browse_on_web').set_label(_("Open Link..."))
            self.get_widget('context_browse_on_web').set_visible(False)

        context_menu = self.get_widget('context-menu')
        context_menu.popup(None, None, None, None, 3, event.get_time())
        return True

    def show_rename_current_tab_dialog(self, target, event):
        """On double-click over a tab, show the rename dialog.
        """
        if event.button == 1:
            if event.type == Gdk.EventType._2BUTTON_PRESS:
                self.accel_rename_current_tab()
                self.set_terminal_focus()
                self.selected_tab.pressed()
                return True

    def show_tab_menu(self, target, event, user_data):
        """Shows the tab menu with a right click. After that, the
        focus come back to the terminal.
        user_data is a Gtk.Label which is displayed in an eventbox in the clicked tab
        """
        if event.button == 3:
            self.tab_context_menu_helper.show(event, self.notebook.find_tab_index_label(user_data))
            self.notebook.get_current_terminal().grab_focus()
            return True
        self.notebook.get_current_terminal().grab_focus()
        return False

    def middle_button_click(self, target, event, user_data):
        """Closes a tab with a middle click
        user_data is a Gtk.Label which is displayed in an eventbox in the clicked tab
        """
        if event.button == 2 and event.type == Gdk.EventType.BUTTON_PRESS:
            self.notebook.delete_page_by_label(user_data)

    def show_about(self, *args):
        """Hides the main window and creates an instance of the About
        Dialog.
        """
        self.hide()
        AboutDialog()

    def show_prefs(self, *args):
        """Hides the main window and creates an instance of the
        Preferences window.
        """
        self.hide()
        PrefsDialog(self.settings).show()

    def is_iconified(self):
        if self.window:
            cur_state = int(self.window.get_state())
            return bool(cur_state & GDK_WINDOW_STATE_ICONIFIED)
        return False

    def window_event(self, window, event):
        state = event.new_window_state
        log.debug("Received window state event: %s", state)

    def show_hide(self, *args):
        """Toggles the main window visibility
        """
        log.debug("Show_hide called")
        if self.forceHide:
            self.forceHide = False
            return

        if self.preventHide:
            return

        if not self.win_prepare():
            return

        if not self.window.get_property('visible'):
            log.info("Showing the terminal")
            self.show()
            self.set_terminal_focus()
            return

        # Disable the focus_if_open feature
        #  - if doesn't work seamlessly on all system
        #  - self.window.window.get_state doesn't provides us the right information on all
        #    systems, especially on MATE/XFCE
        #
        # if self.client.get_bool(KEY('/general/focus_if_open')):
        #     restore_focus = False
        #     if self.window.window:
        #         state = int(self.window.window.get_state())
        #         if ((state & GDK_WINDOW_STATE_STICKY or
        #                 state & GDK_WINDOW_STATE_WITHDRAWN
        #              )):
        #             restore_focus = True
        #     else:
        #         restore_focus = True
        # if not self.hidden:
        # restore_focus = True
        #     if restore_focus:
        #         log.debug("DBG: Restoring the focus to the terminal")
        #         self.hide()
        #         self.show()
        #         self.window.window.focus()
        #         self.set_terminal_focus()
        #         return

        log.info("hiding the terminal")
        self.hide()

    def show_focus(self, *args):
        self.win_prepare()
        self.show()
        self.set_terminal_focus()

    def win_prepare(self, *args):
        event_time = self.hotkeys.get_current_event_time()
        if not self.settings.general.get_boolean('window-refocus') and \
                self.window.get_window() and self.window.get_property('visible'):
            pass
        elif not self.settings.general.get_boolean('window-losefocus'):
            if self.losefocus_time and self.losefocus_time < event_time:
                if self.window.get_window() and self.window.get_property('visible'):
                    log.debug("DBG: Restoring the focus to the terminal")
                    self.window.get_window().focus(event_time)
                    self.set_terminal_focus()
                    self.losefocus_time = 0
                    return False
        elif self.losefocus_time and self.settings.general.get_boolean('window-losefocus'):
            if self.losefocus_time >= event_time and \
                    (self.losefocus_time - event_time) < 10:
                self.losefocus_time = 0
                return False

        # limit rate at which the visibility can be toggled.
        if self.prev_showhide_time and event_time and \
                (event_time - self.prev_showhide_time) < 65:
            return False
        self.prev_showhide_time = event_time

        log.debug("")
        log.debug("=" * 80)
        log.debug("Window display")
        if self.window:
            cur_state = int(self.window.get_state())
            is_sticky = bool(cur_state & GDK_WINDOW_STATE_STICKY)
            is_withdrawn = bool(cur_state & GDK_WINDOW_STATE_WITHDRAWN)
            is_above = bool(cur_state & GDK_WINDOW_STATE_ABOVE)
            is_iconified = self.is_iconified()
            log.debug("gtk.gdk.WindowState = %s", cur_state)
            log.debug("GDK_WINDOW_STATE_STICKY? %s", is_sticky)
            log.debug("GDK_WINDOW_STATE_WITHDRAWN? %s", is_withdrawn)
            log.debug("GDK_WINDOW_STATE_ABOVE? %s", is_above)
            log.debug("GDK_WINDOW_STATE_ICONIFIED? %s", is_iconified)
            return True
        return False

    def show(self):
        """Shows the main window and grabs the focus on it.
        """
        self.hidden = False

        # setting window in all desktops
        window_rect = self.set_final_window_rect()
        self.get_widget('window-root').stick()

        # add tab must be called before window.show to avoid a
        # blank screen before adding the tab.
        if not self.notebook.has_page():
            self.add_tab()

        self.window.set_keep_below(False)
        self.window.show_all()
        # this is needed because self.window.show_all() results in showing every
        # thing which includes the scrollbar too
        self.settings.general.triggerOnChangedValue(self.settings.general, "use-scrollbar")

        # move the window even when in fullscreen-mode
        log.debug("Moving window to: %r", window_rect)
        self.window.move(window_rect.x, window_rect.y)

        # this works around an issue in fluxbox
        if not self.is_fullscreen:
            self.settings.general.triggerOnChangedValue(self.settings.general, 'window-height')

        time = get_server_time(self.window)

        # TODO PORT this
        # When minized, the window manager seems to refuse to resume
        # log.debug("self.window: %s. Dir=%s", type(self.window), dir(self.window))
        # is_iconified = self.is_iconified()
        # if is_iconified:
        #     log.debug("Is iconified. Ubuntu Trick => "
        #               "removing skip_taskbar_hint and skip_pager_hint "
        #               "so deiconify can work!")
        #     self.get_widget('window-root').set_skip_taskbar_hint(False)
        #     self.get_widget('window-root').set_skip_pager_hint(False)
        #     self.get_widget('window-root').set_urgency_hint(False)
        #     log.debug("get_skip_taskbar_hint: {}".format(
        #         self.get_widget('window-root').get_skip_taskbar_hint()))
        #     log.debug("get_skip_pager_hint: {}".format(
        #         self.get_widget('window-root').get_skip_pager_hint()))
        #     log.debug("get_urgency_hint: {}".format(
        #         self.get_widget('window-root').get_urgency_hint()))
        #     glib.timeout_add_seconds(1, lambda: self.timeout_restore(time))
        #

        log.debug("order to present and deiconify")
        self.window.present()
        self.window.deiconify()
        self.window.show()
        self.window.get_window().focus(time)
        self.window.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.window.set_type_hint(Gdk.WindowTypeHint.NORMAL)

        # log.debug("Restoring skip_taskbar_hint and skip_pager_hint")
        # if is_iconified:
        #     self.get_widget('window-root').set_skip_taskbar_hint(False)
        #     self.get_widget('window-root').set_skip_pager_hint(False)
        #     self.get_widget('window-root').set_urgency_hint(False)

        # This is here because vte color configuration works only after the
        # widget is shown.

        self.settings.styleFont.triggerOnChangedValue(self.settings.styleFont, 'color')
        self.settings.styleBackground.triggerOnChangedValue(self.settings.styleBackground, 'color')

        log.debug("Current window position: %r", self.window.get_position())

        self.execute_hook('show')

    def hide_from_remote(self):
        """
        Hides the main window of the terminal and sets the visible
        flag to False.
        """
        log.debug("hide from remote")
        self.forceHide = True
        self.hide()

    def show_from_remote(self):
        """Show the main window of the terminal and sets the visible
        flag to False.
        """
        log.debug("show from remote")
        self.forceHide = True
        self.show()

    def hide(self):
        """Hides the main window of the terminal and sets the visible
        flag to False.
        """
        if self.preventHide:
            return
        self.hidden = True
        self.get_widget('window-root').unstick()
        self.window.hide()  # Don't use hide_all here!

    def get_final_window_monitor(self):
        """Gets the final screen number for the main window of guake.
        """

        screen = self.window.get_screen()

        # fetch settings
        use_mouse = self.settings.general.get_boolean('mouse-display')
        dest_screen = self.settings.general.get_int('display-n')

        if use_mouse:
            """
            TODO this is ported from widget.get_pointer() to
            GdkSeat.get_pointer(), but this whole method could be
            ported to Gdk (eg. gdk_display_get_default_screen(...)
            and gdk-screen-get-n-monitors(...))
            """
            gdk_window = self.window.get_window()
            if gdk_window is not None:
                display = Gdk.Display.get_default()
                seat = display.get_default_seat()
                device = seat.get_pointer()
                win, x, y, _ = gdk_window.get_device_position(device)
                dest_screen = screen.get_monitor_at_point(x, y)

        # If Guake is configured to use a screen that is not currently attached,
        # default to 'primary display' option.
        n_screens = screen.get_n_monitors()
        if dest_screen > n_screens - 1:
            self.settings.general.set_boolean('mouse-display', False)
            self.settings.general.set_int('display-n', dest_screen)
            dest_screen = screen.get_primary_monitor()

        # Use primary display if configured
        if dest_screen == ALWAYS_ON_PRIMARY:
            dest_screen = screen.get_primary_monitor()

        return dest_screen

    # TODO PORT remove this UNITY is DEAD
    def is_using_unity(self):
        linux_distrib = platform.linux_distribution()
        if linux_distrib[0].lower() != "ubuntu":
            return False

        # http://askubuntu.com/questions/70296/is-there-an-environment-variable-that-is-set-for-unity
        if float(linux_distrib[1]) - 0.01 < 11.10:
            if os.environ.get('DESKTOP_SESSION', '').lower() == "gnome".lower():
                return True
        else:
            if os.environ.get('XDG_CURRENT_DESKTOP', '').lower() == "unity".lower():
                return True
        return False

    def set_final_window_rect(self):
        """Sets the final size and location of the main window of guake. The height
        is the window_height property, width is window_width and the
        horizontal alignment is given by window_alignment.
        """

        # fetch settings
        height_percents = self.settings.general.get_int('window-height')

        width_percents = self.settings.general.get_int('window-width')
        halignment = self.settings.general.get_int('window-halignment')
        valignment = self.settings.general.get_int('window-valignment')

        vdisplacement = self.settings.general.get_int('window-vertical-displacement')
        hdisplacement = self.settings.general.get_int('window-horizontal-displacement')

        log.debug("set_final_window_rect")
        log.debug("  height_percents = %s", height_percents)
        log.debug("  width_percents = %s", width_percents)
        log.debug("  halignment = %s", halignment)
        log.debug("  valignment = %s", valignment)
        log.debug("  vdisplacement = %s", vdisplacement)
        log.debug("  hdisplacement = %s", hdisplacement)

        # get the rectangle just from the destination monitor
        screen = self.window.get_screen()
        monitor = self.get_final_window_monitor()
        window_rect = screen.get_monitor_geometry(monitor)
        log.debug("Current monitor geometry")
        log.debug("  window_rect.x: %s", window_rect.x)
        log.debug("  window_rect.y: %s", window_rect.y)
        log.debug("  window_rect.height: %s", window_rect.height)
        log.debug("  window_rect.width: %s", window_rect.width)
        log.debug("is unity: %s", self.is_using_unity())

        # TODO PORT remove this UNITY is DEAD
        if self.is_using_unity():

            # For Ubuntu 12.10 and above, try to use dconf:
            # see if unity dock is hidden => unity_hide
            # and the width of unity dock => unity_dock
            # and the position of the unity dock. => unity_pos
            # found = False
            unity_hide = 0
            unity_dock = 0
            unity_pos = "Left"
            # float() conversion might mess things up. Add 0.01 so the comparison will always be
            # valid, even in case of float("10.10") = 10.099999999999999
            if float(platform.linux_distribution()[1]) + 0.01 >= 12.10:
                try:
                    unity_hide = int(
                        subprocess.check_output([
                            '/usr/bin/dconf', 'read',
                            '/org/compiz/profiles/unity/plugins/unityshell/launcher-hide-mode'
                        ])
                    )
                    unity_dock = int(
                        subprocess.check_output([
                            '/usr/bin/dconf', 'read',
                            '/org/compiz/profiles/unity/plugins/unityshell/icon-size'
                        ]) or "48"
                    )
                    unity_pos = subprocess.check_output([
                        '/usr/bin/dconf', 'read', '/com/canonical/unity/launcher/launcher-position'
                    ]) or "Left"
                    # found = True
                except Exception as e:
                    # in case of error, just ignore it, 'found' will not be set to True and so
                    # we execute the fallback
                    pass
            # FIXME: remove self.client dependency
            # if not found:
            #     # Fallback: try to bet from gconf
            #     unity_hide = self.client.get_int(
            #         KEY('/apps/compiz-1/plugins/unityshell/screen0/options/launcher_hide_mode')
            #     )
            #     unity_icon_size = self.client.get_int(
            #         KEY('/apps/compiz-1/plugins/unityshell/screen0/options/icon_size')
            #     )
            #     unity_dock = unity_icon_size + 17

            # launcher_hide_mode = 1 => autohide
            # only adjust guake window width if Unity dock is positioned "Left" or "Right"
            if unity_hide != 1 and unity_pos not in ("Left", "Right"):
                log.debug(
                    "correcting window width because of launcher position %s "
                    "and width %s (from %s to %s)", unity_pos, unity_dock, window_rect.width,
                    window_rect.width - unity_dock
                )

                window_rect.width = window_rect.width - unity_dock

        total_width = window_rect.width
        total_height = window_rect.height

        log.debug("Correcteed monitor size:")
        log.debug("  total_width: %s", total_width)
        log.debug("  total_height: %s", total_height)

        window_rect.height = int(float(window_rect.height) * float(height_percents) / 100.0)
        window_rect.width = int(float(window_rect.width) * float(width_percents) / 100.0)

        if window_rect.width < total_width:
            if halignment == ALIGN_CENTER:
                # log.debug("aligning to center!")
                window_rect.x += (total_width - window_rect.width) / 2
            elif halignment == ALIGN_LEFT:
                # log.debug("aligning to left!")
                window_rect.x += 0 + hdisplacement
            elif halignment == ALIGN_RIGHT:
                # log.debug("aligning to right!")
                window_rect.x += total_width - window_rect.width - hdisplacement
        if window_rect.height < total_height:
            if valignment == ALIGN_BOTTOM:
                window_rect.y += (total_height - window_rect.height)

        if valignment == ALIGN_TOP:
            window_rect.y += vdisplacement
        elif valignment == ALIGN_BOTTOM:
            window_rect.y -= vdisplacement

        if width_percents == 100 and height_percents == 100:
            log.debug("MAXIMIZING MAIN WINDOW")
            self.window.maximize()
        elif not self.is_fullscreen:
            log.debug("RESIZING MAIN WINDOW TO THE FOLLOWING VALUES:")
            self.window.unmaximize()
            log.debug("  window_rect.x: %s", window_rect.x)
            log.debug("  window_rect.y: %s", window_rect.y)
            log.debug("  window_rect.height: %s", window_rect.height)
            log.debug("  window_rect.width: %s", window_rect.width)
            # Note: move_resize is only on GTK3
            self.window.resize(window_rect.width, window_rect.height)
            self.window.move(window_rect.x, window_rect.y)
            self.window.move(window_rect.x, window_rect.y)
            log.debug("Updated window position: %r", self.window.get_position())

        return window_rect

    def force_move_if_shown(self):
        if not self.hidden:
            # when displayed, GTK might refuse to move the window (X or Y position). Just hide and
            # redisplay it so the final position is correct
            log.debug("FORCING HIDE")
            self.hide()
            log.debug("FORCING SHOW")
            self.show()

    # -- configuration --

    def load_config(self):
        """"Just a proxy for all the configuration stuff.
        """

        self.settings.general.triggerOnChangedValue(self.settings.general, 'use-trayicon')
        self.settings.general.triggerOnChangedValue(self.settings.general, 'prompt-on-quit')
        self.settings.general.triggerOnChangedValue(self.settings.general, 'prompt-on-close-tab')
        self.settings.general.triggerOnChangedValue(self.settings.general, 'window-tabbar')
        self.settings.general.triggerOnChangedValue(self.settings.general, 'mouse-display')
        self.settings.general.triggerOnChangedValue(self.settings.general, 'display-n')
        self.settings.general.triggerOnChangedValue(self.settings.general, 'window-ontop')
        if not self.is_fullscreen:
            self.settings.general.triggerOnChangedValue(self.settings.general, 'window-height')
            self.settings.general.triggerOnChangedValue(self.settings.general, 'window-width')
        self.settings.general.triggerOnChangedValue(self.settings.general, 'use-scrollbar')
        self.settings.general.triggerOnChangedValue(self.settings.general, 'history-size')
        self.settings.general.triggerOnChangedValue(self.settings.general, 'infinite-history')
        self.settings.general.triggerOnChangedValue(self.settings.general, 'use-vte-titles')
        self.settings.general.triggerOnChangedValue(self.settings.general, 'set-window-title')
        self.settings.general.triggerOnChangedValue(self.settings.general, 'abbreviate-tab-names')
        self.settings.general.triggerOnChangedValue(self.settings.general, 'max-tab-name-length')
        self.settings.general.triggerOnChangedValue(self.settings.general, 'quick-open-enable')
        self.settings.general.triggerOnChangedValue(
            self.settings.general, 'quick-open-command-line'
        )
        self.settings.style.triggerOnChangedValue(self.settings.style, 'cursor-shape')
        self.settings.styleFont.triggerOnChangedValue(self.settings.styleFont, 'style')
        self.settings.styleFont.triggerOnChangedValue(self.settings.styleFont, 'palette')
        self.settings.styleFont.triggerOnChangedValue(self.settings.styleFont, 'palette-name')
        self.settings.styleFont.triggerOnChangedValue(self.settings.styleFont, 'allow-bold')
        self.settings.styleBackground.triggerOnChangedValue(
            self.settings.styleBackground, 'transparency'
        )
        self.settings.general.triggerOnChangedValue(self.settings.general, 'use-default-font')
        self.settings.general.triggerOnChangedValue(self.settings.general, 'compat-backspace')
        self.settings.general.triggerOnChangedValue(self.settings.general, 'compat-delete')

    def run_quit_dialog(self, procs, tab):
        """Run the "are you sure" dialog for closing a tab, or quitting Guake
        """
        # Stop an open "close tab" dialog from obstructing a quit
        if self.prompt_dialog is not None:
            self.prompt_dialog.destroy()
        self.prompt_dialog = PromptQuitDialog(self.window, procs, tab)
        response = self.prompt_dialog.run() == Gtk.ResponseType.YES
        self.prompt_dialog.destroy()
        self.prompt_dialog = None
        # Keep Guake focussed after dismissing tab-close prompt
        if tab == -1:
            self.window.present()
        return response

    def accel_quit(self, *args):
        """Callback to prompt the user whether to quit Guake or not.
        """
        procs = self.notebook.get_running_fg_processes_count()
        tabs = self.notebook.get_n_pages()
        prompt_cfg = self.settings.general.get_boolean('prompt-on-quit')
        prompt_tab_cfg = self.settings.general.get_int('prompt-on-close-tab')
        # "Prompt on tab close" config overrides "prompt on quit" config
        if prompt_cfg or (prompt_tab_cfg == 1 and procs > 0) or (prompt_tab_cfg == 2):
            log.debug("Remaining procs=%r", procs)
            if self.run_quit_dialog(procs, tabs):
                log.info("Quitting Guake")
                Gtk.main_quit()
        else:
            log.info("Quitting Guake")
            Gtk.main_quit()

    def accel_reset_terminal(self, *args):
        """Callback to reset and clean the terminal"""
        self.reset_terminal()
        return True

    def accel_zoom_in(self, *args):
        """Callback to zoom in.
        """
        for term in self.notebook.iter_terminals():
            term.increase_font_size()
        return True

    def accel_zoom_out(self, *args):
        """Callback to zoom out.
        """
        for term in self.notebook.iter_terminals():
            term.decrease_font_size()
        return True

    def accel_increase_height(self, *args):
        """Callback to increase height.
        """
        height = self.settings.general.get_int('window-height')
        self.settings.general.set_int('window-height', min(height + 2, 100))
        return True

    def accel_decrease_height(self, *args):
        """Callback to decrease height.
        """
        height = self.settings.general.get_int('window-height')
        self.settings.general.set_int('window-height', max(height - 2, 0))
        return True

    def accel_increase_transparency(self, *args):
        """Callback to increase transparency.
        """
        transparency = self.settings.styleBackground.get_int('transparency')
        if int(transparency) - 2 > 0:
            self.settings.styleBackground.set_int('transparency', int(transparency) - 2)
        return True

    def accel_decrease_transparency(self, *args):
        """Callback to decrease transparency.
        """
        transparency = self.settings.styleBackground.get_int('transparency')
        if int(transparency) + 2 < MAX_TRANSPARENCY:
            self.settings.styleBackground.set_int('transparency', int(transparency) + 2)
        return True

    def accel_toggle_transparency(self, *args):
        """Callback to toggle transparency.
        """
        self.transparency_toggled = not self.transparency_toggled
        self.settings.styleBackground.triggerOnChangedValue(
            self.settings.styleBackground, 'transparency'
        )
        return True

    def accel_add(self, *args):
        """Callback to add a new tab. Called by the accel key.
        """
        self.add_tab()
        return True

    def accel_prev(self, *args):
        """Callback to go to the previous tab. Called by the accel key.
        """
        if self.notebook.get_current_page() == 0:
            self.notebook.set_current_page(self.notebook.get_n_pages() - 1)
        else:
            self.notebook.prev_page()
        return True

    def accel_next(self, *args):
        """Callback to go to the next tab. Called by the accel key.
        """
        if self.notebook.get_current_page() + 1 == self.notebook.get_n_pages():
            self.notebook.set_current_page(0)
        else:
            self.notebook.next_page()
        return True

    def accel_move_tab_left(self, *args):
        """ Callback to move a tab to the left """
        pos = self.notebook.get_current_page()
        if pos != 0:
            self.move_tab(pos, pos - 1)
        return True

    def accel_move_tab_right(self, *args):
        """ Callback to move a tab to the right """
        pos = self.notebook.get_current_page()
        if pos != self.notebook.get_n_pages() - 1:
            self.move_tab(pos, pos + 1)
        return True

    def gen_accel_switch_tabN(self, N):
        """Generates callback (which called by accel key) to go to the Nth tab.
        """

        def callback(*args):
            if 0 <= N < self.notebook.get_n_pages():
                self.notebook.set_current_page(N)
            return True

        return callback

    def accel_switch_tab_last(self, *args):
        last_tab = self.notebook.get_n_pages() - 1
        self.notebook.set_current_page(last_tab)
        return True

    def accel_rename_current_tab(self, *args):
        """Callback to show the rename tab dialog. Called by the accel
        key.
        """
        self.on_rename_current_tab_activate(args)
        return True

    def accel_copy_clipboard(self, *args):
        """Callback to copy text in the shown terminal. Called by the
        accel key.
        """
        self.notebook.get_current_terminal().copy_clipboard()

        return True

    def accel_paste_clipboard(self, *args):
        """Callback to paste text in the shown terminal. Called by the
        accel key.
        """
        self.notebook.get_current_terminal().paste_clipboard()
        return True

    def accel_toggle_fullscreen(self, *args):
        """Callback toggle the fullscreen status of the main
        window. Called by the accel key.
        """

        if not self.is_fullscreen:
            self.fullscreen()
        else:
            self.unfullscreen()
        return True

    def accel_toggle_hide_on_lose_focus(self, *args):
        """Callback toggle whether the window should hide when it loses
        focus. Called by the accel key.
        """

        if self.settings.general.get_boolean('window-losefocus'):
            self.settings.general.set_boolean('window-losefocus', False)
        else:
            self.settings.general.set_boolean('window-losefocus', True)
        return True

    def fullscreen(self):
        log.debug("FULLSCREEN: ON")
        self.window.fullscreen()
        self.is_fullscreen = True

        if not self.settings.general.get_boolean('toolbar-visible-in-fullscreen'):
            self.toolbar.hide()

    def unfullscreen(self):

        # Fixes "Guake cannot restore from fullscreen" (#628)
        log.debug("UNMAXIMIZING")
        self.window.unmaximize()

        self.set_final_window_rect()
        log.debug("FULLSCREEN: OFF")
        self.window.unfullscreen()
        self.is_fullscreen = False

        # making sure that tabbar will come back to default state.
        self.settings.general.triggerOnChangedValue(self.settings.general, 'window-tabbar')

        # make sure the window size is correct after returning
        # from fullscreen. broken on old compiz/metacity versions :C
        self.settings.general.triggerOnChangedValue(self.settings.general, 'window-height')

    # -- callbacks --

    def on_terminal_exited(self, term, status, term1):
        """When a terminal is closed, shell process should be killed,
        this is the method that does that, or, at least calls
        `delete_tab' method to do the work.
        """
        log.debug("Terminal exited: %s", term)
        if libutempter is not None:
            libutempter.utempter_remove_record(term.get_pty())
        self.delete_tab(self.notebook.find_page_index_for_terminal(term), kill=False, prompt=False)

    def recompute_tabs_titles(self):
        """Updates labels on all tabs. This is required when `self.abbreviate`
        changes
        """
        use_vte_titles = self.settings.general.get_boolean("use-vte-titles")
        if not use_vte_titles:
            return

        # TODO NOTEBOOK this code only works if there is only one terminal in a
        # page, this need to be rewritten
        for terminal in self.notebook.iter_terminals():
            page_num = self.notebook.page_num(terminal.get_parent())
            self.rename_tab(page_num, self.compute_tab_title(terminal), False)

    def compute_tab_title(self, vte):
        """Abbreviate and cut vte terminal title when necessary
        """
        vte_title = vte.get_window_title() or _("Terminal")
        try:
            current_directory = vte.get_current_directory()
            if self.abbreviate and vte_title.endswith(current_directory):
                parts = current_directory.split('/')
                parts = [s[:1] for s in parts[:-1]] + [parts[-1]]
                vte_title = vte_title[:len(vte_title) - len(current_directory)] + '/'.join(parts)
        except OSError:
            pass
        return self._shorten_tab_title(vte_title)

    def _shorten_tab_title(self, text):
        use_vte_titles = self.settings.general.get_boolean('use-vte-titles')
        if not use_vte_titles:
            return text
        max_name_length = self.settings.general.get_int("max-tab-name-length")
        if max_name_length != 0 and len(text) > max_name_length:
            text = "..." + text[-max_name_length:]
        return text

    def on_terminal_title_changed(self, vte, term):
        box = term.get_parent()
        use_vte_titles = self.settings.general.get_boolean('use-vte-titles')
        if not use_vte_titles:
            return
        page_num = self.notebook.page_num(box)
        # if tab has been renamed by user, don't override.
        if not getattr(box, 'custom_label_set', False):
            title = self.compute_tab_title(vte)
            self.rename_tab(page_num, title, False)
            self.update_window_title(title)
        else:
            text = self.notebook.get_tab_text_page(page)
            if text:
                self.update_window_title(text)

    def update_window_title(self, title):
        if self.settings.general.get_boolean('set-window-title') is True:
            self.window.set_title(title)
        else:
            self.window.set_title(self.default_window_title)

    def on_rename_current_tab_activate(self, *args):
        """Shows a dialog to rename the current tab.
        """
        print(args)
        entry = Gtk.Entry()
        page_num = self.tab_context_menu_helper.last_invoked_on_tab_index
        page = self.notebook.get_nth_page(page_num)
        entry.set_text(self.notebook.get_tab_label(page).get_children()[0].get_text())
        entry.set_property('can-default', True)
        entry.show()

        vbox = Gtk.VBox()
        vbox.set_border_width(6)
        vbox.show()

        dialog = Gtk.Dialog(
            _("Rename tab"), self.window,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT, Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT)
        )

        dialog.set_size_request(300, -1)
        dialog.vbox.pack_start(vbox, True, True, 0)
        dialog.set_border_width(4)
        dialog.set_default_response(Gtk.ResponseType.ACCEPT)
        dialog.add_action_widget(entry, Gtk.ResponseType.ACCEPT)
        entry.reparent(vbox)

        # don't hide on lose focus until the rename is finished
        self.preventHide = True
        response = dialog.run()
        self.preventHide = False

        if response == Gtk.ResponseType.ACCEPT:
            new_text = entry.get_text()
            new_text = self._shorten_tab_title(new_text)

            self.rename_tab(page_num, new_text, True)

        dialog.destroy()
        self.set_terminal_focus()

    def on_close_activate(self, *args):
        """Tab context menu close handler
        """
        page_num = self.tab_context_menu_helper.last_invoked_on_tab_index
        self.notebook.delete_page(page_num)

    def on_drag_data_received(self, widget, context, x, y, selection, target, timestamp, term):
        box = term.get_parent()
        droppeduris = selection.get_uris()

        # url-unquote the list, strip file:// schemes, handle .desktop-s
        pathlist = []
        app = None
        for uri in droppeduris:
            scheme, _, path, _, _ = urlsplit(uri)

            if scheme != "file":
                pathlist.append(uri)
            else:
                filename = url2pathname(path)

                desktopentry = DesktopEntry()
                try:
                    desktopentry.parse(filename)
                except xdg.Exceptions.ParsingError:
                    pathlist.append(filename)
                    continue

                if desktopentry.getType() == 'Link':
                    pathlist.append(desktopentry.getURL())

                if desktopentry.getType() == 'Application':
                    app = desktopentry.getExec()

        if app and len(droppeduris) == 1:
            text = app
        else:
            text = str.join("", (shell_quote(path) + " " for path in pathlist))

        box.terminal.feed_child(text)
        return True

    # -- tab related functions --

    def close_tab(self, *args):
        """Closes the current tab.
        """
        page_num = self.notebook.get_current_page()
        self.delete_page(page_num)

    def rename_tab_uuid(self, term_uuid, new_text, user_set=True):
        """Rename an already added tab by its UUID
        """
        term_uuid = uuid.UUID(term_uuid)
        # TODO NOTEBOOK this is not optimal (page reordering messes the lookup up)
        # and should be fixed in the notebook rewrite
        page_index, = (
            index for index, t in enumerate(self.notebook.iter_terminals())
            if t.get_uuid() == term_uuid
        )
        self.rename_tab(tab_index, new_text, user_set)

    def rename_tab(self, page_index, new_text, user_set=False):
        """Rename an already added tab by its index. Use user_set to define
        if the rename was triggered by the user (eg. rename dialog) or by
        an update from the vte (eg. vte:window-title-changed)
        """
        page_box = self.notebook.get_nth_page(page_index)
        if not getattr(page_box, "custom_label_set", False) or user_set:
            eventbox = Gtk.EventBox()
            label = Gtk.Label(new_text)
            eventbox.add(label)
            eventbox.connect("button-press-event", self.show_tab_menu, label)
            eventbox.connect("button-press-event", self.middle_button_click, label)
            self.notebook.set_tab_label(page_box, eventbox)
            label.show()

            if user_set:
                setattr(page_box, "custom_label_set", new_text != "-")

    def rename_current_tab(self, new_text, user_set=False):
        page_num = self.notebook.get_current_page()
        self.rename_tab(page_num, new_text, user_set)

    def get_current_dir(self):
        """Gets the working directory of the current tab to create a
        new one in the same dir.
        """
        active_terminal = self.notebook.get_current_terminal()
        if not active_terminal:
            return os.path.expanduser('~')
        return active_terminal.get_current_directory()

    def spawn_sync_pid(self, directory=None, terminal=None):

        argv = list()
        user_shell = self.settings.general.get_string('default-shell')
        if user_shell and os.path.exists(user_shell):
            argv.append(user_shell)
        else:
            argv.append(os.environ['SHELL'])

        login_shell = self.settings.general.get_boolean('use-login-shell')
        if login_shell:
            argv.append('--login')

        # We can choose the directory to vte launch. It is important
        # to be used by dbus interface. I'm testing if directory is a
        # string because when binded to a signal, the first param can
        # be a button not a directory.

        if isinstance(directory, str):
            wd = directory
        else:
            wd = os.environ['HOME']
            try:
                if self.settings.general.get_boolean('open-tab-cwd'):
                    wd = self.get_current_dir()
            except:  # pylint: disable=bare-except
                pass

        # Environment variables are not actually parameters but they
        # need to be set before calling terminal.fork_command()
        # method. This is a good place to do it.
        self.update_proxy_vars(terminal)
        pid = terminal.spawn_sync(
            Vte.PtyFlags.DEFAULT, wd, argv, [], GLib.SpawnFlags.DO_NOT_REAP_CHILD, None, None, None
        )
        try:
            tuple_type = gi._gi.ResultTuple  # pylint: disable=c-extension-no-member
        except:  # pylint: disable=bare-except
            tuple_type = tuple
        if isinstance(pid, (tuple, tuple_type)):
            # Return a tuple in 2.91
            # https://lazka.github.io/pgi-docs/Vte-2.91/classes/Terminal.html#Vte.Terminal.spawn_sync
            pid = pid[1]
        assert isinstance(pid, int)
        return pid

    def update_proxy_vars(self, terminal=None):
        """This method updates http{s,}_proxy environment variables
        with values found in gconf.
        """
        if terminal:
            os.environ['GUAKE_TAB_UUID'] = str(terminal.get_uuid())
        else:
            del os.environ['GUAKE_TAB_UUID']
        return
        # TODO PORT port this code
        proxy = '/system/http_proxy/'
        if self.client.get_boolen(proxy + 'use_http_proxy'):
            host = self.client.get_string(proxy + 'host')
            port = self.client.get_int(proxy + 'port')
            if self.client.get_bool(proxy + 'use_same_proxy'):
                ssl_host = host
                ssl_port = port
            else:
                ssl_host = self.client.get_string('/system/proxy/secure_host')
                ssl_port = self.client.get_int('/system/proxy/secure_port')

            if self.client.get_bool(proxy + 'use_authentication'):
                auth_user = self.client.get_string(proxy + 'authentication_user')
                auth_pass = self.client.get_string(proxy + 'authentication_password')
                auth_pass = quote_plus(auth_pass, '')
                os.environ[
                    'http_proxy'
                ] = "http://{!s}:{!s}@{!s}:{:d}".format(auth_user, auth_pass, host, port)
                os.environ[
                    'https_proxy'
                ] = "http://{!s}:{!s}@{!s}:{:d}".format(auth_user, auth_pass, ssl_host, ssl_port)
            else:
                os.environ['http_proxy'] = "http://{!s}:{:d}".format(host, port)
                os.environ['https_proxy'] = "http://{!s}:{:d}".format(ssl_host, ssl_port)

    def setup_new_terminal(self, directory=None):
        terminal = GuakeTerminal(self)
        terminal.grab_focus()

        terminal.connect('button-press-event', self.show_context_menu)
        terminal.connect('child-exited', self.on_terminal_exited, terminal)
        terminal.connect('window-title-changed', self.on_terminal_title_changed, terminal)
        terminal.connect('drag-data-received', self.on_drag_data_received, terminal)

        # TODO PORT is this still the case with the newer vte version?
        # -- Ubuntu has a patch to libvte which disables mouse scrolling in apps
        # -- like vim and less by default. If this is the case, enable it back.
        if hasattr(terminal, "set_alternate_screen_scroll"):
            terminal.set_alternate_screen_scroll(True)

        pid = self.spawn_sync_pid(directory, terminal)

        if libutempter is not None:
            libutempter.utempter_add_record(terminal.get_pty().get_fd(), os.uname()[1])
        terminal.pid = pid
        return terminal

    def add_tab(self, directory=None):
        """Adds a new tab to the terminal notebook.
        """
        # TODO NOTEBOOK

        box, page_num = self.notebook.new_page()
        text = self.compute_tab_title(box.get_terminals()[0])
        self.notebook.set_current_page(page_num)
        self.rename_tab(page_num, text, False)
        self.load_config()

        if self.is_fullscreen:
            self.fullscreen()
        return str(box.get_terminals()[0].get_uuid())

    def save_tab(self, directory=None):
        self.preventHide = True
        current_term = self.notebook.get_current_terminal()
        current_term.select_all()
        current_term.copy_clipboard()
        current_term.unselect_all()
        guake_clipboard = Gtk.Clipboard.get_default(self.window.get_display())
        current_selection = guake_clipboard.wait_for_text()
        if not current_selection:
            return
        current_selection = current_selection.rstrip()

        dialog = Gtk.FileChooserDialog(
            _("Save to..."), self.window, Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        )
        dialog.set_default_response(Gtk.ResponseType.OK)
        filter = Gtk.FileFilter()
        filter.set_name(_("All files"))
        filter.add_pattern("*")
        dialog.add_filter(filter)

        filter = Gtk.FileFilter()
        filter.set_name(_("Text and Logs"))
        filter.add_pattern("*.log")
        filter.add_pattern("*.txt")
        dialog.add_filter(filter)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            with open(filename, "w") as f:
                f.write(current_selection)
        dialog.destroy()
        self.preventHide = False

    def find_tab(self, directory=None):
        log.debug("find")
        # TODO SEARCH
        self.preventHide = True
        search_text = Gtk.TextView()

        dialog = Gtk.Dialog(
            _("Find"), self.window, Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (
                _("Forward"), RESPONSE_FORWARD, _("Backward"), RESPONSE_BACKWARD, Gtk.STOCK_CANCEL,
                Gtk.ResponseType.NONE
            )
        )
        dialog.vbox.pack_end(search_text, True, True, 0)
        dialog.buffer = search_text.get_buffer()
        dialog.connect("response", self._dialog_response_callback)

        search_text.show()
        search_text.grab_focus()
        dialog.show_all()
        # Note: beware to reset preventHide when closing the find dialog

    def _dialog_response_callback(self, dialog, response_id):
        if response_id not in (RESPONSE_FORWARD, RESPONSE_BACKWARD):
            dialog.destroy()
            self.preventHide = False
            return

        start, end = dialog.buffer.get_bounds()
        search_string = start.get_text(end)

        log.debug(
            "Searching for %r %s\n", search_string, "forward"
            if response_id == RESPONSE_FORWARD else "backward"
        )

        current_term = self.notebook.get_current_terminal()
        log.debug("type: %r", type(current_term))
        log.debug("dir: %r", dir(current_term))
        current_term.search_set_gregex()
        current_term.search_get_gregex()

        # buffer = self.text_view.get_buffer()
        # if response_id == RESPONSE_FORWARD:
        #     buffer.search_forward(search_string, self)
        # elif response_id == RESPONSE_BACKWARD:
        #     buffer.search_backward(search_string, self)

    def delete_tab(self, page_num, kill=True, prompt=True):
        """This function will destroy the notebook page, terminal and
        tab widgets and will call the function to kill interpreter
        forked by vte.
        """
        # Run prompt if necessary
        if prompt:
            procs = self.notebook.get_running_fg_processes_count_page(page_num)
            prompt_cfg = self.settings.general.get_int('prompt-on-close-tab')
            if (prompt_cfg == 1 and procs > 0) or (prompt_cfg == 2):
                if not self.run_quit_dialog(procs, -1):
                    return

        self.notebook.delete_page(page_num, kill=kill)

        if not self.notebook.has_page():
            self.hide()
            # avoiding the delay on next Guake show request
            self.add_tab()
        else:
            self.set_terminal_focus()

        self.was_deleted_tab = True
        abbreviate_tab_names = self.settings.general.get_boolean('abbreviate-tab-names')
        if abbreviate_tab_names:
            self.abbreviate = False
            self.recompute_tabs_titles()

    def set_terminal_focus(self):
        """Grabs the focus on the current tab.
        """
        self.notebook.set_current_page(self.notebook.get_current_page())

    def get_selected_uuidtab(self):
        """Returns the uuid of the current selected terminal
        """
        page_num = self.notebook.get_current_page()
        terminals = self.notebook.get_terminals_for_page(page_num)
        return str(terminals[0].get_uuid())

    def search_on_web(self, *args):
        """Search for the selected text on the web
        """
        current_term = self.notebook.get_current_terminal()

        if current_term.get_has_selection():
            current_term.copy_clipboard()
            guake_clipboard = Gtk.Clipboard.get_default(self.window.get_display())
            search_query = guake_clipboard.wait_for_text()
            search_query = quote_plus(search_query)
            if search_query:
                search_url = "https://www.google.com/#q={!s}&safe=off".format(search_query, )
                Gtk.show_uri(self.window.get_screen(), search_url, get_server_time(self.window))
        return True

    def quick_open(self, *args):
        """Open open selection
        """
        current_term = self.notebook.get_current_terminal()

        if current_term.get_has_selection():
            self.notebook.get_current_terminal().quick_open()
        return True

    def get_current_terminal_link_under_cursor(self):
        current_term = self.notebook.get_current_terminal()
        link = current_term.found_link
        log.debug("Current link under cursor: %s", link)
        if link:
            return link
        return None

    def get_current_terminal_filename_under_cursor(self, selected_text):
        current_term = self.notebook.get_current_terminal()
        filename, _1, _2 = current_term.is_file_on_local_server(selected_text)
        log.info("Current filename under cursor: %s", filename)
        if filename:
            return filename
        return None

    def browse_on_web(self, *args):
        log.debug("browsing %s...", self.get_current_terminal_link_under_cursor())
        self.notebook.get_current_terminal().browse_link_under_cursor()

    def set_tab_position(self, *args):
        if self.settings.general.get_boolean('tab-ontop'):
            self.notebook.set_tab_pos(Gtk.PositionType.TOP)
        else:
            self.notebook.set_tab_pos(Gtk.PositionType.BOTTOM)

    def reset_terminal(self, directory=None):
        self.preventHide = True
        current_term = self.notebook.get_current_terminal()
        current_term.reset(True, True)
        self.preventHide = False

    def execute_hook(self, event_name):
        """Execute shell commands related to current event_name"""
        hook = self.settings.hooks.get_string('{!s}'.format(event_name))
        if hook is not None and hook != "":
            hook = hook.split()
            try:
                subprocess.Popen(hook)
            except OSError as oserr:
                if oserr.errno == 8:
                    log.error("Hook execution failed! Check shebang at first line of %s!", hook)
                    log.debug(traceback.format_exc())
                else:
                    log.error(str(oserr))
            except Exception as e:
                log.error("hook execution failed! %s", e)
                log.debug(traceback.format_exc())
            else:
                log.debug("hook on event %s has been executed", event_name)


class TabContextMenuHelper():

    def __init__(self, menu):
        self.menu = menu
        self.menu.connect('hide', self._hide)
        self.reset()

    def reset(self):
        self.is_showing = False
        self.last_invoked_on_tab_index = -1

    def show(self, event, invoked_on_tab_index):
        self.is_showing = True
        self.last_invoked_on_tab_index = invoked_on_tab_index
        self.menu.popup_at_pointer(event)

    def _hide(self, *args):
        self.is_showing = False

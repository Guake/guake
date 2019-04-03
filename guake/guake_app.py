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

from guake import notifier
from guake.about import AboutDialog
from guake.common import gladefile
from guake.common import pixmapfile
from guake.globals import ALIGN_BOTTOM
from guake.globals import ALIGN_CENTER
from guake.globals import ALIGN_LEFT
from guake.globals import ALIGN_RIGHT
from guake.globals import ALIGN_TOP
from guake.globals import ALWAYS_ON_PRIMARY
from guake.globals import LOCALE_DIR
from guake.globals import NAME
from guake.globals import SCHEMA_DIR
from guake.globals import _
from guake.gsettings import GSettingHandler
from guake.guake_logging import setupLogging
from guake.guake_notebook import GuakeNotebook
from guake.keybindings import Keybindings
from guake.prefs import PrefsDialog
from guake.settings import Settings
from guake.simplegladeapp import SimpleGladeApp
from guake.simplegladeapp import bindtextdomain
from guake.terminal import GuakeTerminalBox
from guake.utils import get_server_time

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
    sys.stderr.write("[WARN] Unable to load the library libutempter !\n")
    sys.stderr.write("[WARN] The <wall> command will not work in guake !\n")
    sys.stderr.write("[WARN] " + str(e) + '\n')

log = logging.getLogger(__name__)

instance = None
RESPONSE_FORWARD = 0
RESPONSE_BACKWARD = 1

# Disable find feature until python-vte hasn't been updated
enable_find = False

GObject.threads_init()

# Loading translation
bindtextdomain(NAME, LOCALE_DIR)

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
        super(Guake, self).__init__(gladefile('guake.glade'))

        self.add_callbacks(self)

        schema_source = Gio.SettingsSchemaSource.new_from_directory(
            SCHEMA_DIR, Gio.SettingsSchemaSource.get_default(), False
        )

        self.settings = Settings(schema_source)
        self.debug_mode = self.settings.general.get_boolean('debug-mode')
        setupLogging(self.debug_mode)

        self._select_gtk_theme()

        # Cannot use "getattr(gtk.Window().get_style(), "base")[int(gtk.STATE_SELECTED)]"
        # since theme has not been applied before first show_all
        self.selected_color = None

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

        ipath = pixmapfile('add_tab.png')
        self.get_widget('image2').set_from_file(ipath)

        # important widgets
        self.window = self.get_widget('window-root')
        self.window.set_keep_above(True)
        self.mainframe = self.get_widget('mainframe')
        self.mainframe.remove(self.get_widget('notebook-teminals'))
        self.notebook = GuakeNotebook()
        self.notebook.set_name("notebook-teminals")

        # help(Gtk.PositionType)
        self.notebook.set_tab_pos(Gtk.PositionType.BOTTOM)
        # self.notebook.set_property("tab_pos", "bottom")
        self.notebook.set_property("show_tabs", False)
        self.notebook.set_property("show_border", False)
        self.notebook.set_property("visible", True)
        self.notebook.set_property("has_focus", True)
        self.notebook.set_property("can_focus", True)
        self.notebook.set_property("is_focus", True)
        self.notebook.set_property("enable_popup", True)
        self.notebook.set_property("expand", True)
        self.notebook.connect("switch_page", self.select_current_tab)
        self.mainframe.add(self.notebook)
        self.set_tab_position()

        self.tabs = self.get_widget('hbox-tabs')
        self.toolbar = self.get_widget('toolbar')
        self.mainframe = self.get_widget('mainframe')

        # check and set ARGB for real transparency
        color = self.window.get_style_context().get_background_color(Gtk.StateFlags.NORMAL)
        self.window.set_app_paintable(True)

        def draw_callback(widget, cr):
            if widget.transparency:
                pass
                cr.set_source_rgba(color.red, color.green, color.blue, 1)
            else:
                cr.set_source_rgb(0, 0, 0)
            cr.set_operator(cairo.OPERATOR_SOURCE)
            cr.paint()
            cr.set_operator(cairo.OPERATOR_OVER)

        screen = self.window.get_screen()
        visual = screen.get_rgba_visual()
        self.window.transparency = False

        if visual and screen.is_composited():
            self.window.set_visual(visual)
            self.window.transparency = True
        else:
            log.warn('System doesn\'t support transparency')
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

        # double click stuff
        def double_click(hbox, event):
            """Handles double clicks on tabs area and when receive
            one, calls add_tab.
            """
            if event.button == 1 and event.type == Gdk.EventType._2BUTTON_PRESS:
                self.add_tab()

        evtbox = self.get_widget('event-tabs')
        evtbox.connect('button-press-event', double_click)

        # TODO PORT there is still some gtk stuff in there, how to trigger this? cant test...
        def scroll_manager(hbox, event):
            adj = self.get_widget('tabs-scrolledwindow').get_hadjustment()
            adj.set_page_increment(1)
            if event.direction == Gdk.ScrollDirection.Down:
                if self.notebook.get_current_page() + 1 < self.notebook.get_tab_count():
                    self.notebook.next_page()
                else:
                    return

            if event.direction == Gdk.ScrollDirection.UP:
                self.notebook.prev_page()

            current_page = self.notebook.get_current_page()
            tab = self.tabs.get_children()[current_page]
            rectangle = tab.get_allocation()
            adj.set_value(rectangle.x)

        evtbox.connect('scroll-event', scroll_manager)

        self.abbreviate = False
        self.was_deleted_tab = False

        def tabs_scrollbar_hide(hscrollbar):
            self.get_widget('event-tabs').set_property('height_request', 10)
            if self.abbreviate and self.was_deleted_tab:
                self.was_deleted_tab = False
                self.abbreviate = False
                self.recompute_tabs_titles()

        def tabs_scrollbar_show(hscrollbar):
            self.get_widget('event-tabs').set_property('height_request', -1)
            if self.settings.general.get_boolean('abbreviate-tab-names'):
                self.abbreviate = True
                self.recompute_tabs_titles()

        tabs_scrollbar = self.get_widget('tabs-scrolledwindow').get_hscrollbar()
        tabs_scrollbar.connect('hide', tabs_scrollbar_hide)
        tabs_scrollbar.connect('show', tabs_scrollbar_show)

        # Flag to prevent guake hide when window_losefocus is true and
        # user tries to use the context menu.
        self.showing_context_menu = False

        def hide_context_menu(menu):
            """Turn context menu flag off to make sure it is not being
            shown.
            """
            self.showing_context_menu = False

        self.get_widget('context-menu').connect('hide', hide_context_menu)
        self.get_widget('tab-menu').connect('hide', hide_context_menu)
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

    def _select_gtk_theme(self):
        gtk_theme_name = self.settings.general.get_string('gtk-theme-name')
        log.debug("Wanted GTK theme: %r", gtk_theme_name)
        settings = Gtk.Settings.get_default()
        if gtk_theme_name and (Path("/usr/share/themes") / gtk_theme_name).exists():
            settings.set_property("gtk-theme-name", gtk_theme_name)

        prefer_dark_theme = self.settings.general.get_boolean('gtk-prefer-dark-theme')
        log.debug("Prefer dark theme: %r", prefer_dark_theme)
        if prefer_dark_theme:
            settings.set_property("gtk-application-prefer-dark-theme", prefer_dark_theme)

    # load the custom commands infrastucture
    def load_custom_commands(self):
        if self.custom_command_menuitem:
            self.get_widget('context-menu').remove(self.custom_command_menuitem)
        custom_commands_menu = Gtk.Menu()
        if not self.get_custom_commands(custom_commands_menu):
            return
        menu = Gtk.MenuItem("Custom Commands")
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
        # TODO PORT test this code, where is the spec for the json file?

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
        # TODO PORT test this code
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

    def __load_palette(self):
        colorRGBA = Gdk.RGBA(0, 0, 0, 0)
        paletteList = list()
        for color in self.settings.styleFont.get_string("palette").split(':'):
            colorRGBA.parse(color)
            paletteList.append(colorRGBA.copy())
        return paletteList

    def __get_background_color(self, palette_list, transparency):
        if len(palette_list) > 16:
            bg_color = palette_list[17]
        else:
            bg_color = Gdk.RGBA(0, 0, 0, 0.9)

        if not self.transparency_toggled:
            bg_color.alpha = 1 / 100 * transparency
        else:
            bg_color.alpha = 1
        return bg_color

    def set_background_color_from_settings(self):
        self.set_colors_from_settings()

    def set_colors_from_settings(self):
        transparency = self.settings.styleBackground.get_int('transparency')
        palette_list = self.__load_palette()
        bg_color = self.__get_background_color(palette_list, transparency)

        if len(palette_list) > 16:
            font_color = palette_list[16]
        else:
            font_color = Gdk.RGBA(0, 0, 0, 0)

        for i in self.notebook.iter_terminals():
            i.set_color_foreground(font_color)
            i.set_color_bold(font_color)
            i.set_colors(font_color, bg_color, palette_list[:16])

    def execute_command(self, command, tab=None):
        """Execute the `command' in the `tab'. If tab is None, the
        command will be executed in the currently selected
        tab. Command should end with '\n', otherwise it will be
        appended to the string.
        """
        if not self.notebook.has_term():
            self.add_tab()

        if command[-1] != '\n':
            command += '\n'

        index = self.notebook.get_current_page()
        index = tab or self.notebook.get_current_page()
        for terminal in self.notebook.get_terminals_for_tab(index):
            terminal.feed_child(command, len(command))
            break

    def execute_command_by_uuid(self, tab_uuid, command):
        """Execute the `command' in the tab whose terminal has the `tab_uuid' uuid
        """
        if command[-1] != '\n':
            command += '\n'
        try:
            tab_uuid = uuid.UUID(tab_uuid)
            tab_index, = (
                index for index, t in enumerate(self.notebook.iter_terminals())
                if t.get_uuid() == tab_uuid
            )
            self.tabs.get_children()[tab_index]  # pylint: disable=expression-not-assigned
        except ValueError:
            pass
        else:
            terminals = self.notebook.get_terminals_for_tab(tab_index)
            for current_vte in terminals:
                current_vte.feed_child(command, len(command))

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

        link = self.getCurrentTerminalLinkUnderCursor()
        if link:
            self.get_widget('context_browse_on_web').set_visible(True)
            if len(link) >= 28:
                self.get_widget('context_browse_on_web'
                                ).set_label(_("Open Link: '{}...'".format(link[:25])))
            else:
                self.get_widget('context_browse_on_web').set_label(_("Open Link: {}".format(link)))
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

    def show_tab_menu(self, target, event):
        """Shows the tab menu with a right click. After that, the
        focus come back to the terminal.
        """
        if event.button == 3:
            self.showing_context_menu = True
            self.selected_tab = target
            menu = self.get_widget('tab-menu')
            menu.popup(None, None, None, None, 3, event.get_time())
        """This may look like it could be refactored by just calling self.set_terminal_focus()
        but self.set_terminal_focus() calls self.get_selected_tab() which overrides the
        value of self.selected_tab
        """
        self.notebook.get_current_terminal().grab_focus()
        pos = self.notebook.get_current_page()
        self.select_tab(0)
        self.select_tab(pos)

    def middle_button_click(self, target, event):
        """Closes a tab with a middle click
        """
        if event.button == 2 and event.type == Gdk.EventType.BUTTON_PRESS:
            previously_selected_tab = self.get_selected_tab()
            target.activate_tab()
            target_position = self.get_selected_tab()
            self.select_tab(previously_selected_tab)
            self.delete_tab(target_position)

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
        # TODO PORT reenable this after keybinder fixes (this is mostly done but needs testing)
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
        if not self.notebook.has_term():
            self.add_tab()

        self.window.set_keep_below(False)
        self.window.show_all()
        # this is needed because self.window.show_all() results in showing every
        # thing which includes the scrollbar too
        self.settings.general.triggerOnChangedValue(self.settings.general, "use-scrollbar")

        # TODO PORT do we need this?
        # if self.selected_color is None:
        #    self.selected_color = getattr(self.window.get_style(),
        #                                  "light")[int(gtk.STATE_SELECTED)]
        #
        #    # Reapply the tab color to all button in the tab list, since at least one doesn't have
        #    # the select color set. This needs to happen AFTER the first show_all, since before,
        #    # gtk has not loaded the right colors yet.
        #    for tab in self.tabs.get_children():
        #        if isinstance(tab, gtk.RadioButton):
        #            tab.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.Color(str(self.selected_color)))

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
            # TODO PORT get_pointer is deprecated
            # https://developer.gnome.org/gtk3/stable/GtkWidget.html#gtk-widget-get-pointer
            win, x, y, _ = screen.get_root_window().get_pointer()
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
            if unity_hide != 1 and (unity_pos == "Left" or unity_pos == "Right"):
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
        procs = self.notebook.get_running_fg_processes()
        tabs = self.notebook.get_tab_count()
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
            if N >= 0 and N < self.notebook.get_n_pages():
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
        pagepos = self.notebook.get_current_page()
        self.selected_tab = self.tabs.get_children()[pagepos]
        self.on_rename_current_tab_activate()
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

    def on_terminal_exited(self, term, status, widget):
        """When a terminal is closed, shell process should be killed,
        this is the method that does that, or, at least calls
        `delete_tab' method to do the work.
        """
        log.debug("Terminal exited: %s", term)
        if libutempter is not None:
            libutempter.utempter_remove_record(term.get_pty())
        self.delete_tab(self.notebook.page_num(widget), kill=False, prompt=False)

    def recompute_tabs_titles(self):
        """Updates labels on all tabs. This is required when `self.abbreviate`
        changes
        """
        use_vte_titles = self.settings.general.get_boolean("use-vte-titles")
        if not use_vte_titles:
            return

        for tab, vte in zip(self.tabs.get_children(), self.notebook.term_list):
            tab.set_label(self.compute_tab_title(vte))

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

    def on_terminal_title_changed(self, vte, box):
        use_vte_titles = self.settings.general.get_boolean('use-vte-titles')
        if not use_vte_titles:
            return
        page = self.notebook.page_num(box)
        tab = self.tabs.get_children()[page]
        # if tab has been renamed by user, don't override.
        if not getattr(tab, 'custom_label_set', False):
            vte_title = self.compute_tab_title(vte)
            tab.set_label(vte_title)
            tab.set_tooltip_text(vte_title)
            self.update_window_title(vte_title)
        else:
            text = getattr(tab, 'custom_label_text')
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
        entry = Gtk.Entry()
        entry.set_text(self.selected_tab.get_label())
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
        # dialog.set_has_separator(False)
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

            self.selected_tab.set_label(new_text)
            # if user sets empty name, consider he wants default behavior.
            setattr(self.selected_tab, 'custom_label_set', bool(new_text))

            # holds custom label name of the tab,
            # we need this to restore the name if the max length is changed
            setattr(self.selected_tab, 'custom_label_text', new_text)

            # trigger titling handler in case that custom label has been reset
            current_vte = self.notebook.get_current_terminal()
            current_vte.emit('window-title-changed')

        dialog.destroy()
        self.set_terminal_focus()

    def on_close_activate(self, *args):
        """Tab context menu close handler
        """
        tabs = self.tabs.get_children()
        pagepos = tabs.index(self.selected_tab)
        self.delete_tab(pagepos)

    def on_drag_data_received(self, widget, context, x, y, selection, target, timestamp, box):
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

        box.terminal.feed_child(text, len(command))
        return True

    # -- tab related functions --

    def close_tab(self, *args):
        """Closes the current tab.
        """
        pagepos = self.notebook.get_current_page()
        self.delete_tab(pagepos)

    def rename_tab_uuid(self, tab_uuid, new_text):
        """Rename an already added tab by its UUID
        """
        try:
            tab_uuid = uuid.UUID(tab_uuid)
            tab_index, = (
                index for index, t in enumerate(self.notebook.iter_terminals())
                if t.get_uuid() == tab_uuid
            )
            tab = self.tabs.get_children()[tab_index]
        except ValueError:
            pass
        else:
            tab.set_label(new_text)
            setattr(tab, 'custom_label_set', new_text != "-")
            if new_text != "-":
                setattr(self.selected_tab, 'custom_label_text', new_text)
            terminals = self.notebook.get_terminals_for_tab(tab_index)
            for current_vte in terminals:
                current_vte.emit('window-title-changed')

    def rename_tab(self, tab_index, new_text):
        """Rename an already added tab by its index.
        """
        try:
            tab = self.tabs.get_children()[tab_index]
        except IndexError:
            pass
        else:
            tab.set_label(new_text)
            setattr(tab, 'custom_label_set', new_text != "-")
            if new_text != "-":
                setattr(self.selected_tab, 'custom_label_text', new_text)
            terminals = self.notebook.get_terminals_for_tab(tab_index)
            for current_vte in terminals:
                current_vte.emit('window-title-changed')

    def rename_current_tab(self, new_text):
        """Sets the `self.selected_tab' var with the selected radio
        button and change its label to `new_text'.
        """

        pagepos = self.notebook.get_current_page()
        self.selected_tab = self.tabs.get_children()[pagepos]
        self.selected_tab.set_label(new_text)

        # it's hard to pass an empty string as a command line argument,
        # so we'll interpret single dash "-" as a "reset custom title" request
        setattr(self.selected_tab, 'custom_label_set', new_text != "-")
        if new_text != "-":
            setattr(self.selected_tab, 'custom_label_text', new_text)

        # trigger titling handler in case that custom label has been reset
        current_vte = self.notebook.get_current_terminal()
        current_vte.emit('window-title-changed')
        self.notebook.get_current_terminal().grab_focus()

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
            if self.settings.general.get_boolean('open-tab-cwd'):
                wd = self.get_current_dir()
            else:
                wd = os.environ['HOME']

        # TODO PORT the next line
        # params['loglastlog'] = login_shell

        # Environment variables are not actually parameters but they
        # need to be set before calling terminal.fork_command()
        # method. This is a good place to do it.
        self.update_proxy_vars(terminal)
        pid = terminal.spawn_sync(
            Vte.PtyFlags.DEFAULT, wd, argv, [], GLib.SpawnFlags.DO_NOT_REAP_CHILD, None, None, None
        )
        if isinstance(pid, tuple):
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

    def add_tab(self, directory=None):
        """Adds a new tab to the terminal notebook.
        """
        box = GuakeTerminalBox(self.settings)
        box.terminal.grab_focus()
        # TODO PORT port this
        # TODO PORT seems to run just fine without
        # box.terminal.drag_dest_set(gtk.DEST_DEFAULT_MOTION |
        #                           gtk.DEST_DEFAULT_DROP |
        #                           gtk.DEST_DEFAULT_HIGHLIGHT,
        #                           [('text/uri-list', gtk.TARGET_OTHER_APP, 0)],
        #                           gtk.gdk.ACTION_COPY
        #                           )

        box.terminal.connect('button-press-event', self.show_context_menu)
        box.terminal.connect('child-exited', self.on_terminal_exited, box)
        box.terminal.connect('window-title-changed', self.on_terminal_title_changed, box)
        box.terminal.connect('drag-data-received', self.on_drag_data_received, box)

        # TODO PORT is this still the case with the newer vte version?
        # -- Ubuntu has a patch to libvte which disables mouse scrolling in apps
        # -- like vim and less by default. If this is the case, enable it back.
        if hasattr(box.terminal, "set_alternate_screen_scroll"):
            box.terminal.set_alternate_screen_scroll(True)

        box.show()

        self.notebook.append_tab(box.terminal)

        pid = self.spawn_sync_pid(directory, box.terminal)

        if libutempter is not None:
            # TODO PORT needs verification box.terminal.get_pty() -> box.terminal.get_pty().get_fd()
            # After the fork_command we add this new tty to utmp !
            libutempter.utempter_add_record(box.terminal.get_pty().get_fd(), os.uname()[1])
        box.terminal.pid = pid

        # Adding a new radio button to the tabbar
        label = self.compute_tab_title(box.terminal)
        tabs = self.tabs.get_children()
        parent = tabs and tabs[0] or None
        bnt = Gtk.RadioButton(group=parent, label=label, use_underline=False)
        bnt.set_property('can-focus', False)
        bnt.set_property('draw-indicator', False)
        bnt.connect('button-press-event', self.show_tab_menu)
        bnt.connect('button-press-event', self.middle_button_click)
        bnt.connect('button-press-event', self.show_rename_current_tab_dialog)

        def _update_window_title_on_active_tab(*args):
            current_pagepos = self.notebook.get_current_page()
            wanted_pagepos = self.notebook.page_num(box)
            if current_pagepos != wanted_pagepos:
                self.notebook.set_current_page(wanted_pagepos)
                box.terminal.emit('window-title-changed')

        bnt.activate_tab = _update_window_title_on_active_tab
        bnt.connect('clicked', bnt.activate_tab)

        if self.selected_color is not None:
            # TODO PORT
            bnt.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.Color(str(self.selected_color)))
        # TODO PORT drag and drop
        # drag_drop_type = ("text/plain", gtk.TARGET_SAME_APP, 80)
        # TODO PORT drag and drop
        # bnt.drag_dest_set(gtk.DEST_DEFAULT_ALL, [drag_drop_type], gtk.gdk.ACTION_MOVE)
        bnt.connect("drag_data_received", self.on_drop_tab)
        # TODO PORT drag and drop
        # bnt.drag_source_set(gtk.gdk.BUTTON1_MASK, [drag_drop_type], gtk.gdk.ACTION_MOVE)
        bnt.connect("drag_data_get", self.on_drag_tab)
        bnt.show()

        self.tabs.pack_start(bnt, False, True, 1)

        self.notebook.append_page(box, None)
        bnt.activate_tab()
        box.terminal.grab_focus()
        self.load_config()

        for tab in self.tabs:
            if getattr(tab, 'custom_label_set', False):
                tab.set_label(getattr(tab, 'custom_label_text', tab.get_label()))

        if self.is_fullscreen:
            self.fullscreen()

        return str(box.terminal.get_uuid())

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
        # TODO PORT
        self.preventHide = True
        search_text = Gtk.TextView()

        dialog = Gtk.Dialog(
            _("Find"), self.window, Gtk.DialogFlags.DESTROY_WITH_PARENT, (
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
        if (response_id != RESPONSE_FORWARD and response_id != RESPONSE_BACKWARD):
            dialog.destroy()
            self.preventHide = False
            return

        start, end = dialog.buffer.get_bounds()
        search_string = start.get_text(end)

        log.debug(
            "Searching for %r %s\n", search_string,
            "forward" if response_id == RESPONSE_FORWARD else "backward"
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

    def on_drag_tab(self, widget, context, selection, targetType, eventTime):
        tab_pos = self.tabs.get_children().index(widget)
        selection.set(selection.target, 32, str(tab_pos))

    def on_drop_tab(self, widget, context, x, y, selection, targetType, data):
        old_tab_pos = int(selection.get_text())
        new_tab_pos = self.tabs.get_children().index(widget)
        self.move_tab(old_tab_pos, new_tab_pos)

    def move_tab(self, old_tab_pos, new_tab_pos):
        self.notebook.reorder_child(self.notebook.get_nth_page(old_tab_pos), new_tab_pos)
        self.tabs.reorder_child(self.tabs.get_children()[old_tab_pos], new_tab_pos)
        self.notebook.set_current_page(new_tab_pos)

    def is_tabs_scrollbar_visible(self):
        return (
            self.window.get_visible() and
            self.get_widget('tabs-scrolledwindow').get_hscrollbar().get_visible()
        )

    def delete_tab(self, pagepos, kill=True, prompt=True):
        """This function will destroy the notebook page, terminal and
        tab widgets and will call the function to kill interpreter
        forked by vte.
        """
        # Run prompt if necessary
        if prompt:
            procs = self.notebook.get_running_fg_processes_tab(pagepos)
            prompt_cfg = self.settings.general.get_int('prompt-on-close-tab')
            if (prompt_cfg == 1 and procs > 0) or (prompt_cfg == 2):
                if not self.run_quit_dialog(procs, -1):
                    return

        self.tabs.get_children()[pagepos].destroy()
        self.notebook.delete_tab(pagepos, kill=kill)

        if not self.notebook.has_term():
            self.hide()
            # avoiding the delay on next Guake show request
            self.add_tab()
        else:
            self.set_terminal_focus()

        self.was_deleted_tab = True
        abbreviate_tab_names = self.settings.general.get_boolean('abbreviate-tab-names')
        if abbreviate_tab_names and not self.is_tabs_scrollbar_visible():
            self.abbreviate = False
            self.recompute_tabs_titles()

        for tab in self.tabs:
            if getattr(tab, 'custom_label_set', False):
                tab.set_label(getattr(tab, 'custom_label_text', tab.get_label()))

    def set_terminal_focus(self):
        """Grabs the focus on the current tab.
        """
        self.notebook.get_current_terminal().grab_focus()
        self.notebook.set_current_page(self.get_selected_tab())
        # Hack to fix "Not focused on opening if tab was moved" (#441)
        pos = self.get_selected_tab()
        self.select_tab(0)
        self.select_tab(pos)

    def get_selected_uuidtab(self):
        """Returns the uuid of the current selected terminal
        """
        pagepos = self.notebook.get_current_page()
        terminals = self.notebook.get_terminals_for_tab(pagepos)
        return str(terminals[0].get_uuid())

    def select_current_tab(self, notebook, user_data, page):
        """When current self.notebook page is changed, the tab bar
        made with radio buttons must be updated.  This method does
        this work.
        """
        self.tabs.get_children()[page].set_active(True)

    def select_tab(self, tab_index):
        """Select an already added tab by its index.
        """
        try:
            self.tabs.get_children()[tab_index].set_active(True)
            return tab_index
        except IndexError:
            pass

    def get_selected_tab(self):
        """Return the selected tab index and set the
        self.selected_tab var.
        """
        pagepos = self.notebook.get_current_page()
        self.selected_tab = self.tabs.get_children()[pagepos]
        return pagepos

    def get_selected_tablabel(self):
        """Return the selected tab label.
        """
        pagepos = self.notebook.get_current_page()
        tab = self.tabs.get_children()[pagepos]
        tablabel = tab.get_label()
        return tablabel

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

    def getCurrentTerminalLinkUnderCursor(self):
        current_term = self.notebook.get_current_terminal()
        link = current_term.found_link
        log.debug("Current link under cursor: %s", link)
        if link:
            return link

    def browse_on_web(self, *args):
        log.debug("browsing %s...", self.getCurrentTerminalLinkUnderCursor())
        self.notebook.get_current_terminal().browse_link_under_cursor()

    def set_tab_position(self, *args):
        if self.settings.general.get_boolean('tab-ontop'):
            self.mainframe.reorder_child(self.notebook, 2)
        else:
            self.mainframe.reorder_child(self.notebook, 0)

        # self.mainframe.pack_start(self.notebook, expand=True, fill=True, padding=0)

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
        return

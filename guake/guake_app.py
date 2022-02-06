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
import shutil
import subprocess
import time as pytime
import traceback
import uuid

from pathlib import Path
from threading import Thread
from time import sleep
from urllib.parse import quote_plus
from xml.sax.saxutils import escape as xml_escape

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Keybinder", "3.0")
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import Keybinder

from guake import gtk_version
from guake import guake_version
from guake import notifier
from guake import vte_version
from guake.about import AboutDialog
from guake.common import gladefile
from guake.common import pixmapfile
from guake.dialogs import PromptQuitDialog
from guake.globals import MAX_TRANSPARENCY
from guake.globals import NAME
from guake.globals import TABS_SESSION_SCHEMA_VERSION
from guake.gsettings import GSettingHandler
from guake.keybindings import Keybindings
from guake.notebook import NotebookManager
from guake.palettes import PALETTES
from guake.paths import LOCALE_DIR
from guake.paths import SCHEMA_DIR
from guake.paths import try_to_compile_glib_schemas
from guake.prefs import PrefsDialog
from guake.prefs import refresh_user_start
from guake.settings import Settings
from guake.simplegladeapp import SimpleGladeApp
from guake.theme import patch_gtk_theme
from guake.theme import select_gtk_theme
from guake.utils import BackgroundImageManager
from guake.utils import FullscreenManager
from guake.utils import HidePrevention
from guake.utils import RectCalculator
from guake.utils import TabNameUtils
from guake.utils import get_server_time
from guake.utils import save_tabs_when_changed

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


class Guake(SimpleGladeApp):

    """Guake main class. Handles specialy the main window."""

    def __init__(self):
        def load_schema():
            log.info("Loading Gnome schema from: %s", SCHEMA_DIR)

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
        self.accel_group = None

        if (
            "schema-version" not in self.settings.general.keys()
            or self.settings.general.get_string("schema-version") != guake_version()
        ):
            log.exception("Schema from old guake version detected, regenerating schema")
            try:
                try_to_compile_glib_schemas()
            except subprocess.CalledProcessError:
                log.exception("Schema in non user-editable location, attempting to continue")
            schema_source = load_schema()
            self.settings = Settings(schema_source)
            self.settings.general.set_string("schema-version", guake_version())

        log.info("Language previously loaded from: %s", LOCALE_DIR)

        super().__init__(gladefile("guake.glade"))

        select_gtk_theme(self.settings)
        patch_gtk_theme(self.get_widget("window-root").get_style_context(), self.settings)
        self.add_callbacks(self)

        log.info("Guake Terminal %s", guake_version())
        log.info("VTE %s", vte_version())
        log.info("Gtk %s", gtk_version())

        self.hidden = True
        self.forceHide = False

        # trayicon! Using SVG handles better different OS trays
        # img = pixmapfile('guake-tray.svg')
        # trayicon!
        img = pixmapfile("guake-tray.png")
        try:
            import appindicator  # pylint: disable=import-outside-toplevel
        except ImportError:
            self.tray_icon = Gtk.StatusIcon()
            self.tray_icon.set_from_file(img)
            self.tray_icon.set_tooltip_text(_("Guake Terminal"))
            self.tray_icon.connect("popup-menu", self.show_menu)
            self.tray_icon.connect("activate", self.show_hide)
        else:
            # TODO PORT test this on a system with app indicator
            self.tray_icon = appindicator.Indicator(
                _("guake-indicator"), _("guake-tray"), appindicator.CATEGORY_OTHER
            )
            self.tray_icon.set_icon(img)
            self.tray_icon.set_status(appindicator.STATUS_ACTIVE)
            menu = self.get_widget("tray-menu")
            show = Gtk.MenuItem(_("Show"))
            show.set_sensitive(True)
            show.connect("activate", self.show_hide)
            show.show()
            menu.prepend(show)
            self.tray_icon.set_menu(menu)

        # important widgets
        self.window = self.get_widget("window-root")
        self.window.set_name("guake-terminal")
        self.window.set_keep_above(True)
        self.mainframe = self.get_widget("mainframe")
        self.mainframe.remove(self.get_widget("notebook-teminals"))

        # Pending restore for terminal split after show-up
        #     [(RootTerminalBox, TerminaBox, panes), ...]
        self.pending_restore_page_split = []
        self._failed_restore_page_split = []

        # BackgroundImageManager
        self.background_image_manager = BackgroundImageManager(self.window)

        # FullscreenManager
        self.fullscreen_manager = FullscreenManager(self.settings, self.window, self)

        # Workspace tracking
        self.notebook_manager = NotebookManager(
            self.window,
            self.mainframe,
            self.settings.general.get_boolean("workspace-specific-tab-sets"),
            self.terminal_spawned,
            self.page_deleted,
        )
        self.notebook_manager.connect("notebook-created", self.notebook_created)
        self.notebook_manager.set_workspace(0)
        self.set_tab_position()

        # check and set ARGB for real transparency
        self.update_visual()
        self.window.get_screen().connect("composited-changed", self.update_visual)

        # Debounce accel_search_terminal
        self.prev_accel_search_terminal_time = 0.0

        # holds the timestamp of the losefocus event
        self.losefocus_time = 0

        # holds the timestamp of the previous show/hide action
        self.prev_showhide_time = 0

        # Controls the transparency state needed for function accel_toggle_transparency
        self.transparency_toggled = False

        # store the default window title to reset it when update is not wanted
        self.default_window_title = self.window.get_title()

        self.display_tab_names = 0

        self.window.connect("focus-out-event", self.on_window_losefocus)
        self.window.connect("focus-in-event", self.on_window_takefocus)

        # Handling the delete-event of the main window to avoid
        # problems when closing it.
        def destroy(*args):
            self.hide()
            return True

        def window_event(*args):
            return self.window_event(*args)

        self.window.connect("delete-event", destroy)
        self.window.connect("window-state-event", window_event)

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

        if self.settings.general.get_boolean("start-fullscreen"):
            self.fullscreen()

        refresh_user_start(self.settings)

        # Restore tabs when startup
        if self.settings.general.get_boolean("restore-tabs-startup"):
            self.restore_tabs(suppress_notify=True)

        # Pop-up that shows that guake is working properly (if not
        # unset in the preferences windows)
        if self.settings.general.get_boolean("use-popup"):
            key = self.settings.keybindingsGlobal.get_string("show-hide")
            keyval, mask = Gtk.accelerator_parse(key)
            label = Gtk.accelerator_get_label(keyval, mask)
            filename = pixmapfile("guake-notification.png")
            notifier.showMessage(
                _("Guake Terminal"),
                _("Guake is now running,\n" "press <b>{!s}</b> to use it.").format(
                    xml_escape(label)
                ),
                filename,
            )

        log.info("Guake initialized")

    def get_notebook(self):
        return self.notebook_manager.get_current_notebook()

    def notebook_created(self, nm, notebook, key):
        notebook.attach_guake(self)

        # Tracking when reorder page
        notebook.connect("page-reordered", self.on_page_reorder)

    def update_visual(self, user_data=None):
        screen = self.window.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            # NOTE: We should re-realize window when update window visual
            # Otherwise it may failed, when the Guake it start without compositor
            self.window.unrealize()
            self.window.set_visual(visual)
            self.window.set_app_paintable(True)
            self.window.transparency = True
            self.window.realize()
            if self.window.get_property("visible"):
                self.hide()
                self.show()
        else:
            log.warn("System doesn't support transparency")
            self.window.transparency = False
            self.window.set_visual(screen.get_system_visual())

    # new color methods should be moved to the GuakeTerminal class

    def _load_palette(self):
        colorRGBA = Gdk.RGBA(0, 0, 0, 0)
        paletteList = []
        for color in self.settings.styleFont.get_string("palette").split(":"):
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
        transparency = self.settings.styleBackground.get_int("transparency")
        if not self.transparency_toggled:
            bg_color.alpha = 1 / 100 * transparency
        else:
            bg_color.alpha = 1
        return bg_color

    def set_background_color_from_settings(self, terminal_uuid=None):
        self.set_colors_from_settings(terminal_uuid)

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

    def set_colors_from_settings(self, terminal_uuid=None):
        bg_color = self.get_bgcolor()
        font_color = self.get_fgcolor()
        palette_list = self._load_palette()

        terminals = self.get_notebook().iter_terminals()
        if terminal_uuid:
            terminals = [t for t in terminals if t.uuid == terminal_uuid]

        for i in terminals:
            i.set_color_foreground(font_color)
            i.set_color_bold(font_color)
            i.set_colors(font_color, bg_color, palette_list[:16])

    def set_colors_from_settings_on_page(self, current_terminal_only=False, page_num=None):
        """If page_num is None, sets colors on the current page."""
        bg_color = self.get_bgcolor()
        font_color = self.get_fgcolor()
        palette_list = self._load_palette()

        if current_terminal_only:
            terminal = self.get_notebook().get_current_terminal()
            terminal.set_color_foreground(font_color)
            terminal.set_color_bold(font_color)
            terminal.set_colors(font_color, bg_color, palette_list[:16])
        else:
            if page_num is None:
                page_num = self.get_notebook().get_current_page()
            for terminal in self.get_notebook().get_nth_page(page_num).iter_terminals():
                terminal.set_color_foreground(font_color)
                terminal.set_color_bold(font_color)
                terminal.set_colors(font_color, bg_color, palette_list[:16])

    def reset_terminal_custom_colors(
        self, current_terminal=False, current_page=False, terminal_uuid=None
    ):
        """Resets terminal(s) colors to the settings colors.
        If current_terminal == False and current_page == False and terminal_uuid is None,
        resets colors of all terminals.
        """
        terminals = []

        if current_terminal:
            terminals.append(self.get_notebook().get_current_terminal())
        if current_page:
            page_num = self.get_notebook().get_current_page()
            for t in self.get_notebook().get_nth_page(page_num).iter_terminals():
                terminals.append(t)
        if terminal_uuid:
            for t in self.get_notebook().iter_terminals():
                if t.uuid == terminal_uuid:
                    terminals.append(t)
        if not current_terminal and not current_page and not terminal_uuid:
            terminals = list(self.get_notebook().iter_terminals())

        for i in terminals:
            i.reset_custom_colors()

    def set_bgcolor(self, bgcolor, current_terminal_only=False):
        if isinstance(bgcolor, str):
            c = Gdk.RGBA(0, 0, 0, 0)
            log.debug("Building Gdk Color from: %r", bgcolor)
            c.parse("#" + bgcolor)
            bgcolor = c
        if not isinstance(bgcolor, Gdk.RGBA):
            raise TypeError(f"color should be Gdk.RGBA, is: {bgcolor}")
        bgcolor = self._apply_transparency_to_color(bgcolor)
        log.debug("setting background color to: %r", bgcolor)

        if current_terminal_only:
            self.get_notebook().get_current_terminal().set_color_background_custom(bgcolor)
        else:
            page_num = self.get_notebook().get_current_page()
            for terminal in self.get_notebook().get_nth_page(page_num).iter_terminals():
                terminal.set_color_background_custom(bgcolor)

    def set_fgcolor(self, fgcolor, current_terminal_only=False):
        if isinstance(fgcolor, str):
            c = Gdk.RGBA(0, 0, 0, 0)
            log.debug("Building Gdk Color from: %r", fgcolor)
            c.parse("#" + fgcolor)
            fgcolor = c
        if not isinstance(fgcolor, Gdk.RGBA):
            raise TypeError(f"color should be Gdk.RGBA, is: {fgcolor}")
        log.debug("setting background color to: %r", fgcolor)

        if current_terminal_only:
            self.get_notebook().get_current_terminal().set_color_foreground_custom(fgcolor)
        else:
            page_num = self.get_notebook().get_current_page()
            for terminal in self.get_notebook().get_nth_page(page_num).iter_terminals():
                terminal.set_color_foreground_custom(fgcolor)

    def change_palette_name(self, palette_name):
        if isinstance(palette_name, str):
            if palette_name not in PALETTES:
                log.info("Palette name %s not found", palette_name)
                return
            log.debug("Settings palette name to %s", palette_name)
            self.settings.styleFont.set_string("palette", PALETTES[palette_name])
            self.settings.styleFont.set_string("palette-name", palette_name)
            self.set_colors_from_settings()

    def execute_command(self, command, tab=None):
        """Execute the `command' in the `tab'. If tab is None, the
        command will be executed in the currently selected
        tab. Command should end with '\n', otherwise it will be
        appended to the string.
        """
        if not self.get_notebook().has_page():
            self.add_tab()

        if command[-1] != "\n":
            command += "\n"

        terminal = self.get_notebook().get_current_terminal()
        terminal.feed_child(command)

    def execute_command_by_uuid(self, tab_uuid, command):
        """Execute the `command' in the tab whose terminal has the `tab_uuid' uuid"""
        if command[-1] != "\n":
            command += "\n"
        try:
            tab_uuid = uuid.UUID(tab_uuid)
            (page_index,) = (
                index
                for index, t in enumerate(self.get_notebook().iter_terminals())
                if t.get_uuid() == tab_uuid
            )
        except ValueError:
            pass
        else:
            terminals = self.get_notebook().get_terminals_for_page(page_index)
            for current_vte in terminals:
                current_vte.feed_child(command)

    def on_window_losefocus(self, window, event):
        """Hides terminal main window when it loses the focus and if
        the window_losefocus gconf variable is True.
        """
        if not HidePrevention(self.window).may_hide():
            return

        def hide_window_callback():
            value = self.settings.general.get_boolean("window-losefocus")
            visible = window.get_property("visible")
            self.losefocus_time = get_server_time(self.window)
            if visible and value:
                log.info("Hiding on focus lose")
                self.hide()
            return False

        def losefocus_callback(sleep_time):
            sleep(sleep_time)

            if (
                self.window.get_property("has-toplevel-focus")
                and (self.takefocus_time - self.lazy_losefocus_time) > 0
            ):
                log.debug("Short term losefocus detected. Skip the hidding")
                return

            if self.window.get_property("visible"):
                GLib.idle_add(hide_window_callback)

        if self.settings.general.get_boolean("lazy-losefocus"):
            self.lazy_losefocus_time = get_server_time(self.window)
            thread = Thread(target=losefocus_callback, args=(0.3,))
            thread.daemon = True
            thread.start()
            log.debug("Lazy losefocus check at %s", self.lazy_losefocus_time)
        else:
            hide_window_callback()

    def on_window_takefocus(self, window, event):
        self.takefocus_time = get_server_time(self.window)

    def show_menu(self, status_icon, button, activate_time):
        """Show the tray icon menu."""
        menu = self.get_widget("tray-menu")
        menu.popup(None, None, None, Gtk.StatusIcon.position_menu, button, activate_time)

    def show_about(self, *args):
        # TODO DBUS ONLY
        # TODO TRAY ONLY
        """Hides the main window and creates an instance of the About
        Dialog.
        """
        self.hide()
        AboutDialog()

    def show_prefs(self, *args):
        # TODO DBUS ONLY
        # TODO TRAY ONLY
        """Hides the main window and creates an instance of the
        Preferences window.
        """
        self.hide()
        PrefsDialog(self.settings).show()

    def is_iconified(self):
        # TODO this is "dead" code only gets called to log output or in out commented code
        if self.window:
            cur_state = int(self.window.get_state())
            return bool(cur_state & GDK_WINDOW_STATE_ICONIFIED)
        return False

    def window_event(self, window, event):
        window_state = event.new_window_state
        self.fullscreen_manager.set_window_state(window_state)
        log.debug("Received window state event: %s", window_state)

    def show_hide(self, *args):
        """Toggles the main window visibility"""
        log.debug("Show_hide called")
        if self.forceHide:
            self.forceHide = False
            return

        if not HidePrevention(self.window).may_hide():
            return

        if not self.win_prepare():
            return

        if not self.window.get_property("visible"):
            log.debug("Showing the terminal")
            self.show()
            self.window.get_window().focus(0)
            self.set_terminal_focus()
            return

        should_refocus = self.settings.general.get_boolean("window-refocus")
        has_focus = self.window.get_window().get_state() & Gdk.WindowState.FOCUSED
        if should_refocus and not has_focus:
            log.debug("Refocussing the terminal")
            self.window.get_window().focus(0)
            self.set_terminal_focus()
        else:
            log.debug("Hiding the terminal")
            self.hide()

    def get_visibility(self):
        if self.hidden:
            return 0
        return 1

    def show_focus(self, *args):
        self.win_prepare()
        self.show()
        self.set_terminal_focus()

    def win_prepare(self, *args):
        event_time = self.hotkeys.get_current_event_time()
        if (
            not self.settings.general.get_boolean("window-refocus")
            and self.window.get_window()
            and self.window.get_property("visible")
        ):
            pass
        elif (
            self.losefocus_time
            and not self.settings.general.get_boolean("window-losefocus")
            and self.losefocus_time < event_time
        ):
            if (
                self.window.get_window()
                and self.window.get_property("visible")
                and not self.window.get_window().get_state() & Gdk.WindowState.FOCUSED
            ):
                log.debug("DBG: Restoring the focus to the terminal")
                self.window.get_window().focus(event_time)
                self.set_terminal_focus()
                self.losefocus_time = 0
                return False
        elif (
            self.losefocus_time
            and self.settings.general.get_boolean("window-losefocus")
            and self.losefocus_time >= event_time
            and (self.losefocus_time - event_time) < 10
        ):
            self.losefocus_time = 0
            return False

        # limit rate at which the visibility can be toggled.
        if self.prev_showhide_time and event_time and (event_time - self.prev_showhide_time) < 65:
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

    def restore_pending_terminal_split(self):
        # Restore pending terminal split
        # XXX: Consider refactor how to handle failed restore page split
        self.pending_restore_page_split = self._failed_restore_page_split
        self._failed_restore_page_split = []
        for root, box, panes in self.pending_restore_page_split:
            if (
                self.window.get_property("visible")
                and root.get_notebook() == self.notebook_manager.get_current_notebook()
            ):
                root.restore_box_layout(box, panes)
            else:
                # Consider failed if the window is not visible
                self._failed_restore_page_split.append((root, box, panes))

    def show(self):
        """Shows the main window and grabs the focus on it."""
        self.hidden = False

        # setting window in all desktops

        window_rect = RectCalculator.set_final_window_rect(self.settings, self.window)
        self.window.stick()

        # add tab must be called before window.show to avoid a
        # blank screen before adding the tab.
        if not self.get_notebook().has_page():
            self.add_tab()

        self.window.set_keep_below(False)
        if not self.fullscreen_manager.is_fullscreen():
            self.window.show_all()
        # this is needed because self.window.show_all() results in showing every
        # thing which includes the scrollbar too
        self.settings.general.triggerOnChangedValue(self.settings.general, "use-scrollbar")

        # move the window even when in fullscreen-mode
        log.debug("Moving window to: %r", window_rect)
        self.window.move(window_rect.x, window_rect.y)

        # this works around an issue in fluxbox
        if not self.fullscreen_manager.is_fullscreen():
            self.settings.general.triggerOnChangedValue(self.settings.general, "window-height")

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

        # This is here because vte color configuration works only after the
        # widget is shown.

        self.settings.styleFont.triggerOnChangedValue(self.settings.styleFont, "color")
        self.settings.styleBackground.triggerOnChangedValue(self.settings.styleBackground, "color")

        log.debug("Current window position: %r", self.window.get_position())
        self.restore_pending_terminal_split()
        self.execute_hook("show")

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
        if not HidePrevention(self.window).may_hide():
            return
        self.hidden = True
        self.get_widget("window-root").unstick()
        self.window.hide()  # Don't use hide_all here!

        # Hide popover
        self.notebook_manager.get_current_notebook().popover.hide()

    def force_move_if_shown(self):
        if not self.hidden:
            # when displayed, GTK might refuse to move the window (X or Y position). Just hide and
            # redisplay it so the final position is correct
            log.debug("FORCING HIDE")
            self.hide()
            log.debug("FORCING SHOW")
            self.show()

    # -- configuration --

    def load_config(self, terminal_uuid=None):
        """ "Just a proxy for all the configuration stuff."""
        user_data = {}
        if terminal_uuid:
            user_data["terminal_uuid"] = terminal_uuid

        self.settings.general.triggerOnChangedValue(
            self.settings.general, "use-trayicon", user_data=user_data
        )
        self.settings.general.triggerOnChangedValue(
            self.settings.general, "prompt-on-quit", user_data=user_data
        )
        self.settings.general.triggerOnChangedValue(
            self.settings.general, "prompt-on-close-tab", user_data=user_data
        )
        self.settings.general.triggerOnChangedValue(
            self.settings.general, "window-tabbar", user_data=user_data
        )
        self.settings.general.triggerOnChangedValue(
            self.settings.general, "fullscreen-hide-tabbar", user_data=user_data
        )
        self.settings.general.triggerOnChangedValue(
            self.settings.general, "mouse-display", user_data=user_data
        )
        self.settings.general.triggerOnChangedValue(
            self.settings.general, "display-n", user_data=user_data
        )
        self.settings.general.triggerOnChangedValue(
            self.settings.general, "window-ontop", user_data=user_data
        )
        if not self.fullscreen_manager.is_fullscreen():
            self.settings.general.triggerOnChangedValue(
                self.settings.general, "window-height", user_data=user_data
            )
            self.settings.general.triggerOnChangedValue(
                self.settings.general, "window-width", user_data=user_data
            )
        self.settings.general.triggerOnChangedValue(
            self.settings.general, "use-scrollbar", user_data=user_data
        )
        self.settings.general.triggerOnChangedValue(
            self.settings.general, "history-size", user_data=user_data
        )
        self.settings.general.triggerOnChangedValue(
            self.settings.general, "infinite-history", user_data=user_data
        )
        self.settings.general.triggerOnChangedValue(
            self.settings.general, "use-vte-titles", user_data=user_data
        )
        self.settings.general.triggerOnChangedValue(
            self.settings.general, "set-window-title", user_data=user_data
        )
        self.settings.general.triggerOnChangedValue(
            self.settings.general, "display-tab-names", user_data=user_data
        )
        self.settings.general.triggerOnChangedValue(
            self.settings.general, "max-tab-name-length", user_data=user_data
        )
        self.settings.general.triggerOnChangedValue(
            self.settings.general, "quick-open-enable", user_data=user_data
        )
        self.settings.general.triggerOnChangedValue(
            self.settings.general, "quick-open-command-line", user_data=user_data
        )
        self.settings.style.triggerOnChangedValue(
            self.settings.style, "cursor-shape", user_data=user_data
        )
        self.settings.styleFont.triggerOnChangedValue(
            self.settings.styleFont, "style", user_data=user_data
        )
        self.settings.styleFont.triggerOnChangedValue(
            self.settings.styleFont, "palette", user_data=user_data
        )
        self.settings.styleFont.triggerOnChangedValue(
            self.settings.styleFont, "palette-name", user_data=user_data
        )
        self.settings.styleFont.triggerOnChangedValue(
            self.settings.styleFont, "allow-bold", user_data=user_data
        )
        self.settings.general.triggerOnChangedValue(self.settings.general, "background-image-file")
        self.settings.general.triggerOnChangedValue(
            self.settings.general, "background-image-layout-mode"
        )
        self.settings.style.triggerOnChangedValue(self.settings.style, "cursor-shape")
        self.settings.styleFont.triggerOnChangedValue(self.settings.styleFont, "style")
        self.settings.styleFont.triggerOnChangedValue(self.settings.styleFont, "palette")
        self.settings.styleFont.triggerOnChangedValue(self.settings.styleFont, "palette-name")
        self.settings.styleFont.triggerOnChangedValue(self.settings.styleFont, "allow-bold")
        self.settings.styleBackground.triggerOnChangedValue(
            self.settings.styleBackground, "transparency", user_data=user_data
        )
        self.settings.general.triggerOnChangedValue(
            self.settings.general, "use-default-font", user_data=user_data
        )
        self.settings.general.triggerOnChangedValue(
            self.settings.general, "compat-backspace", user_data=user_data
        )
        self.settings.general.triggerOnChangedValue(
            self.settings.general, "compat-delete", user_data=user_data
        )

    def accel_search_terminal(self, *args):
        nb = self.get_notebook()
        term = nb.get_current_terminal()
        box = nb.get_nth_page(nb.find_page_index_by_terminal(term))

        # Debounce it
        current_time = pytime.time()
        if current_time - self.prev_accel_search_terminal_time < 0.3:
            return

        self.prev_accel_search_terminal_time = current_time
        if box.search_revealer.get_reveal_child():
            if box.search_entry.has_focus():
                box.hide_search_box()
            else:
                # The box was showed, but out of focus
                # Don't hide it, re-grab the focus to search entry
                box.search_entry.grab_focus()
        else:
            box.show_search_box()

    def accel_quit(self, *args):
        """Callback to prompt the user whether to quit Guake or not."""
        procs = self.notebook_manager.get_running_fg_processes_count()
        tabs = self.notebook_manager.get_n_pages()
        notebooks = self.notebook_manager.get_n_notebooks()
        prompt_cfg = self.settings.general.get_boolean("prompt-on-quit")
        prompt_tab_cfg = self.settings.general.get_int("prompt-on-close-tab")
        # "Prompt on tab close" config overrides "prompt on quit" config
        if prompt_cfg or (prompt_tab_cfg == 1 and procs > 0) or (prompt_tab_cfg == 2):
            log.debug("Remaining procs=%r", procs)
            if PromptQuitDialog(self.window, procs, tabs, notebooks).quit():
                log.info("Quitting Guake")
                Gtk.main_quit()
        else:
            log.info("Quitting Guake")
            Gtk.main_quit()

    def accel_reset_terminal(self, *args):
        # TODO KEYBINDINGS ONLY
        """Callback to reset and clean the terminal"""
        HidePrevention(self.window).prevent()
        current_term = self.get_notebook().get_current_terminal()
        current_term.reset(True, True)
        HidePrevention(self.window).allow()
        return True

    def accel_zoom_in(self, *args):
        """Callback to zoom in."""
        for term in self.get_notebook().iter_terminals():
            term.increase_font_size()
        return True

    def accel_zoom_out(self, *args):
        """Callback to zoom out."""
        for term in self.get_notebook().iter_terminals():
            term.decrease_font_size()
        return True

    def accel_increase_height(self, *args):
        """Callback to increase height."""
        height = self.settings.general.get_int("window-height")
        self.settings.general.set_int("window-height", min(height + 2, 100))
        return True

    def accel_decrease_height(self, *args):
        """Callback to decrease height."""
        height = self.settings.general.get_int("window-height")
        self.settings.general.set_int("window-height", max(height - 2, 0))
        return True

    def accel_increase_transparency(self, *args):
        """Callback to increase transparency."""
        transparency = self.settings.styleBackground.get_int("transparency")
        if int(transparency) > 0:
            self.settings.styleBackground.set_int("transparency", int(transparency) - 2)
        return True

    def accel_decrease_transparency(self, *args):
        """Callback to decrease transparency."""
        transparency = self.settings.styleBackground.get_int("transparency")
        if int(transparency) < MAX_TRANSPARENCY:
            self.settings.styleBackground.set_int("transparency", int(transparency) + 2)
        return True

    def accel_toggle_transparency(self, *args):
        """Callback to toggle transparency."""
        self.transparency_toggled = not self.transparency_toggled
        self.settings.styleBackground.triggerOnChangedValue(
            self.settings.styleBackground, "transparency"
        )
        return True

    def accel_add(self, *args):
        """Callback to add a new tab. Called by the accel key."""
        self.add_tab()
        return True

    def accel_add_home(self, *args):
        """Callback to add a new tab in home directory. Called by the accel key."""
        self.add_tab(os.environ["HOME"])
        return True

    def accel_prev(self, *args):
        """Callback to go to the previous tab. Called by the accel key."""
        if self.get_notebook().get_current_page() == 0:
            self.get_notebook().set_current_page(self.get_notebook().get_n_pages() - 1)
        else:
            self.get_notebook().prev_page()
        return True

    def accel_next(self, *args):
        """Callback to go to the next tab. Called by the accel key."""
        if self.get_notebook().get_current_page() + 1 == self.get_notebook().get_n_pages():
            self.get_notebook().set_current_page(0)
        else:
            self.get_notebook().next_page()
        return True

    def accel_move_tab_left(self, *args):
        # TODO KEYBINDINGS ONLY
        """Callback to move a tab to the left"""
        pos = self.get_notebook().get_current_page()
        if pos != 0:
            self.move_tab(pos, pos - 1)
        return True

    def accel_move_tab_right(self, *args):
        # TODO KEYBINDINGS ONLY
        """Callback to move a tab to the right"""
        pos = self.get_notebook().get_current_page()
        if pos != self.get_notebook().get_n_pages() - 1:
            self.move_tab(pos, pos + 1)
        return True

    def move_tab(self, old_tab_pos, new_tab_pos):
        self.get_notebook().reorder_child(
            self.get_notebook().get_nth_page(old_tab_pos), new_tab_pos
        )
        self.get_notebook().set_current_page(new_tab_pos)

    def gen_accel_switch_tabN(self, N):
        """Generates callback (which called by accel key) to go to the Nth tab."""

        def callback(*args):
            if 0 <= N < self.get_notebook().get_n_pages():
                self.get_notebook().set_current_page(N)
            return True

        return callback

    def accel_switch_tab_last(self, *args):
        last_tab = self.get_notebook().get_n_pages() - 1
        self.get_notebook().set_current_page(last_tab)
        return True

    def accel_rename_current_tab(self, *args):
        """Callback to show the rename tab dialog. Called by the accel
        key.
        """
        page_num = self.get_notebook().get_current_page()
        page = self.get_notebook().get_nth_page(page_num)
        self.get_notebook().get_tab_label(page).on_rename(None)
        return True

    def accel_copy_clipboard(self, *args):
        # TODO KEYBINDINGS ONLY
        """Callback to copy text in the shown terminal. Called by the
        accel key.
        """
        self.get_notebook().get_current_terminal().copy_clipboard()
        return True

    def accel_paste_clipboard(self, *args):
        # TODO KEYBINDINGS ONLY
        """Callback to paste text in the shown terminal. Called by the
        accel key.
        """
        self.get_notebook().get_current_terminal().paste_clipboard()
        return True

    def accel_toggle_hide_on_lose_focus(self, *args):
        """Callback toggle whether the window should hide when it loses
        focus. Called by the accel key.
        """
        if self.settings.general.get_boolean("window-losefocus"):
            self.settings.general.set_boolean("window-losefocus", False)
        else:
            self.settings.general.set_boolean("window-losefocus", True)
        return True

    def accel_toggle_fullscreen(self, *args):
        self.fullscreen_manager.toggle()
        return True

    def fullscreen(self):
        self.fullscreen_manager.fullscreen()

    def unfullscreen(self):
        self.fullscreen_manager.unfullscreen()

    # -- callbacks --

    def recompute_tabs_titles(self):
        """Updates labels on all tabs. This is required when `self.display_tab_names`
        changes
        """
        use_vte_titles = self.settings.general.get_boolean("use-vte-titles")
        if not use_vte_titles:
            return

        # TODO NOTEBOOK this code only works if there is only one terminal in a
        # page, this need to be rewritten
        for terminal in self.get_notebook().iter_terminals():
            page_num = self.get_notebook().page_num(terminal.get_parent())
            self.get_notebook().rename_page(page_num, self.compute_tab_title(terminal), False)

    def compute_tab_title(self, vte):
        """Compute the tab title"""
        vte_title = vte.get_window_title() or _("Terminal")
        try:
            current_directory = vte.get_current_directory()
            if self.display_tab_names == 1 and vte_title.endswith(current_directory):
                parts = current_directory.split("/")
                parts = [s[:1] for s in parts[:-1]] + [parts[-1]]
                vte_title = vte_title[: len(vte_title) - len(current_directory)] + "/".join(parts)
            if self.display_tab_names == 2:
                vte_title = current_directory.split("/")[-1]
                if not vte_title:
                    vte_title = "(root)"
        except OSError:
            pass
        return TabNameUtils.shorten(vte_title, self.settings)

    def check_if_terminal_directory_changed(self, term):
        @save_tabs_when_changed
        def terminal_directory_changed(self):
            # Yep, just used for save tabs when changed
            pass

        current_directory = term.get_current_directory()
        if current_directory != term.directory:
            term.directory = current_directory
            terminal_directory_changed(self)

    def on_terminal_title_changed(self, vte, term):
        # box must be a page
        if not term.get_parent():
            return

        # Check if terminal directory has changed
        self.check_if_terminal_directory_changed(term)

        box = term.get_parent().get_root_box()
        use_vte_titles = self.settings.general.get_boolean("use-vte-titles")
        if not use_vte_titles:
            return

        # NOTE: Try our best to find the page_num inside all notebooks
        # this may return -1, should be checked ;)
        nb = self.get_notebook()
        page_num = nb.page_num(box)
        for nb in self.notebook_manager.iter_notebooks():
            page_num = nb.page_num(box)
            if page_num != -1:
                break
        # if tab has been renamed by user, don't override.
        if not getattr(box, "custom_label_set", False):
            title = self.compute_tab_title(vte)
            nb.rename_page(page_num, title, False)
            self.update_window_title(title)
        else:
            text = nb.get_tab_text_page(box)
            if text:
                self.update_window_title(text)

    def update_window_title(self, title):
        if self.settings.general.get_boolean("set-window-title") is True:
            self.window.set_title(title)
        else:
            self.window.set_title(self.default_window_title)

    # TODO PORT reimplement drag and drop text on terminal

    # -- tab related functions --

    def close_tab(self, *args):
        """Closes the current tab."""
        prompt_cfg = self.settings.general.get_int("prompt-on-close-tab")
        self.get_notebook().delete_page_current(prompt=prompt_cfg)

    def rename_tab_uuid(self, term_uuid, new_text, user_set=True):
        """Rename an already added tab by its UUID"""
        term_uuid = uuid.UUID(term_uuid)
        (page_index,) = (
            index
            for index, t in enumerate(self.get_notebook().iter_terminals())
            if t.get_uuid() == term_uuid
        )
        self.get_notebook().rename_page(page_index, new_text, user_set)

    def rename_current_tab(self, new_text, user_set=False):
        page_num = self.get_notebook().get_current_page()
        self.get_notebook().rename_page(page_num, new_text, user_set)

    def terminal_spawned(self, notebook, terminal, pid):
        self.load_config(terminal_uuid=terminal.uuid)
        terminal.handler_ids.append(
            terminal.connect("window-title-changed", self.on_terminal_title_changed, terminal)
        )

        # Use to detect if directory has changed
        terminal.directory = terminal.get_current_directory()

    @save_tabs_when_changed
    def add_tab(self, directory=None):
        """Adds a new tab to the terminal notebook."""
        position = None
        if self.settings.general.get_boolean("new-tab-after"):
            position = 1 + self.get_notebook().get_current_page()
        self.get_notebook().new_page_with_focus(directory, position=position)

    def find_tab(self, directory=None):
        log.debug("find")
        # TODO SEARCH
        HidePrevention(self.window).prevent()
        search_text = Gtk.TextView()

        dialog = Gtk.Dialog(
            _("Find"),
            self.window,
            Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (
                _("Forward"),
                RESPONSE_FORWARD,
                _("Backward"),
                RESPONSE_BACKWARD,
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.NONE,
            ),
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
            HidePrevention(self.window).allow()
            return

        start, end = dialog.buffer.get_bounds()
        search_string = start.get_text(end)

        log.debug(
            "Searching for %r %s\n",
            search_string,
            "forward" if response_id == RESPONSE_FORWARD else "backward",
        )

        current_term = self.get_notebook().get_current_terminal()
        log.debug("type: %r", type(current_term))
        log.debug("dir: %r", dir(current_term))
        current_term.search_set_gregex()
        current_term.search_get_gregex()

    def page_deleted(self, *args):
        if not self.get_notebook().has_page():
            self.hide()
            # avoiding the delay on next Guake show request
            self.add_tab()
        else:
            self.set_terminal_focus()

        self.was_deleted_tab = True
        self.display_tab_names = self.settings.general.get_int("display-tab-names")
        self.recompute_tabs_titles()

    def set_terminal_focus(self):
        """Grabs the focus on the current tab."""
        self.get_notebook().set_current_page(self.get_notebook().get_current_page())

    def get_selected_uuidtab(self):
        # TODO DBUS ONLY
        """Returns the uuid of the current selected terminal"""
        page_num = self.get_notebook().get_current_page()
        terminals = self.get_notebook().get_terminals_for_page(page_num)
        return str(terminals[0].get_uuid())

    def search_on_web(self, *args):
        """Search for the selected text on the web"""
        # TODO KEYBINDINGS ONLY
        current_term = self.get_notebook().get_current_terminal()

        if current_term.get_has_selection():
            current_term.copy_clipboard()
            guake_clipboard = Gtk.Clipboard.get_default(self.window.get_display())
            search_query = guake_clipboard.wait_for_text()
            search_query = quote_plus(search_query)
            if search_query:
                # TODO: search provider should be selectable (someone might
                # prefer bing.com, the internet is a strange place ¯\_(ツ)_/¯ )
                search_url = f"https://www.google.com/search?q={search_query}&safe=off"
                Gtk.show_uri(self.window.get_screen(), search_url, get_server_time(self.window))
        return True

    def set_tab_position(self, *args):
        if self.settings.general.get_boolean("tab-ontop"):
            self.get_notebook().set_tab_pos(Gtk.PositionType.TOP)
        else:
            self.get_notebook().set_tab_pos(Gtk.PositionType.BOTTOM)

    def execute_hook(self, event_name):
        """Execute shell commands related to current event_name"""
        hook = self.settings.hooks.get_string(f"{event_name}")
        if hook is not None and hook != "":
            hook = hook.split()
            try:
                with subprocess.Popen(hook):
                    pass
            except OSError as oserr:
                if oserr.errno == 8:
                    log.error(
                        "Hook execution failed! Check shebang at first line of %s!",
                        hook,
                    )
                    log.debug(traceback.format_exc())
                else:
                    log.error(str(oserr))
            except Exception as e:
                log.error("hook execution failed! %s", e)
                log.debug(traceback.format_exc())
            else:
                log.debug("hook on event %s has been executed", event_name)

    @save_tabs_when_changed
    def on_page_reorder(self, notebook, child, page_num):
        # Yep, just used for save tabs when changed
        pass

    def get_xdg_config_directory(self):
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME", "~/.config")
        return Path(xdg_config_home, "guake").expanduser()

    def save_tabs(self, filename="session.json"):
        config = {
            "schema_version": TABS_SESSION_SCHEMA_VERSION,
            "timestamp": int(pytime.time()),
            "workspace": {},
        }

        for key, nb in self.notebook_manager.get_notebooks().items():
            tabs = []
            for index in range(nb.get_n_pages()):
                try:
                    page = nb.get_nth_page(index)
                    panes = []
                    page.save_box_layout(page.child, panes)
                    tabs.append(
                        {
                            "panes": panes,
                            "label": nb.get_tab_text_index(index),
                            "custom_label_set": getattr(page, "custom_label_set", False),
                        }
                    )
                except FileNotFoundError:
                    # discard same broken tabs
                    pass
            # NOTE: Maybe we will have frame inside the workspace in future
            #       So lets use list to store the tabs (as for each frame)
            config["workspace"][key] = [tabs]

        if not self.get_xdg_config_directory().exists():
            self.get_xdg_config_directory().mkdir(parents=True)
        session_file = self.get_xdg_config_directory() / filename
        with session_file.open("w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        log.info("Guake tabs saved to %s", session_file)

    def restore_tabs(self, filename="session.json", suppress_notify=False):
        session_file = self.get_xdg_config_directory() / filename
        if not session_file.exists():
            log.info("Cannot find session.json file")
            return
        with session_file.open(encoding="utf-8") as f:
            try:
                config = json.load(f)
            except Exception:
                log.warning("%s is broken", session_file)
                shutil.copy(
                    session_file,
                    self.get_xdg_config_directory() / f"{filename}.bak",
                )
                img_filename = pixmapfile("guake-notification.png")
                notifier.showMessage(
                    _("Guake Terminal"),
                    _(
                        "Your {session_filename} file is broken, backup to {session_filename}.bak"
                    ).format(session_filename=filename),
                    img_filename,
                )
                return

        # Check schema_version exist
        if "schema_version" not in config:
            img_filename = pixmapfile("guake-notification.png")
            notifier.showMessage(
                _("Guake Terminal"),
                _(
                    "Tabs session restore abort.\n"
                    "Your session file ({session_filename}) missing schema_version as key"
                ).format(session_filename=session_file),
                img_filename,
            )
            return

        # Check schema version is not higher than current version
        if config["schema_version"] > TABS_SESSION_SCHEMA_VERSION:
            img_filename = pixmapfile("guake-notification.png")
            notifier.showMessage(
                _("Guake Terminal"),
                _(
                    "Tabs session restore abort.\n"
                    "Your session file schema version is higher than current version "
                    "({session_file_schema_version} > {current_schema_version})."
                ).format(
                    session_file_schema_version=config["schema_version"],
                    current_schema_version=TABS_SESSION_SCHEMA_VERSION,
                ),
                img_filename,
            )
            return

        # Disable auto save tabs
        v = self.settings.general.get_boolean("save-tabs-when-changed")
        self.settings.general.set_boolean("save-tabs-when-changed", False)

        # Restore all tabs for all workspaces
        self.pending_restore_page_split = []
        self._failed_restore_page_split = []
        try:
            for key, frames in config["workspace"].items():
                nb = self.notebook_manager.get_notebook(int(key))
                current_pages = nb.get_n_pages()

                # Restore each frames' tabs from config
                # NOTE: If frame implement in future, we will need to update this code
                for tabs in frames:
                    for index, tab in enumerate(tabs):
                        if tab.get("panes", False):
                            box, page_num, term = nb.new_page_with_focus(
                                label=tab["label"], empty=True
                            )
                            box.restore_box_layout(box.child, tab["panes"])
                        else:
                            directory = (
                                tab["panes"][0]["directory"]
                                if len(tab.get("panes", [])) == 1
                                else tab.get("directory", None)
                            )
                            nb.new_page_with_focus(directory, tab["label"], tab["custom_label_set"])

                    # Remove original pages in notebook
                    for i in range(current_pages):
                        nb.delete_page(0)
        except KeyError:
            log.warning("%s schema is broken", session_file)
            shutil.copy(
                session_file,
                self.get_xdg_config_directory() / f"{filename}.bak",
            )
            with (self.get_xdg_config_directory() / f"{filename}.log.err").open(
                "w", encoding="utf-8"
            ) as f:
                traceback.print_exc(file=f)
            img_filename = pixmapfile("guake-notification.png")
            notifier.showMessage(
                _("Guake Terminal"),
                _(
                    "Your {session_filename} schema is broken, backup to {session_filename}.bak, "
                    "and error message has been saved to {session_filename}.log.err.".format(
                        session_filename=filename
                    )
                ),
                img_filename,
            )

        # Reset auto save tabs
        self.settings.general.set_boolean("save-tabs-when-changed", v)

        # Notify the user
        if self.settings.general.get_boolean("restore-tabs-notify") and not suppress_notify:
            filename = pixmapfile("guake-notification.png")
            notifier.showMessage(_("Guake Terminal"), _("Your tabs has been restored!"), filename)

        log.info("Guake tabs restored from %s", session_file)

    def load_background_image(self, filename):
        self.background_image_manager.load_from_file(filename)

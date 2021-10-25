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

import gi

gi.require_version("Vte", "2.91")  # vte-0.38
from gi.repository import Gio
from gi.repository import Pango
from gi.repository import Vte
from guake.utils import RectCalculator

log = logging.getLogger(__name__)


class GSettingHandler:

    """Handles gconf changes, if any gconf variable is changed, a
    different method is called to handle this change.
    """

    def __init__(self, guake_inst):
        """Constructor of GConfHandler, just add the guake dir to the
        gconf client and bind the keys to its handler methods.
        """
        self.guake = guake_inst
        self.settings = guake_inst.settings
        settings = self.settings

        # Notification is not required for mouse_display/display-n because
        # set_final_window_rect polls gconf and is called whenever Guake is
        # shown or resized

        settings.general.onChangedValue("use-trayicon", self.trayicon_toggled)
        settings.general.onChangedValue("window-ontop", self.ontop_toggled)
        settings.general.onChangedValue("tab-ontop", self.tab_ontop_toggled)
        settings.general.onChangedValue("window-tabbar", self.tabbar_toggled)
        settings.general.onChangedValue(
            "fullscreen-hide-tabbar", self.fullscreen_hide_tabbar_toggled
        )
        settings.general.onChangedValue("window-height", self.size_changed)
        settings.general.onChangedValue("window-width", self.size_changed)
        settings.general.onChangedValue("window-valignment", self.alignment_changed)
        settings.general.onChangedValue("window-halignment", self.alignment_changed)
        settings.general.onChangedValue("window-vertical-displacement", self.alignment_changed)
        settings.general.onChangedValue("window-horizontal-displacement", self.alignment_changed)
        settings.style.onChangedValue("cursor-blink-mode", self.cursor_blink_mode_changed)
        settings.style.onChangedValue("cursor-shape", self.cursor_shape_changed)
        settings.general.onChangedValue("background-image-file", self.background_image_file_changed)
        settings.general.onChangedValue(
            "background-image-layout-mode", self.background_image_layout_mode_changed
        )

        settings.general.onChangedValue("use-scrollbar", self.scrollbar_toggled)
        settings.general.onChangedValue("history-size", self.history_size_changed)
        settings.general.onChangedValue("infinite-history", self.infinite_history_changed)
        settings.general.onChangedValue("scroll-output", self.keystroke_output)
        settings.general.onChangedValue("scroll-keystroke", self.keystroke_toggled)

        settings.general.onChangedValue("use-default-font", self.default_font_toggled)
        settings.styleFont.onChangedValue("style", self.fstyle_changed)
        settings.styleFont.onChangedValue("palette", self.fpalette_changed)
        settings.styleFont.onChangedValue("allow-bold", self.allow_bold_toggled)
        settings.styleFont.onChangedValue("bold-is-bright", self.bold_is_bright_toggled)
        settings.styleFont.onChangedValue("cell-height-scale", self.cell_height_scale_value_changed)
        settings.styleFont.onChangedValue("cell-width-scale", self.cell_width_scale_value_changed)
        settings.styleBackground.onChangedValue("transparency", self.bgtransparency_changed)

        settings.general.onChangedValue("compat-backspace", self.backspace_changed)
        settings.general.onChangedValue("compat-delete", self.delete_changed)
        settings.general.onChangedValue("custom-command_file", self.custom_command_file_changed)
        settings.general.onChangedValue("max-tab-name-length", self.max_tab_name_length_changed)
        settings.general.onChangedValue("display-tab-names", self.display_tab_names_changed)
        settings.general.onChangedValue("hide-tabs-if-one-tab", self.hide_tabs_if_one_tab_changed)

    def custom_command_file_changed(self, settings, key, user_data):
        self.guake.load_custom_commands()

    def trayicon_toggled(self, settings, key, user_data):
        """If the gconf var use_trayicon be changed, this method will
        be called and will show/hide the trayicon.
        """
        if hasattr(self.guake.tray_icon, "set_status"):
            self.guake.tray_icon.set_status(settings.get_boolean(key))
        else:
            self.guake.tray_icon.set_visible(settings.get_boolean(key))

    def ontop_toggled(self, settings, key, user_data):
        """If the gconf var window_ontop be changed, this method will
        be called and will set the keep_above attribute in guake's
        main window.
        """
        self.guake.window.set_keep_above(settings.get_boolean(key))

    def tab_ontop_toggled(self, settings, key, user_data):
        """tab_ontop changed"""
        self.guake.set_tab_position()

    def tabbar_toggled(self, settings, key, user_data):
        """If the gconf var use_tabbar be changed, this method will be
        called and will show/hide the tabbar.
        """
        if settings.get_boolean(key):
            if settings.get_boolean(key):
                self.guake.get_notebook().hide_tabbar_if_one_tab()
            else:
                self.guake.notebook_manager.set_notebooks_tabbar_visible(True)
        else:
            self.guake.notebook_manager.set_notebooks_tabbar_visible(False)

    def fullscreen_hide_tabbar_toggled(self, settings, key, user_data):
        """If the gconf var fullscreen_hide_tabbar be changed, this method will be
        called and will show/hide the tabbar when fullscreen.
        """
        if not self.guake.fullscreen_manager.is_fullscreen():
            return

        if settings.get_boolean(key):
            self.guake.notebook_manager.set_notebooks_tabbar_visible(False)
        else:
            if settings.get_boolean(key):
                self.guake.get_notebook().hide_tabbar_if_one_tab()
            else:
                self.guake.notebook_manager.set_notebooks_tabbar_visible(True)

    def alignment_changed(self, settings, key, user_data):
        """If the gconf var window_halignment be changed, this method will
        be called and will call the move function in guake.
        """
        RectCalculator.set_final_window_rect(self.settings, self.guake.window)
        self.guake.set_tab_position()
        self.guake.force_move_if_shown()

    def size_changed(self, settings, key, user_data):
        """If the gconf var window_height or window_width are changed,
        this method will be called and will call the resize function
        in guake.
        """
        RectCalculator.set_final_window_rect(self.settings, self.guake.window)

    def cursor_blink_mode_changed(self, settings, key, user_data):
        """Called when cursor blink mode settings has been changed"""
        terminal = (
            self.guake.notebook_manager.get_terminal_by_uuid(user_data.get("terminal_uuid"))
            if user_data
            else None
        )
        terminals = (terminal,) if terminal else self.guake.notebook_manager.iter_terminals()
        for term in terminals:
            term.set_property("cursor-blink-mode", settings.get_int(key))

    def cursor_shape_changed(self, settings, key, user_data):
        """Called when the cursor shape settings has been changed"""
        terminal = (
            self.guake.notebook_manager.get_terminal_by_uuid(user_data.get("terminal_uuid"))
            if user_data
            else None
        )
        terminals = (terminal,) if terminal else self.guake.notebook_manager.iter_terminals()
        for term in terminals:
            term.set_property("cursor-shape", settings.get_int(key))

    def background_image_file_changed(self, settings, key, user_data):
        """Called when the background image file settings has been changed"""
        filename = settings.get_string(key)
        if not filename or os.path.exists(filename):
            self.guake.background_image_manager.load_from_file(settings.get_string(key))

    def background_image_layout_mode_changed(self, settings, key, user_data):
        """Called when the background image layout mode settings has been changed"""
        self.guake.background_image_manager.layout_mode = settings.get_int(key)

    def scrollbar_toggled(self, settings, key, user_data):
        """If the gconf var use_scrollbar be changed, this method will
        be called and will show/hide scrollbars of all terminals open.
        """
        terminal = (
            self.guake.notebook_manager.get_terminal_by_uuid(user_data.get("terminal_uuid"))
            if user_data
            else None
        )
        terminals = (terminal,) if terminal else self.guake.notebook_manager.iter_terminals()
        for term in terminals:
            # There is an hbox in each tab of the main notebook and it
            # contains a Terminal and a Scrollbar. Since only have the
            # Terminal here, we're going to use this to get the
            # scrollbar and hide/show it.
            hbox = term.get_parent()
            if hbox is None:
                continue
            terminal, scrollbar = hbox.get_children()
            if settings.get_boolean(key):
                scrollbar.show()
            else:
                scrollbar.hide()

    def history_size_changed(self, settings, key, user_data):
        """If the gconf var history_size be changed, this method will
        be called and will set the scrollback_lines property of all
        terminals open.
        """
        lines = settings.get_int(key)
        terminal = (
            self.guake.notebook_manager.get_terminal_by_uuid(user_data.get("terminal_uuid"))
            if user_data
            else None
        )
        terminals = (terminal,) if terminal else self.guake.notebook_manager.iter_terminals()
        for i in terminals:
            i.set_scrollback_lines(lines)

    def infinite_history_changed(self, settings, key, user_data):
        if settings.get_boolean(key):
            lines = -1
        else:
            lines = self.settings.general.get_int("history-size")
        terminal = (
            self.guake.notebook_manager.get_terminal_by_uuid(user_data.get("terminal_uuid"))
            if user_data
            else None
        )
        terminals = (terminal,) if terminal else self.guake.notebook_manager.iter_terminals()
        for i in terminals:
            i.set_scrollback_lines(lines)

    def keystroke_output(self, settings, key, user_data):
        """If the gconf var scroll_output be changed, this method will
        be called and will set the scroll_on_output in all terminals
        open.
        """
        terminal = (
            self.guake.notebook_manager.get_terminal_by_uuid(user_data.get("terminal_uuid"))
            if user_data
            else None
        )
        terminals = (terminal,) if terminal else self.guake.notebook_manager.iter_terminals()
        for i in terminals:
            i.set_scroll_on_output(settings.get_boolean(key))

    def keystroke_toggled(self, settings, key, user_data):
        """If the gconf var scroll_keystroke be changed, this method
        will be called and will set the scroll_on_keystroke in all
        terminals open.
        """
        terminal = (
            self.guake.notebook_manager.get_terminal_by_uuid(user_data.get("terminal_uuid"))
            if user_data
            else None
        )
        terminals = (terminal,) if terminal else self.guake.notebook_manager.iter_terminals()
        for i in terminals:
            i.set_scroll_on_keystroke(settings.get_boolean(key))

    def default_font_toggled(self, settings, key, user_data):
        """If the gconf var use_default_font be changed, this method
        will be called and will change the font style to the gnome
        default or to the chosen font in style/font/style in all
        terminals open.
        """
        font_name = None
        if settings.get_boolean(key):
            gio_settings = Gio.Settings("org.gnome.desktop.interface")
            font_name = gio_settings.get_string("monospace-font-name")
        else:
            font_name = self.settings.styleFont.get_string("style")
        if not font_name:
            log.error("Error: unable to find font name (%s)", font_name)
            return
        font = Pango.FontDescription(font_name)
        if not font:
            log.error("Error: unable to load font (%s)", font_name)
            return
        terminal = (
            self.guake.notebook_manager.get_terminal_by_uuid(user_data.get("terminal_uuid"))
            if user_data
            else None
        )
        terminals = (terminal,) if terminal else self.guake.notebook_manager.iter_terminals()
        for i in terminals:
            i.set_font(font)

    def allow_bold_toggled(self, settings, key, user_data):
        """If the gconf var allow_bold is changed, this method will be called
        and will change the VTE terminal o.
        displaying characters in bold font.
        """
        terminal = (
            self.guake.notebook_manager.get_terminal_by_uuid(user_data.get("terminal_uuid"))
            if user_data
            else None
        )
        terminals = (terminal,) if terminal else self.guake.notebook_manager.iter_terminals()
        for term in terminals:
            term.set_allow_bold(settings.get_boolean(key))

    def bold_is_bright_toggled(self, settings, key, user_data):
        """If the dconf var bold_is_bright is changed, this method will be called
        and will change the VTE terminal to toggle auto-brightened bold text.
        """
        try:
            terminal = self.guake.notebook_manager.get_terminal_by_uuid(
                user_data.get("terminal_uuid") if user_data else None
            )
            terminals = (terminal,) if terminal else self.guake.notebook_manager.iter_terminals()
            for term in terminals:
                term.set_bold_is_bright(settings.get_boolean(key))
        except:  # pylint: disable=bare-except
            log.error("set_bold_is_bright not supported by your version of VTE")

    def cell_height_scale_value_changed(self, settings, key, user_data):
        """If the gconf var style/font/cell-height-scale be changed, this
        method will be called and will set terminal height scale properties
        in all terminals.
        """
        height_scale = settings.get_double(key)
        try:
            terminal = self.guake.notebook_manager.get_terminal_by_uuid(
                user_data.get("terminal_uuid") if user_data else None
            )
            terminals = (terminal,) if terminal else self.guake.notebook_manager.iter_terminals()
            for term in terminals:
                term.set_cell_height_scale(height_scale)
        except:  # pylint: disable=bare-except
            log.error("set_cell_height_scale not supported by your version of VTE")

    def cell_width_scale_value_changed(self, settings, key, user_data):
        """If the gconf var style/font/cell-width-scale be changed, this
        method will be called and will set terminal width scale properties
        in all terminals.
        """
        width_scale = settings.get_double(key)
        try:
            terminal = self.guake.notebook_manager.get_terminal_by_uuid(
                user_data.get("terminal_uuid") if user_data else None
            )
            terminals = (terminal,) if terminal else self.guake.notebook_manager.iter_terminals()
            for term in terminals:
                term.set_cell_width_scale(width_scale)
        except:  # pylint: disable=bare-except
            log.error("set_cell_width_scale not supported by your version of VTE")

    def palette_font_and_background_color_toggled(self, settings, key, user_data):
        """If the gconf var use_palette_font_and_background_color be changed, this method
        will be called and will change the font color and the background color to the color
        defined in the palette.
        """
        self.settings.styleFont.triggerOnChangedValue(self.settings.styleFont, "palette")

    def fstyle_changed(self, settings, key, user_data):
        """If the gconf var style/font/style be changed, this method
        will be called and will change the font style in all terminals
        open.
        """
        terminal_uuid = user_data.get("terminal_uuid") if user_data else None

        if terminal_uuid:
            terminal = self.guake.notebook_manager.get_terminal_by_uuid(terminal_uuid)
            terminals = (terminal,) if terminal else ()
        else:
            terminals = self.guake.notebook_manager.iter_terminals()

        if self.settings.general.get_boolean("use-default-font"):
            gio_settings = Gio.Settings("org.gnome.desktop.interface")
            font_name = gio_settings.get_string("monospace-font-name")
        else:
            font_name = settings.get_string(key)

        font = Pango.FontDescription(font_name)
        for i in terminals:
            i.set_font(font)

    def fpalette_changed(self, settings, key, user_data):
        """If the gconf var style/font/palette be changed, this method
        will be called and will change the color scheme in all terminals
        open.
        """
        self.guake.set_colors_from_settings(
            terminal_uuid=user_data.get("terminal_uuid") if user_data else None
        )

    def bgtransparency_changed(self, settings, key, user_data):
        """If the gconf var style/background/transparency be changed, this
        method will be called and will set the saturation and transparency
        properties in all terminals open.
        """
        self.guake.set_background_color_from_settings(
            terminal_uuid=user_data.get("terminal_uuid") if user_data else None
        )

    def getEraseBinding(self, str):
        if str == "auto":
            return Vte.EraseBinding(0)
        if str == "ascii-backspace":
            return Vte.EraseBinding(1)
        if str == "ascii-delete":
            return Vte.EraseBinding(2)
        if str == "delete-sequence":
            return Vte.EraseBinding(3)
        if str == "tty":
            return Vte.EraseBinding(4)

    def backspace_changed(self, settings, key, user_data):
        """If the gconf var compat_backspace be changed, this method
        will be called and will change the binding configuration in
        all terminals open.
        """
        terminal = (
            self.guake.notebook_manager.get_terminal_by_uuid(user_data.get("terminal_uuid"))
            if user_data
            else None
        )
        terminals = (terminal,) if terminal else self.guake.notebook_manager.iter_terminals()
        for i in terminals:
            i.set_backspace_binding(self.getEraseBinding(settings.get_string(key)))

    def delete_changed(self, settings, key, user_data):
        """If the gconf var compat_delete be changed, this method
        will be called and will change the binding configuration in
        all terminals open.
        """
        terminal = (
            self.guake.notebook_manager.get_terminal_by_uuid(user_data.get("terminal_uuid"))
            if user_data
            else None
        )
        terminals = (terminal,) if terminal else self.guake.notebook_manager.iter_terminals()
        for i in terminals:
            i.set_delete_binding(self.getEraseBinding(settings.get_string(key)))

    def max_tab_name_length_changed(self, settings, key, user_data):
        """If the gconf var max_tab_name_length be changed, this method will
        be called and will set the tab name length limit.
        """

        # avoid get window title before terminal is ready
        if self.guake.notebook_manager.get_current_notebook().get_current_terminal() is None:
            return
        # avoid get window title before terminal is ready
        if (
            self.guake.notebook_manager.get_current_notebook()
            .get_current_terminal()
            .get_window_title()
            is None
        ):
            return

        self.guake.recompute_tabs_titles()

    def display_tab_names_changed(self, settings, key, user_data):
        """If the gconf var display-tab-names was changed, this method will
        be called and will update tab names.
        """
        self.guake.display_tab_names = settings.get_int("display-tab-names")
        self.guake.recompute_tabs_titles()

    def hide_tabs_if_one_tab_changed(self, settings, key, user_data):
        """If the gconf var hide-tabs-if-one-tab was changed, this method will
        be called and will show/hide the tab bar if necessary
        """
        self.guake.get_notebook().hide_tabbar_if_one_tab()

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
from collections import defaultdict
import logging

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from guake import notifier
from guake.common import pixmapfile
from guake.split_utils import FocusMover
from guake.split_utils import SplitMover

log = logging.getLogger(__name__)


class Keybindings:

    """Handles changes in keyboard shortcuts."""

    def __init__(self, guake):
        """Constructor of Keyboard, only receives the guake instance
        to be used in internal methods.
        """
        self.guake = guake
        self.accel_group = None  # see reload_accelerators
        self._lookup = None
        self._masks = None

        # Setup global keys
        self.globalhotkeys = {}
        globalkeys = ["show-hide", "show-focus"]
        for key in globalkeys:
            guake.settings.keybindingsGlobal.onChangedValue(key, self.reload_global)
            guake.settings.keybindingsGlobal.triggerOnChangedValue(
                guake.settings.keybindingsGlobal, key, None
            )

        def x(*args):
            prompt_cfg = self.guake.settings.general.get_int("prompt-on-close-tab")
            self.guake.get_notebook().delete_page_current(prompt=prompt_cfg)

        # Setup local keys
        self.keys = [
            ("toggle-fullscreen", self.guake.accel_toggle_fullscreen),
            ("new-tab", self.guake.accel_add),
            ("new-tab-home", self.guake.accel_add_home),
            ("close-tab", x),
            ("rename-current-tab", self.guake.accel_rename_current_tab),
            ("previous-tab", self.guake.accel_prev),
            ("previous-tab-alt", self.guake.accel_prev),
            ("next-tab", self.guake.accel_next),
            ("next-tab-alt", self.guake.accel_next),
            ("clipboard-copy", self.guake.accel_copy_clipboard),
            ("clipboard-paste", self.guake.accel_paste_clipboard),
            ("quit", self.guake.accel_quit),
            ("zoom-in", self.guake.accel_zoom_in),
            ("zoom-in-alt", self.guake.accel_zoom_in),
            ("zoom-out", self.guake.accel_zoom_out),
            ("increase-height", self.guake.accel_increase_height),
            ("decrease-height", self.guake.accel_decrease_height),
            ("increase-transparency", self.guake.accel_increase_transparency),
            ("decrease-transparency", self.guake.accel_decrease_transparency),
            ("toggle-transparency", self.guake.accel_toggle_transparency),
            ("search-on-web", self.guake.search_on_web),
            ("move-tab-left", self.guake.accel_move_tab_left),
            ("move-tab-right", self.guake.accel_move_tab_right),
            ("switch-tab1", self.guake.gen_accel_switch_tabN(0)),
            ("switch-tab2", self.guake.gen_accel_switch_tabN(1)),
            ("switch-tab3", self.guake.gen_accel_switch_tabN(2)),
            ("switch-tab4", self.guake.gen_accel_switch_tabN(3)),
            ("switch-tab5", self.guake.gen_accel_switch_tabN(4)),
            ("switch-tab6", self.guake.gen_accel_switch_tabN(5)),
            ("switch-tab7", self.guake.gen_accel_switch_tabN(6)),
            ("switch-tab8", self.guake.gen_accel_switch_tabN(7)),
            ("switch-tab9", self.guake.gen_accel_switch_tabN(8)),
            ("switch-tab10", self.guake.gen_accel_switch_tabN(9)),
            ("switch-tab-last", self.guake.accel_switch_tab_last),
            ("reset-terminal", self.guake.accel_reset_terminal),
            (
                "split-tab-vertical",
                lambda *args: self.guake.get_notebook()
                .get_current_terminal()
                .get_parent()
                .split_v()
                or True,
            ),
            (
                "split-tab-horizontal",
                lambda *args: self.guake.get_notebook()
                .get_current_terminal()
                .get_parent()
                .split_h()
                or True,
            ),
            (
                "close-terminal",
                lambda *args: self.guake.get_notebook().get_current_terminal().kill() or True,
            ),
            (
                "focus-terminal-up",
                (
                    lambda *args: FocusMover(self.guake.window).move_up(
                        self.guake.get_notebook().get_current_terminal()
                    )
                    or True
                ),
            ),
            (
                "focus-terminal-down",
                (
                    lambda *args: FocusMover(self.guake.window).move_down(
                        self.guake.get_notebook().get_current_terminal()
                    )
                    or True
                ),
            ),
            (
                "focus-terminal-right",
                (
                    lambda *args: FocusMover(self.guake.window).move_right(
                        self.guake.get_notebook().get_current_terminal()
                    )
                    or True
                ),
            ),
            (
                "focus-terminal-left",
                (
                    lambda *args: FocusMover(self.guake.window).move_left(
                        self.guake.get_notebook().get_current_terminal()
                    )
                    or True
                ),
            ),
            (
                "move-terminal-split-up",
                (
                    lambda *args: SplitMover.move_up(  # keep make style from concat this lines
                        self.guake.get_notebook().get_current_terminal()
                    )
                    or True
                ),
            ),
            (
                "move-terminal-split-down",
                (
                    lambda *args: SplitMover.move_down(  # keep make style from concat this lines
                        self.guake.get_notebook().get_current_terminal()
                    )
                    or True
                ),
            ),
            (
                "move-terminal-split-left",
                (
                    lambda *args: SplitMover.move_left(  # keep make style from concat this lines
                        self.guake.get_notebook().get_current_terminal()
                    )
                    or True
                ),
            ),
            (
                "move-terminal-split-right",
                (
                    lambda *args: SplitMover.move_right(  # keep make style from concat this lines
                        self.guake.get_notebook().get_current_terminal()
                    )
                    or True
                ),
            ),
            ("search-terminal", self.guake.accel_search_terminal),
            ("toggle-hide-on-lose-focus", self.guake.accel_toggle_hide_on_lose_focus),
        ]
        for key, _ in self.keys:
            guake.settings.keybindingsLocal.onChangedValue(key, self.reload_accelerators)
            self.reload_accelerators()

    def reload_global(self, settings, key, user_data):
        value = settings.get_string(key)
        if value == "disabled":
            return

        try:
            self.guake.hotkeys.unbind(self.globalhotkeys[key])
        except BaseException:
            pass

        self.globalhotkeys[key] = value
        if key == "show-hide":
            log.debug("reload_global: %r", value)
            if not self.guake.hotkeys.bind(value, self.guake.show_hide):
                keyval, mask = Gtk.accelerator_parse(value)
                label = Gtk.accelerator_get_label(keyval, mask)
                filename = pixmapfile("guake-notification.png")
                notifier.showMessage(
                    _("Guake Terminal"),
                    _(
                        "A problem happened when binding <b>%s</b> key.\n"
                        "Please use Guake Preferences dialog to choose another "
                        "key"
                    )
                    % label,
                    filename,
                )
        elif key == "show-focus" and not self.guake.hotkeys.bind(value, self.guake.show_focus):
            log.warn("can't bind show-focus key")

    def activate(self, window, event):
        """If keystroke matches a key binding, activate keybinding. Otherwise, allow
        keystroke to pass through."""
        key = event.hardware_keycode
        mod = event.state

        mask = mod & self._masks

        func = self._lookup[mask].get(key, None)
        if func:
            func()
            return True

        return False

    def reload_accelerators(self, *args):
        """Reassign an accel_group to guake main window and guake
        context menu and calls the load_accelerators method.
        """
        self._lookup = defaultdict(dict)
        self._masks = 0

        self.load_accelerators()
        self.guake.accel_group = self

    def load_accelerators(self):
        """Reads all gconf paths under /apps/guake/keybindings/local
        and adds to the _lookup.
        """
        for binding, action in self.keys:
            key, keycodes, mask = Gtk.accelerator_parse_with_keycode(
                self.guake.settings.keybindingsLocal.get_string(binding)
            )
            if keycodes and keycodes[0]:
                self._lookup[mask][keycodes[0]] = action
                self._masks |= mask

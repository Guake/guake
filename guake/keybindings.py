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

from collections import defaultdict

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk
from gi.repository import Gtk

from guake import notifier
from guake.common import pixmapfile
from guake.split_utils import FocusMover
from guake.split_utils import SplitMover

import ctypes
import ctypes.util

log = logging.getLogger(__name__)

# X11 helpers for physical modifier state (layout switch can eat modifiers).
_x11 = None
_x11_display = None
_x11_keymap = (ctypes.c_char * 32)()


def _x11_query_modifiers():
    """Return a Gdk.ModifierType mask of physically held Shift/Ctrl/Alt on X11."""
    global _x11, _x11_display
    try:
        if _x11 is None:
            libname = ctypes.util.find_library("X11") or "libX11.so.6"
            _x11 = ctypes.cdll.LoadLibrary(libname)
            _x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
            _x11.XOpenDisplay.restype = ctypes.c_void_p
            _x11.XQueryKeymap.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            _x11.XQueryKeymap.restype = ctypes.c_int
            _x11.XGetModifierMapping.argtypes = [ctypes.c_void_p]
            _x11.XGetModifierMapping.restype = ctypes.c_void_p
            _x11.XFreeModifiermap.argtypes = [ctypes.c_void_p]
            _x11.XFreeModifiermap.restype = ctypes.c_int
            _x11_display = _x11.XOpenDisplay(None)
        if not _x11_display:
            return Gdk.ModifierType(0)

        _x11.XQueryKeymap(_x11_display, _x11_keymap)
        keys = bytes(_x11_keymap)

        # Read modifier mapping: 8 modifiers * keycodes_per_modifier keycodes.
        class XModifierKeymap(ctypes.Structure):
            _fields_ = [
                ("max_keypermod", ctypes.c_int),
                ("modifiermap", ctypes.POINTER(ctypes.c_ubyte)),
            ]

        modmap_ptr = _x11.XGetModifierMapping(_x11_display)
        if not modmap_ptr:
            return Gdk.ModifierType(0)
        modmap = ctypes.cast(modmap_ptr, ctypes.POINTER(XModifierKeymap)).contents
        n = modmap.max_keypermod
        held = Gdk.ModifierType(0)
        # X modifier indices: Shift=0, Lock=1, Control=2, Mod1=3, Mod2=4, Mod3=5, Mod4=6, Mod5=7
        mod_masks = {
            0: Gdk.ModifierType.SHIFT_MASK,
            2: Gdk.ModifierType.CONTROL_MASK,
            3: Gdk.ModifierType.MOD1_MASK,
        }
        for mod_idx, mask in mod_masks.items():
            for i in range(n):
                keycode = modmap.modifiermap[mod_idx * n + i]
                if keycode != 0 and (keys[keycode >> 3] & (1 << (keycode & 7))):
                    held |= mask
                    break
        _x11.XFreeModifiermap(modmap_ptr)
        return held
    except Exception:
        log.debug("X11 modifier query failed", exc_info=True)
        return Gdk.ModifierType(0)


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
        self.keymap = Gdk.Keymap.get_for_display(Gdk.Display.get_default())

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
            ("new-tab-cwd", self.guake.accel_add_cwd),
            ("close-tab", x),
            ("rename-current-tab", self.guake.accel_rename_current_tab),
            ("previous-tab", self.guake.accel_prev),
            ("previous-tab-alt", self.guake.accel_prev),
            ("next-tab", self.guake.accel_next),
            ("next-tab-alt", self.guake.accel_next),
            ("clipboard-copy", self.guake.accel_copy_clipboard),
            ("clipboard-paste", self.guake.accel_paste_clipboard),
            ("select-all", self.guake.accel_select_all),
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
            ("open-link-under-terminal-cursor", self.guake.open_link_under_terminal_cursor),
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
            log.warning("can't bind show-focus key")

    def activate(self, window, event):
        """If keystroke matches a key binding, activate keybinding. Otherwise, allow
        keystroke to pass through."""
        key = event.keyval
        mod = event.state

        # Restore modifiers eaten by the layout switch (e.g. Ctrl+Shift
        # toggle) on X11. Only for non-modifier key presses.
        is_wayland = os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
        if not is_wayland and event.hardware_keycode:
            mod_keys = {
                Gdk.KEY_Shift_L, Gdk.KEY_Shift_R,
                Gdk.KEY_Control_L, Gdk.KEY_Control_R,
                Gdk.KEY_Alt_L, Gdk.KEY_Alt_R,
                Gdk.KEY_Meta_L, Gdk.KEY_Meta_R,
                Gdk.KEY_Super_L, Gdk.KEY_Super_R,
                Gdk.KEY_ISO_Next_Group, Gdk.KEY_ISO_Prev_Group,
                Gdk.KEY_ISO_First_Group, Gdk.KEY_ISO_Last_Group,
            }
            if key not in mod_keys:
                physical = _x11_query_modifiers()
                if not isinstance(physical, int):
                    physical = int(physical)
                if not isinstance(mod, int):
                    mod = int(mod)
                mod_mask = int(
                    Gdk.ModifierType.SHIFT_MASK
                    | Gdk.ModifierType.CONTROL_MASK
                    | Gdk.ModifierType.MOD1_MASK
                )
                mod |= physical & mod_mask

        # Normalize to the base Latin keysym from group 0 so hotkeys work
        # on non-Latin layouts (e.g. Russian). Group 0 is where XKB keeps
        # the Latin layout.
        if event.hardware_keycode:
            try:
                found, latin_key, _eg, _level, consumed = self.keymap.translate_keyboard_state(
                    event.hardware_keycode, Gdk.ModifierType(0), 0
                )
            except TypeError:
                found = False
                latin_key = 0
                consumed = Gdk.ModifierType(0)

            if found and 0 < latin_key <= 126:
                key = latin_key
                # If the layout switch consumed Shift/Ctrl/Alt, restore them
                # from the physical state so accelerators still match.
                if not isinstance(consumed, int):
                    consumed = int(consumed)
                consumed_mask = (
                    Gdk.ModifierType.SHIFT_MASK
                    | Gdk.ModifierType.CONTROL_MASK
                    | Gdk.ModifierType.MOD1_MASK
                ) & Gdk.ModifierType(consumed)
                mod |= consumed_mask
            elif event.keyval > 126:
                # Fallback: pick any ASCII keysym from this keycode.
                for i in self.keymap.get_entries_for_keycode(event.hardware_keycode)[2]:
                    if 0 < i <= 126:
                        key = i
                        break

        if mod & Gdk.ModifierType.SHIFT_MASK:
            if key == Gdk.KEY_ISO_Left_Tab:
                key = Gdk.KEY_Tab
            else:
                key = Gdk.keyval_to_lower(key)
        else:
            keys = Gdk.keyval_convert_case(key)
            if key != keys[1]:
                key = keys[0]
                mod &= ~Gdk.ModifierType.SHIFT_MASK

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
        """Reads all gconf paths under /org/guake/keybindings/local
        and adds to the _lookup.
        """

        for binding, action in self.keys:
            key, mask = Gtk.accelerator_parse(
                self.guake.settings.keybindingsLocal.get_string(binding)
            )
            if key > 0:
                self._lookup[mask][key] = action
                self._masks |= mask

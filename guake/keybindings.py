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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from guake import notifier
from guake.common import pixmapfile
from guake.split_utils import FocusMover
from guake.split_utils import SplitMover
from locale import gettext as _

log = logging.getLogger(__name__)


class Keybindings():

    """Handles changes in keyboard shortcuts.
    """

    def __init__(self, guake):
        """Constructor of Keyboard, only receives the guake instance
        to be used in internal methods.
        """
        self.guake = guake
        self.accel_group = None  # see reload_accelerators

        # Setup global keys
        self.globalhotkeys = {}
        globalkeys = ['show-hide', 'show-focus']
        for key in globalkeys:
            guake.settings.keybindingsGlobal.onChangedValue(key, self.reload_global)
            guake.settings.keybindingsGlobal.triggerOnChangedValue(
                guake.settings.keybindingsGlobal, key, None
            )

        # Setup local keys
        keys = [
            'toggle-fullscreen', 'new-tab', 'new-tab-home', 'close-tab', 'rename-current-tab',
            'previous-tab', 'next-tab', 'clipboard-copy', 'clipboard-paste', 'quit', 'zoom-in',
            'zoom-out', 'increase-height', 'decrease-height', 'increase-transparency',
            'decrease-transparency', 'toggle-transparency', "search-on-web", 'move-tab-left',
            'move-tab-right', 'switch-tab1', 'switch-tab2', 'switch-tab3', 'switch-tab4',
            'switch-tab5', 'switch-tab6', 'switch-tab7', 'switch-tab8', 'switch-tab9',
            'switch-tab10', 'switch-tab-last', 'reset-terminal', 'split-tab-vertical',
            'split-tab-horizontal', 'close-terminal', 'focus-terminal-up', 'focus-terminal-down',
            'focus-terminal-right', 'focus-terminal-left', 'move-terminal-split-up',
            'move-terminal-split-down', 'move-terminal-split-left', 'move-terminal-split-right',
            'search-terminal'
        ]
        for key in keys:
            guake.settings.keybindingsLocal.onChangedValue(key, self.reload_accelerators)
            self.reload_accelerators()

    def reload_global(self, settings, key, user_data):
        value = settings.get_string(key)
        if value == 'disabled':
            return

        try:
            self.guake.hotkeys.unbind(self.globalhotkeys[key])
        except Exception as e:
            pass

        self.globalhotkeys[key] = value
        if key == "show-hide":
            log.debug("reload_global: %r", value)
            if not self.guake.hotkeys.bind(value, self.guake.show_hide):
                keyval, mask = Gtk.accelerator_parse(value)
                label = Gtk.accelerator_get_label(keyval, mask)
                filename = pixmapfile('guake-notification.png')
                notifier.showMessage(
                    _('Guake Terminal'),
                    _(
                        'A problem happened when binding <b>%s</b> key.\n'
                        'Please use Guake Preferences dialog to choose another '
                        'key'
                    ) % label, filename
                )
        elif key == "show-focus":
            if not self.guake.hotkeys.bind(value, self.guake.show_focus):
                log.warn("can't bind show-focus key")
                return

    def reload_accelerators(self, *args):
        """Reassign an accel_group to guake main window and guake
        context menu and calls the load_accelerators method.
        """
        if self.accel_group:
            self.guake.window.remove_accel_group(self.accel_group)
        self.accel_group = Gtk.AccelGroup()
        self.guake.window.add_accel_group(self.accel_group)
        self.load_accelerators()

    def load_accelerators(self):
        """Reads all gconf paths under /apps/guake/keybindings/local
        and adds to the main accel_group.
        """

        def getk(x):
            return self.guake.settings.keybindingsLocal.get_string(x)

        key, mask = Gtk.accelerator_parse(getk('reset-terminal'))

        if key > 0:
            self.accel_group.connect(
                key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_reset_terminal
            )

        key, mask = Gtk.accelerator_parse(getk('quit'))
        if key > 0:
            self.accel_group.connect(key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_quit)

        key, mask = Gtk.accelerator_parse(getk('new-tab'))
        if key > 0:
            self.accel_group.connect(key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_add)

        key, mask = Gtk.accelerator_parse(getk('new-tab-home'))
        if key > 0:
            self.accel_group.connect(key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_add_home)

        key, mask = Gtk.accelerator_parse(getk('close-tab'))
        if key > 0:

            def x(*args):
                prompt_cfg = self.guake.settings.general.get_int('prompt-on-close-tab')
                self.guake.get_notebook().delete_page_current(prompt=prompt_cfg)

            self.accel_group.connect(key, mask, Gtk.AccelFlags.VISIBLE, x)

        key, mask = Gtk.accelerator_parse(getk('previous-tab'))
        if key > 0:
            self.accel_group.connect(key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_prev)

        key, mask = Gtk.accelerator_parse(getk('next-tab'))
        if key > 0:
            self.accel_group.connect(key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_next)

        key, mask = Gtk.accelerator_parse(getk('move-tab-left'))
        if key > 0:
            self.accel_group.connect(
                key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_move_tab_left
            )

        key, mask = Gtk.accelerator_parse(getk('move-tab-right'))
        if key > 0:
            self.accel_group.connect(
                key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_move_tab_right
            )

        key, mask = Gtk.accelerator_parse(getk('rename-current-tab'))
        if key > 0:
            self.accel_group.connect(
                key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_rename_current_tab
            )

        key, mask = Gtk.accelerator_parse(getk('clipboard-copy'))
        if key > 0:
            self.accel_group.connect(
                key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_copy_clipboard
            )

        key, mask = Gtk.accelerator_parse(getk('clipboard-paste'))
        if key > 0:
            self.accel_group.connect(
                key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_paste_clipboard
            )

        key, mask = Gtk.accelerator_parse(getk('toggle-fullscreen'))
        if key > 0:
            self.accel_group.connect(
                key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_toggle_fullscreen
            )

        key, mask = Gtk.accelerator_parse(getk('toggle-hide-on-lose-focus'))
        if key > 0:
            self.accel_group.connect(
                key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_toggle_hide_on_lose_focus
            )

        key, mask = Gtk.accelerator_parse(getk('zoom-in'))
        if key > 0:
            self.accel_group.connect(key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_zoom_in)

        key, mask = Gtk.accelerator_parse(getk('zoom-in-alt'))
        if key > 0:
            self.accel_group.connect(key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_zoom_in)

        key, mask = Gtk.accelerator_parse(getk('zoom-out'))
        if key > 0:
            self.accel_group.connect(key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_zoom_out)

        key, mask = Gtk.accelerator_parse(getk('increase-height'))
        if key > 0:
            self.accel_group.connect(
                key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_increase_height
            )

        key, mask = Gtk.accelerator_parse(getk('decrease-height'))
        if key > 0:
            self.accel_group.connect(
                key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_decrease_height
            )

        key, mask = Gtk.accelerator_parse(getk('increase-transparency'))
        if key > 0:
            self.accel_group.connect(
                key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_increase_transparency
            )

        key, mask = Gtk.accelerator_parse(getk('decrease-transparency'))
        if key > 0:
            self.accel_group.connect(
                key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_decrease_transparency
            )

        key, mask = Gtk.accelerator_parse(getk('toggle-transparency'))
        if key > 0:
            self.accel_group.connect(
                key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_toggle_transparency
            )

        for tab in range(1, 11):
            key, mask = Gtk.accelerator_parse(getk('switch-tab%d' % tab))
            if key > 0:
                self.accel_group.connect(
                    key, mask, Gtk.AccelFlags.VISIBLE, self.guake.gen_accel_switch_tabN(tab - 1)
                )

        key, mask = Gtk.accelerator_parse(getk('switch-tab-last'))
        if key > 0:
            self.accel_group.connect(
                key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_switch_tab_last
            )

        try:
            key, mask = Gtk.accelerator_parse(getk('search-on-web'))
            if key > 0:
                self.accel_group.connect(
                    key, mask, Gtk.AccelFlags.VISIBLE, self.guake.search_on_web
                )
        except Exception:
            log.exception("Exception occured")

        key, mask = Gtk.accelerator_parse(getk('split-tab-vertical'))
        if key > 0:
            self.accel_group.connect(
                key,
                mask,
                Gtk.AccelFlags.VISIBLE,
                (
                    lambda *args:  # keep make style from concat this lines
                    self.guake.get_notebook().get_current_terminal().get_parent().split_v() or True
                )
            )
        key, mask = Gtk.accelerator_parse(getk('split-tab-horizontal'))
        if key > 0:
            self.accel_group.connect(
                key,
                mask,
                Gtk.AccelFlags.VISIBLE,
                (
                    lambda *args:  # keep make style from concat this lines
                    self.guake.get_notebook().get_current_terminal().get_parent().split_h() or True
                )
            )
        key, mask = Gtk.accelerator_parse(getk('close-terminal'))
        if key > 0:
            self.accel_group.connect(
                key, mask, Gtk.AccelFlags.VISIBLE,
                (lambda *args: self.guake.get_notebook().get_current_terminal().kill() or True)
            )
        key, mask = Gtk.accelerator_parse(getk('focus-terminal-up'))
        if key > 0:
            self.accel_group.connect(
                key, mask, Gtk.AccelFlags.VISIBLE, (
                    lambda *args: FocusMover(self.guake.window).
                    move_up(self.guake.get_notebook().get_current_terminal()) or True
                )
            )
        key, mask = Gtk.accelerator_parse(getk('focus-terminal-down'))
        if key > 0:
            self.accel_group.connect(
                key, mask, Gtk.AccelFlags.VISIBLE, (
                    lambda *args: FocusMover(self.guake.window).
                    move_down(self.guake.get_notebook().get_current_terminal()) or True
                )
            )
        key, mask = Gtk.accelerator_parse(getk('focus-terminal-right'))
        if key > 0:
            self.accel_group.connect(
                key, mask, Gtk.AccelFlags.VISIBLE, (
                    lambda *args: FocusMover(self.guake.window).
                    move_right(self.guake.get_notebook().get_current_terminal()) or True
                )
            )
        key, mask = Gtk.accelerator_parse(getk('focus-terminal-left'))
        if key > 0:
            self.accel_group.connect(
                key, mask, Gtk.AccelFlags.VISIBLE, (
                    lambda *args: FocusMover(self.guake.window).
                    move_left(self.guake.get_notebook().get_current_terminal()) or True
                )
            )
        key, mask = Gtk.accelerator_parse(getk('move-terminal-split-up'))
        if key > 0:
            self.accel_group.connect(
                key,
                mask,
                Gtk.AccelFlags.VISIBLE,
                (
                    lambda *args:  # keep make style from concat this lines
                    SplitMover.move_up(self.guake.get_notebook().get_current_terminal()) or True
                )
            )
        key, mask = Gtk.accelerator_parse(getk('move-terminal-split-down'))
        if key > 0:
            self.accel_group.connect(
                key,
                mask,
                Gtk.AccelFlags.VISIBLE,
                (
                    lambda *args:  # keep make style from concat this lines
                    SplitMover.move_down(self.guake.get_notebook().get_current_terminal()) or True
                )
            )
        key, mask = Gtk.accelerator_parse(getk('move-terminal-split-left'))
        if key > 0:
            self.accel_group.connect(
                key,
                mask,
                Gtk.AccelFlags.VISIBLE,
                (
                    lambda *args:  # keep make style from concat this lines
                    SplitMover.move_left(self.guake.get_notebook().get_current_terminal()) or True
                )
            )
        key, mask = Gtk.accelerator_parse(getk('move-terminal-split-right'))
        if key > 0:
            self.accel_group.connect(
                key,
                mask,
                Gtk.AccelFlags.VISIBLE,
                (
                    lambda *args:  # keep make style from concat this lines
                    SplitMover.move_right(self.guake.get_notebook().get_current_terminal()) or True
                )
            )

        key, mask = Gtk.accelerator_parse(getk('search-terminal'))
        if key > 0:
            self.accel_group.connect(
                key, mask, Gtk.AccelFlags.VISIBLE, self.guake.accel_search_terminal
            )

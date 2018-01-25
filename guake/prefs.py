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
import re
import warnings

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Keybinder', '3.0')
gi.require_version('Vte', '2.91')  # vte-0.38
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import Keybinder
from gi.repository import Pango
from gi.repository import Vte

from guake.common import ShowableError
from guake.common import get_binaries_from_path
from guake.common import gladefile
from guake.common import hexify_color
from guake.common import pixmapfile
from guake.globals import ALIGN_BOTTOM
from guake.globals import ALIGN_CENTER
from guake.globals import ALIGN_LEFT
from guake.globals import ALIGN_RIGHT
from guake.globals import ALIGN_TOP
from guake.globals import ALWAYS_ON_PRIMARY
from guake.globals import LOCALE_DIR
from guake.globals import NAME
from guake.globals import _
from guake.palettes import PALETTES
from guake.simplegladeapp import SimpleGladeApp
from guake.simplegladeapp import bindtextdomain
from guake.terminal import GuakeTerminal
from guake.terminal import QUICK_OPEN_MATCHERS

# pylint: disable=unsubscriptable-object

log = logging.getLogger(__name__)

# A regular expression to match possible python interpreters when
# filling interpreters combo in preferences (including bpython and ipython)
PYTHONS = re.compile(r'^[a-z]python$|^python\d\.\d$')

# Path to the shells file, it will be used to start to populate
# interpreters combo, see the next variable, its important to fill the
# rest of the combo too.
SHELLS_FILE = '/etc/shells'

# string to show in prefereces dialog for user shell option
USER_SHELL_VALUE = _('<user shell>')

# translating our types to vte types
ERASE_BINDINGS = {
    'ASCII DEL': 'ascii-delete',
    'Escape sequence': 'delete-sequence',
    'Control-H': 'ascii-backspace'
}

HOTKEYS = [
    {
        'label': _('General'),
        'key': 'general',
        'keys': [
            {
                'key': 'show-hide',
                'label': _('Toggle Guake visibility')
            },
            {
                'key': 'show-focus',
                'label': _('Show and focus Guake window')
            },
            {
                'key': 'toggle-fullscreen',
                'label': _('Toggle Fullscreen')
            },
            {
                'key': 'toggle-hide-on-lose-focus',
                'label': _('Toggle Hide on Lose Focus')
            },
            {
                'key': 'quit',
                'label': _('Quit')
            },
            {
                'key': 'reset-terminal',
                'label': _('Reset terminal')
            },
        ]
    },
    {
        'label': _('Tab management'),
        'key': 'tab',
        'keys': [
            {
                'key': 'new-tab',
                'label': _('New tab')
            },
            {
                'key': 'close-tab',
                'label': _('Close tab')
            },
            {
                'key': 'rename-current-tab',
                'label': _('Rename current tab')
            },
        ]
    },
    {
        'label': _('Navigation'),
        'key': 'nav',
        'keys': [
            {
                'key': 'previous-tab',
                'label': _('Go to previous tab')
            },
            {
                'key': 'next-tab',
                'label': _('Go to next tab')
            },
            {
                'key': 'move-tab-left',
                'label': _('Move current tab left')
            },
            {
                'key': 'move-tab-right',
                'label': _('Move current tab right')
            },
            {
                'key': 'switch-tab1',
                'label': _('Go to first tab')
            },
            {
                'key': 'switch-tab2',
                'label': _('Go to second tab')
            },
            {
                'key': 'switch-tab3',
                'label': _('Go to third tab')
            },
            {
                'key': 'switch-tab4',
                'label': _('Go to fourth tab')
            },
            {
                'key': 'switch-tab5',
                'label': _('Go to fifth tab')
            },
            {
                'key': 'switch-tab6',
                'label': _('Go to sixth tab')
            },
            {
                'key': 'switch-tab7',
                'label': _('Go to seventh tab')
            },
            {
                'key': 'switch-tab8',
                'label': _('Go to eighth tab')
            },
            {
                'key': 'switch-tab9',
                'label': _('Go to ninth tab')
            },
            {
                'key': 'switch-tab10',
                'label': _('Go to tenth tab')
            },
            {
                'key': 'switch-tab-last',
                'label': _('Go to last tab')
            },
        ]
    },
    {
        'label': _('Appearance'),
        'key': 'appearance',
        'keys': [{
            'key': 'zoom-out',
            'label': _('Zoom out')
        }, {
            'key': 'zoom-in',
            'label': _('Zoom in')
        }, {
            'key': 'zoom-in-alt',
            'label': _('Zoom in (alternative)')
        }, {
            'key': 'increase-height',
            'label': _('Increase height')
        }, {
            'key': 'decrease-height',
            'label': _('Decrease height')
        }, {
            'key': 'increase-transparency',
            'label': _('Increase transparency')
        }, {
            'key': 'decrease-transparency',
            'label': _('Decrease transparency')
        }, {
            'key': 'toggle-transparency',
            'label': _('Toggle transparency')
        }]
    },
    {
        'label': _('Clipboard'),
        'key': 'clipboard',
        'keys': [
            {
                'key': 'clipboard-copy',
                'label': _('Copy text to clipboard')
            },
            {
                'key': 'clipboard-paste',
                'label': _('Paste text from clipboard')
            },
        ]
    },
    {
        'label': _('Extra features'),
        'key': 'extra',
        'keys': [{
            'key': 'search-on-web',
            'label': _('Search select text on web')
        }, ]
    },
]

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
}

HOTKET_MODEL_INDEX_DCONF = 0
HOTKET_MODEL_INDEX_LABEL = 1
HOTKET_MODEL_INDEX_HUMAN_ACCEL = 2
HOTKET_MODEL_INDEX_ACCEL = 3


def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c, c) for c in text)


class PrefsCallbacks(object):

    """Holds callbacks that will be used in the PrefsDialg class.
    """

    def __init__(self, prefDlg):
        self.prefDlg = prefDlg
        self.settings = prefDlg.settings

    # general tab

    def on_default_shell_changed(self, combo):
        """Changes the activity of default_shell in gconf
        """
        citer = combo.get_active_iter()
        if not citer:
            return
        shell = combo.get_model().get_value(citer, 0)
        # we unset the value (restore to default) when user chooses to use
        # user shell as guake shell interpreter.
        if shell == USER_SHELL_VALUE:
            self.settings.general.reset('default-shell')
        else:
            self.settings.general.set_string('default-shell', shell)

    def on_use_login_shell_toggled(self, chk):
        """Changes the activity of use_login_shell in gconf
        """
        self.settings.general.set_boolean('use-login-shell', chk.get_active())

    def on_open_tab_cwd_toggled(self, chk):
        """Changes the activity of open_tab_cwd in gconf
        """
        self.settings.general.set_boolean('open-tab-cwd', chk.get_active())

    def on_use_trayicon_toggled(self, chk):
        """Changes the activity of use_trayicon in gconf
        """
        self.settings.general.set_boolean('use-trayicon', chk.get_active())

    def on_use_popup_toggled(self, chk):
        """Changes the activity of use_popup in gconf
        """
        self.settings.general.set_boolean('use-popup', chk.get_active())

    def on_prompt_on_quit_toggled(self, chk):
        """Set the `prompt on quit' property in gconf
        """
        self.settings.general.set_boolean('prompt-on-quit', chk.get_active())

    def on_prompt_on_close_tab_changed(self, combo):
        """Set the `prompt_on_close_tab' property in gconf
        """
        self.settings.general.set_int('prompt-on-close-tab', combo.get_active())

    def on_window_ontop_toggled(self, chk):
        """Changes the activity of window_ontop in gconf
        """
        self.settings.general.set_boolean('window-ontop', chk.get_active())

    def on_tab_ontop_toggled(self, chk):
        """Changes the activity of tab_ontop in gconf
        """
        self.settings.general.set_boolean('tab-ontop', chk.get_active())

    def on_quick_open_enable_toggled(self, chk):
        """Changes the activity of quick_open_enable in gconf
        """
        self.settings.general.set_boolean('quick-open-enable', chk.get_active())

    def on_quick_open_in_current_terminal_toggled(self, chk):
        self.settings.general.set_boolean('quick-open-in-current-terminal', chk.get_active())

    def on_startup_script_changed(self, edt):
        self.settings.general.set_string('startup-script', edt.get_text())

    def on_window_refocus_toggled(self, chk):
        """Changes the activity of window_refocus in gconf
        """
        self.settings.general.set_boolean('window-refocus', chk.get_active())

    def on_window_losefocus_toggled(self, chk):
        """Changes the activity of window_losefocus in gconf
        """
        self.settings.general.set_boolean('window-losefocus', chk.get_active())

    def on_quick_open_command_line_changed(self, edt):
        self.settings.general.set_string('quick-open-command-line', edt.get_text())

    def on_hook_show_changed(self, edt):
        self.settings.hooks.set_string('show', edt.get_text())

    def on_window_tabbar_toggled(self, chk):
        """Changes the activity of window_tabbar in gconf
        """
        self.settings.general.set_boolean('window-tabbar', chk.get_active())

    def on_start_fullscreen_toggled(self, chk):
        """Changes the activity of start_fullscreen in gconf
        """
        self.settings.general.set_boolean('start-fullscreen', chk.get_active())

    def on_use_vte_titles_toggled(self, chk):
        """Save `use_vte_titles` property value in gconf
        """
        self.settings.general.set_boolean('use-vte-titles', chk.get_active())

    def on_set_window_title_toggled(self, chk):
        """Save `set_window_title` property value in gconf
        """
        self.settings.general.set_boolean('set-window-title', chk.get_active())

    def on_abbreviate_tab_names_toggled(self, chk):
        """Save `abbreviate_tab_names` property value in gconf
        """
        self.settings.general.set_boolean('abbreviate-tab-names', chk.get_active())

    def on_max_tab_name_length_changed(self, spin):
        """Changes the value of max_tab_name_length in gconf
        """
        val = int(spin.get_value())
        self.settings.general.set_int('max-tab-name-length', val)
        self.prefDlg.update_vte_subwidgets_states()

    def on_mouse_display_toggled(self, chk):
        """Set the 'appear on mouse display' preference in gconf. This
        property supercedes any value stored in display_n.
        """
        self.settings.general.set_boolean('mouse-display', chk.get_active())

    def on_right_align_toggled(self, chk):
        """set the horizontal alignment setting.
        """
        v = chk.get_active()
        self.settings.general.set_int('window-halignment', 1 if v else 0)

    def on_bottom_align_toggled(self, chk):
        """set the vertical alignment setting.
        """
        v = chk.get_active()
        self.settings.general.set_int('window-valignment', ALIGN_BOTTOM if v else ALIGN_TOP)

    def on_display_n_changed(self, combo):
        """Set the destination display in gconf.
        """

        i = combo.get_active_iter()
        if not i:
            return

        model = combo.get_model()
        first_item_path = model.get_path(model.get_iter_first())

        if model.get_path(i) == first_item_path:
            val_int = ALWAYS_ON_PRIMARY
        else:
            val = model.get_value(i, 0)
            val_int = int(val.split()[0])  # extracts 1 from '1' or from '1 (primary)'
        self.settings.general.set_int('display-n', val_int)

    def on_window_height_value_changed(self, hscale):
        """Changes the value of window_height in gconf
        """
        val = hscale.get_value()
        self.settings.general.set_int('window-height', int(val))

    def on_window_width_value_changed(self, wscale):
        """Changes the value of window_width in gconf
        """
        val = wscale.get_value()
        self.settings.general.set_int('window-width', int(val))

    def on_window_halign_value_changed(self, halign_button):
        """Changes the value of window_halignment in gconf
        """
        if halign_button.get_active():
            which_align = {
                'radiobutton_align_left': ALIGN_LEFT,
                'radiobutton_align_right': ALIGN_RIGHT,
                'radiobutton_align_center': ALIGN_CENTER
            }
            self.settings.general.set_int(
                'window-halignment', which_align[halign_button.get_name()]
            )
        self.prefDlg.get_widget("window_horizontal_displacement").set_sensitive(
            which_align[halign_button.get_name()] != ALIGN_CENTER
        )

    def on_use_audible_bell_toggled(self, chk):
        """Changes the value of use_audible_bell in gconf
        """
        self.settings.general.set_boolean('use-audible-bell', chk.get_active())

    # scrolling tab

    def on_use_scrollbar_toggled(self, chk):
        """Changes the activity of use_scrollbar in gconf
        """
        self.settings.general.set_boolean('use-scrollbar', chk.get_active())

    def on_history_size_value_changed(self, spin):
        """Changes the value of history_size in gconf
        """
        val = int(spin.get_value())
        self.settings.general.set_int('history-size', val)
        self._update_history_widgets()

    def on_infinite_history_toggled(self, chk):
        self.settings.general.set_boolean('infinite-history', chk.get_active())
        self._update_history_widgets()

    def _update_history_widgets(self):
        infinite = self.prefDlg.get_widget('infinite_history').get_active()
        self.prefDlg.get_widget('history_size').set_sensitive(not infinite)

    def on_scroll_output_toggled(self, chk):
        """Changes the activity of scroll_output in gconf
        """
        self.settings.general.set_boolean('scroll-output', chk.get_active())

    def on_scroll_keystroke_toggled(self, chk):
        """Changes the activity of scroll_keystroke in gconf
        """
        self.settings.general.set_boolean('scroll-keystroke', chk.get_active())

    # appearance tab

    def on_use_default_font_toggled(self, chk):
        """Changes the activity of use_default_font in gconf
        """
        self.settings.general.set_boolean('use-default-font', chk.get_active())

    def on_allow_bold_toggled(self, chk):
        """Changes the value of allow_bold in gconf
        """
        self.settings.styleFont.set_boolean('allow-bold', chk.get_active())

    def on_font_style_font_set(self, fbtn):
        """Changes the value of font_style in gconf
        """
        self.settings.styleFont.set_string('style', fbtn.get_font_name())

    def on_transparency_value_changed(self, hscale):
        """Changes the value of background_transparency in gconf
        """
        value = hscale.get_value()
        self.prefDlg.set_colors_from_settings()
        self.settings.styleBackground.set_int('transparency', int(value))

    # compatibility tab

    def on_backspace_binding_changed(self, combo):
        """Changes the value of compat_backspace in gconf
        """
        val = combo.get_active_text()
        self.settings.general.set_string('compat-backspace', ERASE_BINDINGS[val])

    def on_delete_binding_changed(self, combo):
        """Changes the value of compat_delete in gconf
        """
        val = combo.get_active_text()
        self.settings.general.set_string('compat-delete', ERASE_BINDINGS[val])

    def on_custom_command_file_chooser_file_changed(self, filechooser):
        self.settings.general.set_string('custom_command_file', filechooser.get_filename())

    def toggle_prompt_on_quit_sensitivity(self, combo):
        self.prefDlg.toggle_prompt_on_quit_sensitivity(combo)

    def toggle_style_sensitivity(self, chk):
        self.prefDlg.toggle_style_sensitivity(chk)

    def toggle_use_font_background_sensitivity(self, chk):
        self.prefDlg.toggle_use_font_background_sensitivity(chk)

    def toggle_display_n_sensitivity(self, chk):
        self.prefDlg.toggle_display_n_sensitivity(chk)

    def toggle_quick_open_command_line_sensitivity(self, chk):
        self.prefDlg.toggle_quick_open_command_line_sensitivity(chk)

    def toggle_use_vte_titles(self, chk):
        self.prefDlg.toggle_use_vte_titles(chk)

    def update_vte_subwidgets_states(self):
        self.prefDlg.update_vte_subwidgets_states()

    def on_reset_compat_defaults_clicked(self, btn):
        self.prefDlg.on_reset_compat_defaults_clicked(btn)

    def on_palette_name_changed(self, combo):
        self.prefDlg.on_palette_name_changed(combo)

    def on_cursor_shape_changed(self, combo):
        self.prefDlg.on_cursor_shape_changed(combo)

    def on_blink_cursor_toggled(self, chk):
        self.prefDlg.on_blink_cursor_toggled(chk)

    def on_palette_color_set(self, btn):
        self.prefDlg.on_palette_color_set(btn)

    def on_window_vertical_displacement_value_changed(self, spin):
        """Changes the value of window-vertical-displacement
        """
        self.settings.general.set_int('window-vertical-displacement', int(spin.get_value()))

    def on_window_horizontal_displacement_value_changed(self, spin):
        """Changes the value of window-horizontal-displacement
        """
        self.settings.general.set_int('window-horizontal-displacement', int(spin.get_value()))

    def reload_erase_combos(self, btn=None):
        self.prefDlg.reload_erase_combos(btn)

    def gtk_widget_destroy(self, btn):
        self.prefDlg.gtk_widget_destroy(btn)


class PrefsDialog(SimpleGladeApp):

    """The Guake Preferences dialog.
    """

    def __init__(self, settings):
        """Setup the preferences dialog interface, loading images,
        adding filters to file choosers and connecting some signals.
        """
        self.hotkey_alread_used = False
        self.store = None

        super(PrefsDialog, self).__init__(gladefile('prefs.glade'), root='config-window')
        self.settings = settings

        self.add_callbacks(PrefsCallbacks(self))

        # window cleanup handler
        self.window = self.get_widget('config-window')
        self.get_widget('config-window').connect('destroy', self.on_destroy)

        # images
        ipath = pixmapfile('guake-notification.png')
        self.get_widget('image_logo').set_from_file(ipath)
        ipath = pixmapfile('quick-open.png')
        self.get_widget('image_quick_open').set_from_file(ipath)

        # Model format:
        # 0: the keybinding path in gsettings (str, hidden),
        # 1: label (str)
        # 2: human readable accelerator (str)
        # 3: gtk accelerator (str, hidden)
        self.store = Gtk.TreeStore(str, str, str, str)
        treeview = self.get_widget('treeview-keys')
        treeview.set_model(self.store)
        treeview.set_rules_hint(True)

        # TODO PORT this is killing the editing of the accl
        # treeview.connect('button-press-event', self.start_editing)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_('Action'), renderer, text=1)
        column.set_property('expand', True)
        treeview.append_column(column)

        renderer = Gtk.CellRendererAccel()
        renderer.set_property('editable', True)
        renderer.connect('accel-edited', self.on_accel_edited)
        renderer.connect('accel-cleared', self.on_accel_cleared)
        column = Gtk.TreeViewColumn(_('Shortcut'), renderer, text=2)
        column.pack_start(renderer, True)
        column.set_property('expand', False)
        column.add_attribute(renderer, "accel-mods", 0)
        column.add_attribute(renderer, "accel-key", 1)
        treeview.append_column(column)

        self.demo_terminal = GuakeTerminal(self.settings)
        self.demo_terminal_box = self.get_widget('demo_terminal_box')
        self.demo_terminal_box.add(self.demo_terminal)

        pid = self.spawn_sync_pid(None, self.demo_terminal)

        self.demo_terminal.pid = pid

        self.populate_shell_combo()
        self.populate_keys_tree()
        self.populate_display_n()
        self.load_configs()
        self.get_widget('config-window').hide()

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

        if isinstance(directory, str):
            wd = directory
        else:
            wd = os.environ['HOME']

        pid = terminal.spawn_sync(
            Vte.PtyFlags.DEFAULT, wd, argv, [], GLib.SpawnFlags.DO_NOT_REAP_CHILD, None, None, None
        )
        return pid

    def show(self):
        """Calls the main window show_all method and presents the
        window in the desktop.
        """
        self.get_widget('config-window').show_all()
        self.get_widget('config-window').present()

    def hide(self):
        """Calls the main window hide function.
        """
        self.get_widget('config-window').hide()

    def on_destroy(self, window):
        self.demo_terminal.kill()
        self.demo_terminal.destroy()

    def toggle_prompt_on_quit_sensitivity(self, combo):
        """If toggle_on_close_tabs is set to 2 (Always), prompt_on_quit has no
        effect.
        """
        self.get_widget('prompt_on_quit').set_sensitive(combo.get_active() != 2)

    def toggle_style_sensitivity(self, chk):
        """If the user chooses to use the gnome default font
        configuration it means that he will not be able to use the
        font selector.
        """
        self.get_widget('font_style').set_sensitive(not chk.get_active())

    def toggle_use_font_background_sensitivity(self, chk):
        """If the user chooses to use the gnome default font
        configuration it means that he will not be able to use the
        font selector.
        """
        self.get_widget('palette_16').set_sensitive(chk.get_active())
        self.get_widget('palette_17').set_sensitive(chk.get_active())

    def toggle_display_n_sensitivity(self, chk):
        """When the user unchecks 'on mouse display', the option to select an
        alternate display should be enabeld.
        """
        self.get_widget('display_n').set_sensitive(not chk.get_active())

    def toggle_quick_open_command_line_sensitivity(self, chk):
        """When the user unchecks 'enable quick open', the command line should be disabled
        """
        self.get_widget('quick_open_command_line').set_sensitive(chk.get_active())
        self.get_widget('quick_open_in_current_terminal').set_sensitive(chk.get_active())

    def toggle_use_vte_titles(self, chk):
        """When vte titles aren't used, there is nothing to abbreviate
        """
        self.update_vte_subwidgets_states()

    def update_vte_subwidgets_states(self):
        do_use_vte_titles = self.get_widget('use_vte_titles').get_active()
        max_tab_name_length_wdg = self.get_widget('max_tab_name_length')
        max_tab_name_length_wdg.set_sensitive(do_use_vte_titles)
        self.get_widget('lbl_max_tab_name_length').set_sensitive(do_use_vte_titles)
        self.get_widget('abbreviate_tab_names').set_sensitive(do_use_vte_titles)

    def on_reset_compat_defaults_clicked(self, bnt):
        """Reset default values to compat_{backspace,delete} gconf
        keys. The default values are retrivied from the guake.schemas
        file.
        """
        self.settings.general.reset('compat-backspace')
        self.settings.general.reset('compat-delete')
        self.reload_erase_combos()

    def on_palette_name_changed(self, combo):
        """Changes the value of palette in gconf
        """
        palette_name = combo.get_active_text()
        if palette_name not in PALETTES:
            return
        self.settings.styleFont.set_string('palette', PALETTES[palette_name])
        self.settings.styleFont.set_string('palette-name', palette_name)
        self.set_palette_colors(PALETTES[palette_name])
        self.update_demo_palette(PALETTES[palette_name])

    def on_cursor_shape_changed(self, combo):
        """Changes the value of cursor_shape in gconf
        """
        index = combo.get_active()
        self.settings.style.set_int('cursor-shape', index)

    def on_blink_cursor_toggled(self, chk):
        """Changes the value of blink_cursor in gconf
        """
        self.settings.style.set_int('cursor-blink-mode', chk.get_active())

    def on_palette_color_set(self, btn):
        """Changes the value of palette in gconf
        """

        palette = []
        for i in range(18):
            palette.append(hexify_color(self.get_widget('palette_%d' % i).get_color()))
        palette = ':'.join(palette)
        self.settings.styleFont.set_string('palette', palette)
        self.settings.styleFont.set_string('palette-name', _('Custom'))
        self.set_palette_name('Custom')
        self.update_demo_palette(palette)

    # this methods should be moved to the GuakeTerminal class FROM HERE

    def set_palette_name(self, palette_name):
        """If the given palette matches an existing one, shows it in the
        combobox
        """
        combo = self.get_widget('palette_name')
        found = False
        log.debug("wanting palette: %r", palette_name)
        for i in combo.get_model():
            if i[0] == palette_name:
                combo.set_active_iter(i.iter)
                found = True
                break
        if not found:
            combo.set_active(self.custom_palette_index)

    def update_demo_palette(self, palette):
        self.set_colors_from_settings()

    def set_colors_from_settings(self):
        transparency = self.settings.styleBackground.get_int('transparency')
        colorRGBA = Gdk.RGBA(0, 0, 0, 0)
        palette_list = list()
        for color in self.settings.styleFont.get_string("palette").split(':'):
            colorRGBA.parse(color)
            palette_list.append(colorRGBA.copy())

        if len(palette_list) > 16:
            bg_color = palette_list[17]
        else:
            bg_color = Gdk.RGBA(255, 255, 255, 0)

            bg_color.alpha = 1 / 100 * transparency

        if len(palette_list) > 16:
            font_color = palette_list[16]
        else:
            font_color = Gdk.RGBA(0, 0, 0, 0)

        self.demo_terminal.set_color_foreground(font_color)
        self.demo_terminal.set_color_bold(font_color)
        self.demo_terminal.set_colors(font_color, bg_color, palette_list[:16])

    # TO HERE (see above)
    def fill_palette_names(self):
        combo = self.get_widget('palette_name')
        for palette in sorted(PALETTES):
            combo.append_text(palette)
        self.custom_palette_index = len(PALETTES)
        combo.append_text(_('Custom'))

    def set_cursor_shape(self, shape_index):
        self.get_widget('cursor_shape').set_active(shape_index)

    def set_cursor_blink_mode(self, mode_index):
        self.get_widget('cursor_blink_mode').set_active(mode_index)

    def set_palette_colors(self, palette):
        """Updates the color buttons with the given palette
        """
        palette = palette.split(':')
        for i, pal in enumerate(palette):
            x, color = Gdk.Color.parse(pal)
            self.get_widget('palette_%d' % i).set_color(color)

    def reload_erase_combos(self, btn=None):
        """Read from gconf the value of compat_{backspace,delete} vars
        and select the right option in combos.
        """
        # backspace erase binding
        combo = self.get_widget('backspace-binding-combobox')
        binding = self.settings.general.get_string('compat-backspace')
        for i in combo.get_model():
            if ERASE_BINDINGS.get(i[0]) == binding:
                combo.set_active_iter(i.iter)

        # delete erase binding
        combo = self.get_widget('delete-binding-combobox')
        binding = self.settings.general.get_string('compat-delete')
        for i in combo.get_model():
            if ERASE_BINDINGS.get(i[0]) == binding:
                combo.set_active_iter(i.iter)

    def _load_hooks_settings(self):
        """load hooks settings"""
        log.debug("executing _load_hooks_settings")
        hook_show_widget = self.get_widget("hook_show")
        hook_show_setting = self.settings.hooks.get_string("show")
        if hook_show_widget is not None:
            if hook_show_setting is not None:
                hook_show_widget.set_text(hook_show_setting)
        return

    def _load_default_shell_settings(self):
        combo = self.get_widget('default_shell')
        # get the value for defualt shell. If unset, set to USER_SHELL_VALUE.
        value = self.settings.general.get_string('default-shell') or USER_SHELL_VALUE
        for i in combo.get_model():
            if i[0] == value:
                combo.set_active_iter(i.iter)

    def _load_screen_settings(self):
        """Load screen settings"""
        # display number / use primary display
        combo = self.get_widget('display_n')
        dest_screen = self.settings.general.get_int('display-n')
        # If Guake is configured to use a screen that is not currently attached,
        # default to 'primary display' option.
        screen = self.get_widget('config-window').get_screen()
        n_screens = screen.get_n_monitors()
        if dest_screen > n_screens - 1:
            self.settings.general.set_boolean('mouse-display', False)
            dest_screen = screen.get_primary_monitor()
            self.settings.general.set_int('display_n', dest_screen)

        if dest_screen == ALWAYS_ON_PRIMARY:
            first_item = combo.get_model().get_iter_first()
            combo.set_active_iter(first_item)
        else:
            seen_first = False  # first item "always on primary" is special
            for i in combo.get_model():
                if seen_first:
                    i_int = int(i[0].split()[0])  # extracts 1 from '1' or from '1 (primary)'
                    if i_int == dest_screen:
                        combo.set_active_iter(i.iter)
                else:
                    seen_first = True

    def load_configs(self):
        """Load configurations for all widgets in General, Scrolling
        and Appearance tabs from gconf.
        """
        self._load_default_shell_settings()

        # login shell
        value = self.settings.general.get_boolean('use-login-shell')
        self.get_widget('use_login_shell').set_active(value)

        # tray icon
        value = self.settings.general.get_boolean('use-trayicon')
        self.get_widget('use_trayicon').set_active(value)

        # popup
        value = self.settings.general.get_boolean('use-popup')
        self.get_widget('use_popup').set_active(value)

        # prompt on quit
        value = self.settings.general.get_boolean('prompt-on-quit')
        self.get_widget('prompt_on_quit').set_active(value)

        # prompt on close_tab
        value = self.settings.general.get_int('prompt-on-close-tab')
        self.get_widget('prompt_on_close_tab').set_active(value)
        self.get_widget('prompt_on_quit').set_sensitive(value != 2)

        # ontop
        value = self.settings.general.get_boolean('window-ontop')
        self.get_widget('window_ontop').set_active(value)

        # tab ontop
        value = self.settings.general.get_boolean('tab-ontop')
        self.get_widget('tab_ontop').set_active(value)

        # refocus
        value = self.settings.general.get_boolean('window-refocus')
        self.get_widget('window_refocus').set_active(value)

        # losefocus
        value = self.settings.general.get_boolean('window-losefocus')
        self.get_widget('window_losefocus').set_active(value)

        # use VTE titles
        value = self.settings.general.get_boolean('use-vte-titles')
        self.get_widget('use_vte_titles').set_active(value)

        # set window title
        value = self.settings.general.get_boolean('set-window-title')
        self.get_widget('set_window_title').set_active(value)

        # abbreviate tab names
        self.get_widget('abbreviate_tab_names').set_sensitive(value)
        value = self.settings.general.get_boolean('abbreviate-tab-names')
        self.get_widget('abbreviate_tab_names').set_active(value)

        # max tab name length
        value = self.settings.general.get_int('max-tab-name-length')
        self.get_widget('max_tab_name_length').set_value(value)

        self.update_vte_subwidgets_states()

        value = self.settings.general.get_int('window-height')
        self.get_widget('window_height').set_value(value)

        value = self.settings.general.get_int('window-width')
        self.get_widget('window_width').set_value(value)

        # window displacements
        value = self.settings.general.get_int('window-vertical-displacement')
        self.get_widget('window_vertical_displacement').set_value(value)

        value = self.settings.general.get_int('window-horizontal-displacement')
        self.get_widget('window_horizontal_displacement').set_value(value)

        value = self.settings.general.get_int('window-halignment')
        which_button = {
            ALIGN_RIGHT: 'radiobutton_align_right',
            ALIGN_LEFT: 'radiobutton_align_left',
            ALIGN_CENTER: 'radiobutton_align_center'
        }
        self.get_widget(which_button[value]).set_active(True)
        self.get_widget("window_horizontal_displacement").set_sensitive(value != ALIGN_CENTER)

        value = self.settings.general.get_boolean('open-tab-cwd')
        self.get_widget('open_tab_cwd').set_active(value)

        # tab bar
        value = self.settings.general.get_boolean('window-tabbar')
        self.get_widget('window_tabbar').set_active(value)

        # start fullscreen
        value = self.settings.general.get_boolean('start-fullscreen')
        self.get_widget('start_fullscreen').set_active(value)

        # use audible bell
        value = self.settings.general.get_boolean('use-audible-bell')
        self.get_widget('use_audible_bell').set_active(value)

        self._load_screen_settings()

        value = self.settings.general.get_boolean('quick-open-enable')
        self.get_widget('quick_open_enable').set_active(value)
        self.get_widget('quick_open_command_line').set_sensitive(value)
        self.get_widget('quick_open_in_current_terminal').set_sensitive(value)
        text = Gtk.TextBuffer()
        text = self.get_widget('quick_open_supported_patterns').get_buffer()
        for title, matcher, _useless in QUICK_OPEN_MATCHERS:
            text.insert_at_cursor("%s: %s\n" % (title, matcher))
        self.get_widget('quick_open_supported_patterns').set_buffer(text)

        value = self.settings.general.get_string('quick-open-command-line')
        if value is None:
            value = "subl %(file_path)s:%(line_number)s"
        self.get_widget('quick_open_command_line').set_text(value)

        value = self.settings.general.get_boolean('quick-open-in-current-terminal')
        self.get_widget('quick_open_in_current_terminal').set_active(value)

        value = self.settings.general.get_string('startup-script')
        if value:
            self.get_widget('startup_script').set_text(value)

        # use display where the mouse is currently
        value = self.settings.general.get_boolean('mouse-display')
        self.get_widget('mouse_display').set_active(value)

        # scrollbar
        value = self.settings.general.get_boolean('use-scrollbar')
        self.get_widget('use_scrollbar').set_active(value)

        # history size
        value = self.settings.general.get_int('history-size')
        self.get_widget('history_size').set_value(value)

        # infinite history
        value = self.settings.general.get_boolean('infinite-history')
        self.get_widget('infinite_history').set_active(value)
        print("infinite history: ", value)

        # scroll output
        value = self.settings.general.get_boolean('scroll-output')
        self.get_widget('scroll_output').set_active(value)

        # scroll keystroke
        value = self.settings.general.get_boolean('scroll-keystroke')
        self.get_widget('scroll_keystroke').set_active(value)

        # default font
        value = self.settings.general.get_boolean('use-default-font')
        self.get_widget('use_default_font').set_active(value)
        self.get_widget('font_style').set_sensitive(not value)

        # font
        value = self.settings.styleFont.get_string('style')
        if value:
            self.get_widget('font_style').set_font_name(value)

        # allow bold font
        value = self.settings.styleFont.get_boolean('allow-bold')
        self.get_widget('allow_bold').set_active(value)

        # palette
        self.fill_palette_names()
        value = self.settings.styleFont.get_string('palette-name')
        self.set_palette_name(value)
        value = self.settings.styleFont.get_string('palette')
        self.set_palette_colors(value)
        self.update_demo_palette(value)

        # cursor shape
        value = self.settings.style.get_int('cursor-shape')
        self.set_cursor_shape(value)

        # cursor blink
        value = self.settings.style.get_int('cursor-blink-mode')
        self.set_cursor_blink_mode(value)

        value = self.settings.styleBackground.get_int('transparency')
        self.get_widget('background_transparency').set_value(value)

        value = self.settings.general.get_int('window-valignment')
        self.get_widget('top_align').set_active(value)

        # it's a separated method, to be reused.
        self.reload_erase_combos()

        # custom command context-menu configuration file
        custom_command_file = self.settings.general.get_string('custom-command-file')
        if custom_command_file:
            custom_command_file_name = os.path.expanduser(custom_command_file)
        else:
            custom_command_file_name = None
        custom_cmd_filter = Gtk.FileFilter()
        custom_cmd_filter.set_name(_("JSON files"))
        custom_cmd_filter.add_pattern("*.json")
        self.get_widget('custom_command_file_chooser').add_filter(custom_cmd_filter)
        all_files_filter = Gtk.FileFilter()
        all_files_filter.set_name(_("All files"))
        all_files_filter.add_pattern("*")
        self.get_widget('custom_command_file_chooser').add_filter(all_files_filter)
        if custom_command_file_name:
            self.get_widget('custom_command_file_chooser').set_filename(custom_command_file_name)

        # hooks
        self._load_hooks_settings()

    # -- populate functions --

    def populate_shell_combo(self):
        """Read the /etc/shells and looks for installed shells to
        fill the default_shell combobox.
        """
        cb = self.get_widget('default_shell')
        # append user shell as first option
        cb.append_text(USER_SHELL_VALUE)
        if os.path.exists(SHELLS_FILE):
            lines = open(SHELLS_FILE).readlines()
            for i in lines:
                possible = i.strip()
                if possible and not possible.startswith('#') and os.path.exists(possible):
                    cb.append_text(possible)

        for i in get_binaries_from_path(PYTHONS):
            cb.append_text(i)

    def populate_keys_tree(self):
        """Reads the HOTKEYS global variable and insert all data in
        the TreeStore used by the preferences window treeview.
        """
        for group in HOTKEYS:
            parent = self.store.append(None, [None, group['label'], None, None])
            for item in group['keys']:
                if item['key'] == "show-hide" or item['key'] == "show-focus":
                    accel = self.settings.keybindingsGlobal.get_string(item['key'])
                else:
                    accel = self.settings.keybindingsLocal.get_string(item['key'])
                gsettings_path = item['key']
                keycode, mask = Gtk.accelerator_parse(accel)
                keylabel = Gtk.accelerator_get_label(keycode, mask)
                self.store.append(parent, [gsettings_path, item['label'], keylabel, accel])
        self.get_widget('treeview-keys').expand_all()

    def populate_display_n(self):
        """Get the number of displays and populate this drop-down box
        with them all. Prepend the "always on primary" option.
        """
        cb = self.get_widget('display_n')
        screen = self.get_widget('config-window').get_screen()

        cb.append_text("always on primary")

        for m in range(0, int(screen.get_n_monitors())):
            if m == int(screen.get_primary_monitor()):
                # TODO l10n
                cb.append_text(str(m) + ' ' + '(primary)')
            else:
                cb.append_text(str(m))

    # -- key handling --

    def on_accel_edited(self, cellrendereraccel, path, key, mods, hwcode):
        """Callback that handles key edition in cellrenderer. It makes
        some tests to validate the key, like looking for already in
        use keys and look for [A-Z][a-z][0-9] to avoid problems with
        these common keys. If all tests are ok, the value will be
        stored in gconf.
        """
        accelerator = Gtk.accelerator_name(key, mods)

        dconf_path = self.store[path][HOTKET_MODEL_INDEX_DCONF]
        old_accel = self.store[path][HOTKET_MODEL_INDEX_HUMAN_ACCEL]
        keylabel = Gtk.accelerator_get_label(key, mods)

        # we needn't to change anything, the user is trying to set the
        # same key that is already set.
        if old_accel == accelerator:
            return False

        self.hotkey_alread_used = False

        # looking for already used keybindings

        def each_key(model, path, subiter):
            keyentry = model.get_value(subiter, HOTKET_MODEL_INDEX_ACCEL)
            if keyentry and keyentry == accelerator:
                self.hotkey_alread_used = True
                msg = _("The shortcut \"%s\" is already in use.") % html_escape(accelerator)
                ShowableError(self.window, _('Error setting keybinding.'), msg, -1)
                raise Exception('This is ok, we just use it to break the foreach loop!')

        self.store.foreach(each_key)
        if self.hotkey_alread_used:
            return False

        # avoiding problems with common keys
        if ((mods == 0 and key != 0) and
            ((key >= ord('a') and key <= ord('z')) or (key >= ord('A') and key <= ord('Z')) or
             (key >= ord('0') and key <= ord('9')))):
            dialog = Gtk.MessageDialog(
                self.get_widget('config-window'),
                Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                Gtk.MessageType.WARNING, Gtk.ButtonsType.OK,
                _(
                    "The shortcut \"%s\" cannot be used "
                    "because it will become impossible to "
                    "type using this key.\n\n"
                    "Please try with a key such as "
                    "Control, Alt or Shift at the same "
                    "time.\n"
                ) % html_escape(key)
            )
            dialog.run()
            dialog.destroy()
            return False

        self.store[path][HOTKET_MODEL_INDEX_HUMAN_ACCEL] = keylabel

        if dconf_path == "show-hide" or dconf_path == "show-focus":
            self.settings.keybindingsGlobal.set_string(dconf_path, accelerator)
        else:
            self.settings.keybindingsLocal.set_string(dconf_path, accelerator)
        self.store[path][HOTKET_MODEL_INDEX_ACCEL] = accelerator

    def on_accel_cleared(self, cellrendereraccel, path):
        """If the user tries to clear a keybinding with the backspace
        key this callback will be called and it just fill the model
        with an empty key and set the 'disabled' string in gconf path.
        """
        dconf_path = self.store[path][HOTKET_MODEL_INDEX_DCONF]

        if dconf_path == "show-hide":
            # cannot disable 'show-hide' hotkey
            log.warn("Cannot disable 'show-hide' hotkey")
            self.settings.keybindingsGlobal.set_string(dconf_path, old_accel)
        else:
            self.store[path][HOTKET_MODEL_INDEX_HUMAN_ACCEL] = ""
            self.store[path][HOTKET_MODEL_INDEX_ACCEL] = "None"
            if dconf_path == "show-focus":
                self.settings.keybindingsGlobal.set_string(dconf_path, 'disabled')
            else:
                self.settings.keybindingsLocal.set_string(dconf_path, 'disabled')

    def start_editing(self, treeview, event):
        """Make the treeview grab the focus and start editing the cell
        that the user has clicked to avoid confusion with two or three
        clicks before editing a keybinding.

        Thanks to gnome-keybinding-properties.c =)
        """
        # TODO PORT some thing in here is breaking stuff

        if event.window != treeview.get_bin_window():
            return False

        x, y = int(event.x), int(event.y)
        ret = treeview.get_path_at_pos(x, y)
        if not ret:
            return False

        path, column, cellx, celly = ret
        if path and len(path) > 1:

            def real_cb():
                treeview.grab_focus()
                treeview.set_cursor(path, column, True)

            treeview.stop_emission('button-press-event')
            GObject.idle_add(real_cb)

        return True


class KeyEntry(object):

    def __init__(self, keycode, mask):
        self.keycode = keycode
        self.mask = mask

    def __repr__(self):
        return u'KeyEntry(%d, %d)' % (self.keycode, self.mask)

    def __eq__(self, rval):
        return self.keycode == rval.keycode and self.mask == rval.mask


def setup_standalone_signals(instance):
    """Called when prefs dialog is running in standalone mode. It
    makes the delete event of dialog and click on close button finish
    the application.
    """
    window = instance.get_widget('config-window')
    window.connect('delete-event', Gtk.main_quit)

    # We need to block the execution of the already associated
    # callback before connecting the new handler.
    button = instance.get_widget('button1')
    button.handler_block_by_func(instance.gtk_widget_destroy)
    button.connect('clicked', Gtk.main_quit)

    return instance


if __name__ == '__main__':
    bindtextdomain(NAME, LOCALE_DIR)
    setup_standalone_signals(PrefsDialog(None)).show()
    Gtk.main()

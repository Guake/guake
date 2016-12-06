#!/usr/bin/env python
# -*- coding: utf-8; -*-
#
# Copyright (C) 2007-2013 Guake authors
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA 02110-1301 USA
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import gconf
import gobject
import gtk
import logging
import os
import re
import warnings

from pango import FontDescription

from guake.common import ShowableError
from guake.common import _
from guake.common import get_binaries_from_path
from guake.common import gladefile
from guake.common import hexify_color
from guake.common import pixmapfile
from guake.globals import ALIGN_CENTER
from guake.globals import ALIGN_LEFT
from guake.globals import ALIGN_RIGHT
from guake.globals import ALWAYS_ON_PRIMARY
from guake.globals import GKEY
from guake.globals import KEY
from guake.globals import LKEY
from guake.globals import LOCALE_DIR
from guake.globals import NAME
from guake.palettes import PALETTES
from guake.simplegladeapp import SimpleGladeApp
from guake.simplegladeapp import bindtextdomain
from guake.terminal import GuakeTerminal
from guake.terminal import QUICK_OPEN_MATCHERS

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
ERASE_BINDINGS = {'ASCII DEL': 'ascii-delete',
                  'Escape sequence': 'delete-sequence',
                  'Control-H': 'ascii-backspace'}

HOTKEYS = [
    {'label': _('General'),
     'keys': [{'key': GKEY('show_hide'),
               'label': _('Toggle Guake visibility')},
              {'key': LKEY('toggle_fullscreen'),
               'label': _('Toggle Fullscreen')},
              {'key': LKEY('toggle_hide_on_lose_focus'),
               'label': _('Toggle Hide on Lose Focus')},
              {'key': LKEY('quit'),
               'label': _('Quit')},
              {'key': LKEY('reset_terminal'),
               'label': _('Reset terminal')},
              ]},

    {'label': _('Tab management'),
     'keys': [{'key': LKEY('new_tab'),
               'label': _('New tab')},
              {'key': LKEY('close_tab'),
               'label': _('Close tab')},
              {'key': LKEY('rename_current_tab'),
               'label': _('Rename current tab')},
              ]},

    {'label': _('Navigation'),
     'keys': [{'key': LKEY('previous_tab'),
               'label': _('Go to previous tab')},
              {'key': LKEY('next_tab'),
               'label': _('Go to next tab')},
              {'key': LKEY('move_tab_left'),
               'label': _('Move current tab left')},
              {'key': LKEY('move_tab_right'),
               'label': _('Move current tab right')},
              {'key': LKEY('switch_tab1'),
               'label': _('Go to first tab')},
              {'key': LKEY('switch_tab2'),
               'label': _('Go to second tab')},
              {'key': LKEY('switch_tab3'),
               'label': _('Go to third tab')},
              {'key': LKEY('switch_tab4'),
               'label': _('Go to fourth tab')},
              {'key': LKEY('switch_tab5'),
               'label': _('Go to fifth tab')},
              {'key': LKEY('switch_tab6'),
               'label': _('Go to sixth tab')},
              {'key': LKEY('switch_tab7'),
               'label': _('Go to seventh tab')},
              {'key': LKEY('switch_tab8'),
               'label': _('Go to eighth tab')},
              {'key': LKEY('switch_tab9'),
               'label': _('Go to ninth tab')},
              {'key': LKEY('switch_tab10'),
               'label': _('Go to tenth tab')},
              {'key': LKEY('switch_tab_last'),
               'label': _('Go to last tab')},
              ]},

    {'label': _('Appearance'),
     'keys': [{'key': LKEY('zoom_out'),
               'label': _('Zoom out')},
              {'key': LKEY('zoom_in'),
               'label': _('Zoom in')},
              {'key': LKEY('zoom_in_alt'),
               'label': _('Zoom in (alternative)')},
              {'key': LKEY('increase_height'),
               'label': _('Increase height')},
              {'key': LKEY('decrease_height'),
               'label': _('Decrease height')},
              {'key': LKEY('increase_transparency'),
               'label': _('Increase transparency')},
              {'key': LKEY('decrease_transparency'),
               'label': _('Decrease transparency')},
              {'key': LKEY('toggle_transparency'),
               'label': _('Toggle transparency')}
              ]},

    {'label': _('Clipboard'),
     'keys': [{'key': LKEY('clipboard_copy'),
               'label': _('Copy text to clipboard')},
              {'key': LKEY('clipboard_paste'),
               'label': _('Paste text from clipboard')},
              ]},

    {'label': _('Extra features'),
     'keys': [
        {'key': LKEY('search_on_web'),
         'label': _('Search select text on web')},
    ]},
]


class PrefsCallbacks(object):

    """Holds callbacks that will be used in the PrefsDialg class.
    """

    def __init__(self, prefDlg):
        self.client = gconf.client_get_default()
        self.prefDlg = prefDlg

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
            self.client.unset(KEY('/general/default_shell'))
        else:
            self.client.set_string(KEY('/general/default_shell'), shell)

    def on_use_login_shell_toggled(self, chk):
        """Changes the activity of use_login_shell in gconf
        """
        self.client.set_bool(KEY('/general/use_login_shell'), chk.get_active())

    def on_open_tab_cwd_toggled(self, chk):
        """Changes the activity of open_tab_cwd in gconf
        """
        self.client.set_bool(KEY('/general/open_tab_cwd'), chk.get_active())

    def on_use_trayicon_toggled(self, chk):
        """Changes the activity of use_trayicon in gconf
        """
        self.client.set_bool(KEY('/general/use_trayicon'), chk.get_active())

    def on_use_popup_toggled(self, chk):
        """Changes the activity of use_popup in gconf
        """
        self.client.set_bool(KEY('/general/use_popup'), chk.get_active())

    def on_prompt_on_quit_toggled(self, chk):
        """Set the `prompt on quit' property in gconf
        """
        self.client.set_bool(KEY('/general/prompt_on_quit'), chk.get_active())

    def on_prompt_on_close_tab_changed(self, combo):
        """Set the `prompt_on_close_tab' property in gconf
        """
        self.client.set_int(KEY('/general/prompt_on_close_tab'), combo.get_active())

    def on_window_ontop_toggled(self, chk):
        """Changes the activity of window_ontop in gconf
        """
        self.client.set_bool(KEY('/general/window_ontop'), chk.get_active())

    def on_tab_ontop_toggled(self, chk):
        """Changes the activity of tab_ontop in gconf
        """
        self.client.set_bool(KEY('/general/tab_ontop'), chk.get_active())

    def on_quick_open_enable_toggled(self, chk):
        """Changes the activity of quick_open_enable in gconf
        """
        self.client.set_bool(KEY('/general/quick_open_enable'), chk.get_active())

    def on_quick_open_in_current_terminal_toggled(self, chk):
        self.client.set_bool(KEY('/general/quick_open_in_current_terminal'), chk.get_active())

    def on_startup_script_changed(self, edt):
        self.client.set_string(KEY('/general/startup_script'), edt.get_text())

    def on_window_losefocus_toggled(self, chk):
        """Changes the activity of window_losefocus in gconf
        """
        self.client.set_bool(KEY('/general/window_losefocus'), chk.get_active())

    def on_quick_open_command_line_changed(self, edt):
        self.client.set_string(KEY('/general/quick_open_command_line'), edt.get_text())

    def on_hook_show_changed(self, edt):
        self.client.set_string(KEY('/hooks/show'), edt.get_text())

    def on_window_tabbar_toggled(self, chk):
        """Changes the activity of window_tabbar in gconf
        """
        self.client.set_bool(KEY('/general/window_tabbar'), chk.get_active())

    def on_start_fullscreen_toggled(self, chk):
        """Changes the activity of start_fullscreen in gconf
        """
        self.client.set_bool(KEY('/general/start_fullscreen'), chk.get_active())

    def on_use_vte_titles_toggled(self, chk):
        """Save `use_vte_titles` property value in gconf
        """
        self.client.set_bool(KEY('/general/use_vte_titles'), chk.get_active())

    def on_abbreviate_tab_names_toggled(self, chk):
        """Save `abbreviate_tab_names` property value in gconf
        """
        self.client.set_bool(KEY('/general/abbreviate_tab_names'), chk.get_active())

    def on_max_tab_name_length_changed(self, spin):
        """Changes the value of max_tab_name_length in gconf
        """
        val = int(spin.get_value())
        self.client.set_int(KEY('/general/max_tab_name_length'), val)
        self.prefDlg.update_vte_subwidgets_states()

    def on_mouse_display_toggled(self, chk):
        """Set the 'appear on mouse display' preference in gconf. This
        property supercedes any value stored in display_n.
        """
        self.client.set_bool(KEY('/general/mouse_display'), chk.get_active())

    def on_right_align_toggled(self, chk):
        """set the horizontal alignment setting.
        """
        v = chk.get_active()
        self.client.set_int(KEY('/general/window_halignment'), 1 if v else 0)

    def on_bottom_align_toggled(self, chk):
        """set the vertical alignment setting.
        """
        v = chk.get_active()
        self.client.set_int(KEY('/general/window_valignment'), 1 if v else 0)

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
        self.client.set_int(KEY('/general/display_n'), val_int)

    def on_window_height_value_changed(self, hscale):
        """Changes the value of window_height in gconf
        """
        val = hscale.get_value()
        self.client.set_int(KEY('/general/window_height'), int(val))
        self.client.set_float(KEY('/general/window_height_f'), float(val))

    def on_window_width_value_changed(self, wscale):
        """Changes the value of window_width in gconf
        """
        val = wscale.get_value()
        self.client.set_int(KEY('/general/window_width'), int(val))
        self.client.set_float(KEY('/general/window_width_f'), float(val))

    def on_window_halign_value_changed(self, halign_button):
        """Changes the value of window_halignment in gconf
        """
        if halign_button.get_active():
            which_align = {
                'radiobutton_align_left': ALIGN_LEFT,
                'radiobutton_align_right': ALIGN_RIGHT,
                'radiobutton_align_center': ALIGN_CENTER
            }
            self.client.set_int(KEY('/general/window_halignment'),
                                which_align[halign_button.get_name()])

    def on_use_visible_bell_toggled(self, chk):
        """Changes the value of use_visible_bell in gconf
        """
        self.client.set_bool(KEY('/general/use_visible_bell'), chk.get_active())

    def on_use_audible_bell_toggled(self, chk):
        """Changes the value of use_audible_bell in gconf
        """
        self.client.set_bool(KEY('/general/use_audible_bell'), chk.get_active())

    # scrolling tab

    def on_use_scrollbar_toggled(self, chk):
        """Changes the activity of use_scrollbar in gconf
        """
        self.client.set_bool(KEY('/general/use_scrollbar'), chk.get_active())

    def on_history_size_value_changed(self, spin):
        """Changes the value of history_size in gconf
        """
        val = int(spin.get_value())
        self.client.set_int(KEY('/general/history_size'), val)

    def on_scroll_output_toggled(self, chk):
        """Changes the activity of scroll_output in gconf
        """
        self.client.set_bool(KEY('/general/scroll_output'), chk.get_active())

    def on_scroll_keystroke_toggled(self, chk):
        """Changes the activity of scroll_keystroke in gconf
        """
        self.client.set_bool(KEY('/general/scroll_keystroke'), chk.get_active())

    # appearance tab

    def on_use_default_font_toggled(self, chk):
        """Changes the activity of use_default_font in gconf
        """
        self.client.set_bool(KEY('/general/use_default_font'), chk.get_active())

    def on_show_resizer_toggled(self, chk):
        """Changes the activity of show_resizer in gconf
        """
        self.client.set_bool(KEY('/general/show_resizer'), chk.get_active())

    def on_allow_bold_toggled(self, chk):
        """Changes the value of allow_bold in gconf
        """
        self.client.set_bool(KEY('/style/font/allow_bold'), chk.get_active())

    def on_use_palette_font_and_background_color_toggled(self, chk):
        """Changes the activity of use_palette_font_and_background_color in gconf
        """
        self.client.set_bool(
            KEY('/general/use_palette_font_and_background_color'), chk.get_active())

    def on_font_style_font_set(self, fbtn):
        """Changes the value of font_style in gconf
        """
        self.client.set_string(KEY('/style/font/style'), fbtn.get_font_name())

    def on_font_color_color_set(self, btn):
        """Changes the value of font_color in gconf
        """
        color = hexify_color(btn.get_color())
        self.client.set_string(KEY('/style/font/color'), color)

    def on_background_color_color_set(self, btn):
        """Changes the value of background_color in gconf
        """
        color = hexify_color(btn.get_color())
        self.client.set_string(KEY('/style/background/color'), color)

    def on_background_image_changed(self, btn):
        """Changes the value of background_image in gconf
        """
        filename = btn.get_filename()
        if os.path.isfile(filename or ''):
            self.client.set_string(KEY('/style/background/image'), filename)

    def on_transparency_value_changed(self, hscale):
        """Changes the value of background_transparency in gconf
        """
        value = hscale.get_value()
        self.client.set_int(KEY('/style/background/transparency'), int(value))

    # compatibility tab

    def on_backspace_binding_changed(self, combo):
        """Changes the value of compat_backspace in gconf
        """
        val = combo.get_active_text()
        self.client.set_string(KEY('/general/compat_backspace'),
                               ERASE_BINDINGS[val])

    def on_delete_binding_changed(self, combo):
        """Changes the value of compat_delete in gconf
        """
        val = combo.get_active_text()
        self.client.set_string(KEY('/general/compat_delete'),
                               ERASE_BINDINGS[val])

    def on_custom_command_file_chooser_file_changed(self, filechooser):
        self.client.set_string(KEY('/general/custom_command_file'), filechooser.get_filename())


class PrefsDialog(SimpleGladeApp):

    """The Guake Preferences dialog.
    """

    def __init__(self):
        """Setup the preferences dialog interface, loading images,
        adding filters to file choosers and connecting some signals.
        """
        super(PrefsDialog, self).__init__(gladefile('prefs.glade'),
                                          root='config-window')
        self.add_callbacks(PrefsCallbacks(self))

        self.client = gconf.client_get_default()

        # window cleanup handler
        self.get_widget('config-window').connect('destroy', self.on_destroy)

        # setting evtbox title bg
        eventbox = self.get_widget('eventbox-title')
        eventbox.modify_bg(gtk.STATE_NORMAL,
                           eventbox.get_colormap().alloc_color("#ffffff"))

        # images
        ipath = pixmapfile('guake-notification.png')
        self.get_widget('image_logo').set_from_file(ipath)
        ipath = pixmapfile('quick-open.png')
        self.get_widget('image_quick_open').set_from_file(ipath)

        # the first position in tree will store the keybinding path in gconf,
        # and the user doesn't worry with this, let's hide that =D
        model = gtk.TreeStore(str, str, object, bool)
        treeview = self.get_widget('treeview-keys')
        treeview.set_model(model)
        treeview.set_rules_hint(True)
        treeview.connect('button-press-event', self.start_editing)

        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('keypath', renderer, text=0)
        column.set_visible(False)
        treeview.append_column(column)

        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_('Action'), renderer, text=1)
        column.set_property('expand', True)
        treeview.append_column(column)

        renderer = gtk.CellRendererAccel()
        renderer.set_property('editable', True)

        renderer.connect('accel-edited', self.on_key_edited, model)
        renderer.connect('accel-cleared', self.on_key_cleared, model)

        column = gtk.TreeViewColumn(_('Shortcut'), renderer)
        column.set_cell_data_func(renderer, self.cell_data_func)
        column.set_property('expand', False)
        treeview.append_column(column)

        self.demo_terminal = GuakeTerminal()
        demo_terminal_box = self.get_widget('demo_terminal_box')
        demo_terminal_box.add(self.demo_terminal)

        default_params = {}
        pid = self.demo_terminal.fork_command(**default_params)
        self.demo_terminal.pid = pid

        self.populate_shell_combo()
        self.populate_keys_tree()
        self.populate_display_n()
        self.load_configs()
        self.get_widget('config-window').hide()

        # Preview when selecting a bgimage
        self.selection_preview = gtk.Image()
        self.file_filter = gtk.FileFilter()
        self.file_filter.add_pattern("*.jpg")
        self.file_filter.add_pattern("*.png")
        self.file_filter.add_pattern("*.svg")
        self.file_filter.add_pattern("*.jpeg")
        self.bgfilechooser = self.get_widget('background_image')
        self.bgfilechooser.set_preview_widget(self.selection_preview)
        self.bgfilechooser.set_filter(self.file_filter)
        self.bgfilechooser.connect('update-preview', self.update_preview,
                                   self.selection_preview)

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

    def update_preview(self, file_chooser, preview):
        """Used by filechooser to preview image files
        """
        filename = file_chooser.get_preview_filename()
        if filename and os.path.isfile(filename or ''):
            try:
                mkpb = gtk.gdk.pixbuf_new_from_file_at_size
                pixbuf = mkpb(filename, 256, 256)
                preview.set_from_pixbuf(pixbuf)
                file_chooser.set_preview_widget_active(True)
            except gobject.GError:
                # this exception is raised when user chooses a
                # non-image file or a directory
                warnings.warn('File %s is not an image' % filename)
        else:
            file_chooser.set_preview_widget_active(False)

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

    def clear_background_image(self, btn):
        """Unset the gconf variable that holds the name of the
        background image of all terminals.
        """
        self.client.unset(KEY('/style/background/image'))
        self.bgfilechooser.unselect_all()

    def on_reset_compat_defaults_clicked(self, bnt):
        """Reset default values to compat_{backspace,delete} gconf
        keys. The default values are retrivied from the guake.schemas
        file.
        """
        self.client.unset(KEY('/general/compat_backspace'))
        self.client.unset(KEY('/general/compat_delete'))
        self.reload_erase_combos()

    def on_palette_name_changed(self, combo):
        """Changes the value of palette in gconf
        """
        palette_name = combo.get_active_text()
        if palette_name not in PALETTES:
            return
        self.client.set_string(KEY('/style/font/palette'),
                               PALETTES[palette_name])
        self.client.set_string(KEY('/style/font/palette_name'), palette_name)
        self.set_palette_colors(PALETTES[palette_name])
        self.update_demo_palette(PALETTES[palette_name])

    def on_cursor_shape_changed(self, combo):
        """Changes the value of cursor_shape in gconf
        """
        index = combo.get_active()
        self.client.set_int(KEY('/style/cursor_shape'), index)

    def on_blink_cursor_toggled(self, chk):
        """Changes the value of blink_cursor in gconf
        """
        self.client.set_int(KEY('/style/cursor_blink_mode'), chk.get_active())

    def on_palette_color_set(self, btn):
        """Changes the value of palette in gconf
        """
        palette = []
        for i in range(18):
            palette.append(hexify_color(
                self.get_widget('palette_%d' % i).get_color()))
        palette = ':'.join(palette)
        self.client.set_string(KEY('/style/font/palette'), palette)
        self.client.set_string(KEY('/style/font/palette_name'), _('Custom'))
        self.set_palette_name('Custom')
        self.update_demo_palette(palette)

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
        fgcolor = gtk.gdk.color_parse(
            self.client.get_string(KEY('/style/font/color')))
        bgcolor = gtk.gdk.color_parse(
            self.client.get_string(KEY('/style/background/color')))
        palette = [gtk.gdk.color_parse(color) for color in palette.split(':')]
        font_name = self.client.get_string(KEY('/style/font/style'))
        font = FontDescription(font_name)

        use_palette_font_and_background_color = self.client.get_bool(
            KEY('/general/use_palette_font_and_background_color'))
        if use_palette_font_and_background_color and len(palette) > 16:
            fgcolor = palette[16]
            bgcolor = palette[17]
        self.demo_terminal.set_color_dim(fgcolor)
        self.demo_terminal.set_color_foreground(fgcolor)
        self.demo_terminal.set_color_bold(fgcolor)
        self.demo_terminal.set_color_background(bgcolor)
        self.demo_terminal.set_background_tint_color(bgcolor)
        self.demo_terminal.set_colors(fgcolor, bgcolor, palette[:16])
        self.demo_terminal.set_font(font)

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
            color = gtk.gdk.color_parse(pal)
            self.get_widget('palette_%d' % i).set_color(color)

    def reload_erase_combos(self, btn=None):
        """Read from gconf the value of compat_{backspace,delete} vars
        and select the right option in combos.
        """
        # backspace erase binding
        combo = self.get_widget('backspace-binding-combobox')
        binding = self.client.get_string(KEY('/general/compat_backspace'))
        for i in combo.get_model():
            if ERASE_BINDINGS.get(i[0]) == binding:
                combo.set_active_iter(i.iter)

        # delete erase binding
        combo = self.get_widget('delete-binding-combobox')
        binding = self.client.get_string(KEY('/general/compat_delete'))
        for i in combo.get_model():
            if ERASE_BINDINGS.get(i[0]) == binding:
                combo.set_active_iter(i.iter)

    def _load_hooks_settings(self):
        """load hooks settings"""
        log.debug("executing _load_hooks_settings")
        hook_show_widget = self.get_widget("hook_show")
        hook_show_setting = self.client.get_string(KEY("/hooks/show"))
        if hook_show_widget is not None:
            if hook_show_setting is not None:
                hook_show_widget.set_text(hook_show_setting)
        return

    def _load_default_shell_settings(self):
        combo = self.get_widget('default_shell')
        # get the value for defualt shell. If unset, set to USER_SHELL_VALUE.
        value = self.client.get_string(KEY('/general/default_shell')) or USER_SHELL_VALUE
        for i in combo.get_model():
            if i[0] == value:
                combo.set_active_iter(i.iter)

    def _load_screen_settings(self):
        """Load screen settings"""
        # display number / use primary display
        combo = self.get_widget('display_n')
        dest_screen = self.client.get_int(KEY('/general/display_n'))
        # If Guake is configured to use a screen that is not currently attached,
        # default to 'primary display' option.
        screen = self.get_widget('config-window').get_screen()
        n_screens = screen.get_n_monitors()
        if dest_screen > n_screens - 1:
            self.client.set_bool(KEY('/general/mouse_display'), False)
            dest_screen = screen.get_primary_monitor()
            self.client.set_int(KEY('/general/display_n'), dest_screen)

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
        value = self.client.get_bool(KEY('/general/use_login_shell'))
        self.get_widget('use_login_shell').set_active(value)

        # tray icon
        value = self.client.get_bool(KEY('/general/use_trayicon'))
        self.get_widget('use_trayicon').set_active(value)

        # popup
        value = self.client.get_bool(KEY('/general/use_popup'))
        self.get_widget('use_popup').set_active(value)

        # prompt on quit
        value = self.client.get_bool(KEY('/general/prompt_on_quit'))
        self.get_widget('prompt_on_quit').set_active(value)

        # prompt on close_tab
        value = self.client.get_int(KEY('/general/prompt_on_close_tab'))
        self.get_widget('prompt_on_close_tab').set_active(value)
        self.get_widget('prompt_on_quit').set_sensitive(value != 2)

        # ontop
        value = self.client.get_bool(KEY('/general/window_ontop'))
        self.get_widget('window_ontop').set_active(value)

        # tab ontop
        value = self.client.get_bool(KEY('/general/tab_ontop'))
        self.get_widget('tab_ontop').set_active(value)

        # losefocus
        value = self.client.get_bool(KEY('/general/window_losefocus'))
        self.get_widget('window_losefocus').set_active(value)

        # use VTE titles
        value = self.client.get_bool(KEY('/general/use_vte_titles'))
        self.get_widget('use_vte_titles').set_active(value)

        # abbreviate tab names
        self.get_widget('abbreviate_tab_names').set_sensitive(value)
        value = self.client.get_bool(KEY('/general/abbreviate_tab_names'))
        self.get_widget('abbreviate_tab_names').set_active(value)

        # max tab name length
        value = self.client.get_int(KEY('/general/max_tab_name_length'))
        self.get_widget('max_tab_name_length').set_value(value)

        self.update_vte_subwidgets_states()

        value = self.client.get_float(KEY('/general/window_height_f'))
        if not value:
            value = self.client.get_int(KEY('/general/window_height'))
        self.get_widget('window_height').set_value(value)

        value = self.client.get_float(KEY('/general/window_width_f'))
        if not value:
            value = self.client.get_int(KEY('/general/window_width'))
        self.get_widget('window_width').set_value(value)

        value = self.client.get_int(KEY('/general/window_halignment'))
        which_button = {
            ALIGN_RIGHT: 'radiobutton_align_right',
            ALIGN_LEFT: 'radiobutton_align_left',
            ALIGN_CENTER: 'radiobutton_align_center'
        }
        self.get_widget(which_button[value]).set_active(True)

        value = self.client.get_bool(KEY('/general/open_tab_cwd'))
        self.get_widget('open_tab_cwd').set_active(value)

        # tab bar
        value = self.client.get_bool(KEY('/general/window_tabbar'))
        self.get_widget('window_tabbar').set_active(value)

        # start fullscreen
        value = self.client.get_bool(KEY('/general/start_fullscreen'))
        self.get_widget('start_fullscreen').set_active(value)

        # use visible bell
        value = self.client.get_bool(KEY('/general/use_visible_bell'))
        self.get_widget('use_visible_bell').set_active(value)

        # use audible bell
        value = self.client.get_bool(KEY('/general/use_audible_bell'))
        self.get_widget('use_audible_bell').set_active(value)

        self._load_screen_settings()

        value = self.client.get_bool(KEY('/general/quick_open_enable'))
        self.get_widget('quick_open_enable').set_active(value)
        self.get_widget('quick_open_command_line').set_sensitive(value)
        self.get_widget('quick_open_in_current_terminal').set_sensitive(value)
        text = gtk.TextBuffer()
        text = self.get_widget('quick_open_supported_patterns').get_buffer()
        for title, matcher, _useless in QUICK_OPEN_MATCHERS:
            text.insert_at_cursor("%s: %s\n" % (title, matcher))
        self.get_widget('quick_open_supported_patterns').set_buffer(text)

        value = self.client.get_string(KEY('/general/quick_open_command_line'))
        if value is None:
            value = "subl %(file_path)s:%(line_number)s"
        self.get_widget('quick_open_command_line').set_text(value)

        value = self.client.get_bool(KEY('/general/quick_open_in_current_terminal'))
        self.get_widget('quick_open_in_current_terminal').set_active(value)

        value = self.client.get_string(KEY('/general/startup_script'))
        self.get_widget('startup_script').set_text(value)

        # use display where the mouse is currently
        value = self.client.get_bool(KEY('/general/mouse_display'))
        self.get_widget('mouse_display').set_active(value)

        # scrollbar
        value = self.client.get_bool(KEY('/general/use_scrollbar'))
        self.get_widget('use_scrollbar').set_active(value)

        # history size
        value = self.client.get_int(KEY('/general/history_size'))
        self.get_widget('history_size').set_value(value)

        # scroll output
        value = self.client.get_bool(KEY('/general/scroll_output'))
        self.get_widget('scroll_output').set_active(value)

        # scroll keystroke
        value = self.client.get_bool(KEY('/general/scroll_keystroke'))
        self.get_widget('scroll_keystroke').set_active(value)

        # default font
        value = self.client.get_bool(KEY('/general/use_default_font'))
        self.get_widget('use_default_font').set_active(value)
        self.get_widget('font_style').set_sensitive(not value)

        # resizer visibility
        value = self.client.get_bool(KEY('/general/show_resizer'))
        self.get_widget('show_resizer').set_active(value)

        # use font and background color
        value = self.client.get_bool(KEY('/general/use_palette_font_and_background_color'))
        self.get_widget('use_palette_font_and_background_color').set_active(value)
        self.get_widget('palette_16').set_sensitive(value)
        self.get_widget('palette_17').set_sensitive(value)

        # font
        value = self.client.get_string(KEY('/style/font/style'))
        if value:
            self.get_widget('font_style').set_font_name(value)

        # font color
        val = self.client.get_string(KEY('/style/font/color'))
        try:
            color = gtk.gdk.color_parse(val)
            self.get_widget('font_color').set_color(color)
        except (ValueError, TypeError):
            warnings.warn('Unable to parse color %s' % val, Warning)

        # background color
        value = self.client.get_string(KEY('/style/background/color'))
        try:
            color = gtk.gdk.color_parse(value)
            self.get_widget('background_color').set_color(color)
        except (ValueError, TypeError):
            warnings.warn('Unable to parse color %s' % val, Warning)

        # allow bold font
        value = self.client.get_bool(KEY('/style/font/allow_bold'))
        self.get_widget('allow_bold').set_active(value)

        # palette
        self.fill_palette_names()
        value = self.client.get_string(KEY('/style/font/palette_name'))
        self.set_palette_name(value)
        value = self.client.get_string(KEY('/style/font/palette'))
        self.set_palette_colors(value)
        self.update_demo_palette(value)

        # cursor shape
        value = self.client.get_int(KEY('/style/cursor_shape'))
        self.set_cursor_shape(value)

        # cursor blink
        value = self.client.get_int(KEY('/style/cursor_blink_mode'))
        self.set_cursor_blink_mode(value)

        # background image
        value = self.client.get_string(KEY('/style/background/image'))
        if os.path.isfile(value or ''):
            self.get_widget('background_image').set_filename(value)

        value = self.client.get_int(KEY('/style/background/transparency'))
        self.get_widget('background_transparency').set_value(value)

        value = self.client.get_int(KEY('/general/window_valignment'))
        self.get_widget('top_align').set_active(value)

        # it's a separated method, to be reused.
        self.reload_erase_combos()

        # custom command context-menu configuration file
        custom_command_file = self.client.get_string(KEY('/general/custom_command_file'))
        if custom_command_file:
            custom_command_file_name = os.path.expanduser(custom_command_file)
        else:
            custom_command_file_name = None
        custom_cmd_filter = gtk.FileFilter()
        custom_cmd_filter.set_name(_("JSON files"))
        custom_cmd_filter.add_pattern("*.json")
        self.get_widget('custom_command_file_chooser').add_filter(custom_cmd_filter)
        all_files_filter = gtk.FileFilter()
        all_files_filter.set_name(_("All files"))
        all_files_filter.add_pattern("*")
        self.get_widget('custom_command_file_chooser').add_filter(all_files_filter)
        if custom_command_file_name:
            self.get_widget('custom_command_file_chooser').set_filename(custom_command_file_name)

        # hooks
        self._load_hooks_settings()
        return

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
        model = self.get_widget('treeview-keys').get_model()
        for group in HOTKEYS:
            giter = model.append(None)
            model.set(giter, 0, '', 1, _(group['label']))
            for item in group['keys']:
                child = model.append(giter)
                accel = self.client.get_string(item['key'])
                if accel:
                    params = gtk.accelerator_parse(accel)
                    hotkey = KeyEntry(*params)
                else:
                    hotkey = KeyEntry(0, 0)
                model.set(child,
                          0, item['key'],
                          1, _(item['label']),
                          2, hotkey,
                          3, True)
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

    def on_key_edited(self, renderer, path, keycode, mask, keyval, model):
        """Callback that handles key edition in cellrenderer. It makes
        some tests to validate the key, like looking for already in
        use keys and look for [A-Z][a-z][0-9] to avoid problems with
        these common keys. If all tests are ok, the value will be
        stored in gconf.
        """
        giter = model.get_iter(path)
        gconf_path = model.get_value(giter, 0)

        oldkey = model.get_value(giter, 2)
        hotkey = KeyEntry(keycode, mask)
        key = gtk.accelerator_name(keycode, mask)
        keylabel = gtk.accelerator_get_label(keycode, mask)

        # we needn't to change anything, the user is trying to set the
        # same key that is already set.
        if oldkey == hotkey:
            return False

        # looking for already used keybindings
        def each_key(model, path, subiter):
            keyentry = model.get_value(subiter, 2)
            if keyentry and keyentry == hotkey:
                msg = _("The shortcut \"%s\" is already in use.") % keylabel
                raise ShowableError(_('Error setting keybinding.'), msg, -1)
        model.foreach(each_key)

        # avoiding problems with common keys
        if ((mask == 0 and keycode != 0) and (
            (keycode >= ord('a') and keycode <= ord('z')) or
            (keycode >= ord('A') and keycode <= ord('Z')) or
                (keycode >= ord('0') and keycode <= ord('9')))):
            dialog = gtk.MessageDialog(
                self.get_widget('config-window'),
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
                _("The shortcut \"%s\" cannot be used "
                  "because it will become impossible to "
                  "type using this key.\n\n"
                  "Please try with a key such as "
                  "Control, Alt or Shift at the same "
                  "time.\n") % key)
            dialog.run()
            dialog.destroy()
            return False

        # setting new value in ui
        giter = model.get_iter(path)
        model.set_value(giter, 2, hotkey)

        # setting the new value in gconf
        self.client.set_string(gconf_path, key)

    def on_key_cleared(self, renderer, path, model):
        """If the user tries to clear a keybinding with the backspace
        key this callback will be called and it just fill the model
        with an empty key and set the 'disabled' string in gconf path.
        """
        giter = model.get_iter(path)
        gconf_path = model.get_value(giter, 0)

        self.client.get_string(gconf_path)
        model.set_value(giter, 2, KeyEntry(0, 0))

        self.client.set_string(gconf_path, 'disabled')

    def cell_data_func(self, column, renderer, model, giter):
        """Defines the way that each renderer will handle the key
        object and the mask it sets the properties for a cellrenderer
        key.
        """
        obj = model.get_value(giter, 2)
        if obj:
            renderer.set_property('visible', True)
            renderer.set_property('accel-key', obj.keycode)
            renderer.set_property('accel-mods', obj.mask)
        else:
            renderer.set_property('visible', False)
            renderer.set_property('accel-key', 0)
            renderer.set_property('accel-mods', 0)

    def start_editing(self, treeview, event):
        """Make the treeview grab the focus and start editing the cell
        that the user has clicked to avoid confusion with two or three
        clicks before editing a keybinding.

        Thanks to gnome-keybinding-properties.c =)
        """
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
            gobject.idle_add(real_cb)

        return True


class KeyEntry(object):

    def __init__(self, keycode, mask):
        self.keycode = keycode
        self.mask = mask

    def __repr__(self):
        return u'KeyEntry(%d, %d)' % (
            self.keycode, self.mask)

    def __eq__(self, rval):
        return self.keycode == rval.keycode and self.mask == rval.mask


def setup_standalone_signals(instance):
    """Called when prefs dialog is running in standalone mode. It
    makes the delete event of dialog and click on close button finish
    the application.
    """
    window = instance.get_widget('config-window')
    window.connect('delete-event', gtk.main_quit)

    # We need to block the execution of the already associated
    # callback before connecting the new handler.
    button = instance.get_widget('button1')
    button.handler_block_by_func(instance.gtk_widget_destroy)
    button.connect('clicked', gtk.main_quit)

    return instance

if __name__ == '__main__':
    bindtextdomain(NAME, LOCALE_DIR)
    setup_standalone_signals(PrefsDialog()).show()
    gtk.main()

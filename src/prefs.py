#!/usr/bin/env python
# -*- coding: utf-8; -*-
#
# Copyright (C) 2008 Lincoln de Sousa <lincoln@minaslivre.org>
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
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
from __future__ import absolute_import

import re
import os
import warnings

import gtk
import gobject
import gconf

from guake.simplegladeapp import SimpleGladeApp, bindtextdomain
from guake.globals import NAME, LOCALE_DIR, GCONF_PATH, KEY, ALIGN_LEFT, ALIGN_RIGHT, ALIGN_CENTER
from guake.common import *

# A regular expression to match possible python interpreters when
# filling interpreters combo in preferences
PYTHONS = re.compile('^python\d\.\d$')

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

# Stuff used to build the treeview that will allow the user to change
# keybindings in the preferences window.
LKEY = lambda x:GCONF_PATH+'/keybindings/local/' + x
GKEY = lambda x:GCONF_PATH+'/keybindings/global/' + x

HOTKEYS = [
    {'label': 'General',
     'keys': [{'key': GKEY('show_hide'),
               'label': 'Toggle Guake visibility'},
              {'key': LKEY('toggle_fullscreen'),
               'label': 'Toggle Fullscreen'},
              {'key': LKEY('quit'),
               'label': 'Quit'},
              ]},

    {'label': 'Tab management',
     'keys': [{'key': LKEY('new_tab'),
               'label': 'New tab'},
              {'key': LKEY('close_tab'),
               'label': 'Close tab'},
              {'key': LKEY('rename_tab'),
               'label': 'Rename current tab'},
              ]},

    {'label': 'Navigation',
     'keys': [{'key': LKEY('previous_tab'),
               'label': 'Go to previous tab'},
              {'key': LKEY('next_tab'),
               'label': 'Go to next tab'},
              ]},

    {'label': 'Clipboard',
     'keys': [{'key': LKEY('clipboard_copy'),
               'label': 'Copy text to clipboard'},
              {'key': LKEY('clipboard_paste'),
               'label': 'Paste text from clipboard'},
              ]}
    ]

PALETTES = [
    # tango
    '#000000000000:#cccc00000000:#4e4e9a9a0606:#c4c4a0a00000:#34346565a4a4:'
    '#757550507b7b:#060698209a9a:#d3d3d7d7cfcf:#555557575353:#efef29292929:'
    '#8a8ae2e23434:#fcfce9e94f4f:#72729f9fcfcf:#adad7f7fa8a8:#3434e2e2e2e2:'
    '#eeeeeeeeecec',

    # linux console
    '#000000000000:#aaaa00000000:#0000aaaa0000:#aaaa55550000:#00000000aaaa:'
    '#aaaa0000aaaa:#0000aaaaaaaa:#aaaaaaaaaaaa:#555555555555:#ffff55555555:'
    '#5555ffff5555:#ffffffff5555:#55555555ffff:#ffff5555ffff:#5555ffffffff:'
    '#ffffffffffff',

    # xterm
    '#000000000000:#cdcb00000000:#0000cdcb0000:#cdcbcdcb0000:#1e1a908fffff:'
    '#cdcb0000cdcb:#0000cdcbcdcb:#e5e2e5e2e5e2:#4ccc4ccc4ccc:#ffff00000000:'
    '#0000ffff0000:#ffffffff0000:#46458281b4ae:#ffff0000ffff:#0000ffffffff:'
    '#ffffffffffff',

    # rxvt
    '#000000000000:#cdcd00000000:#0000cdcd0000:#cdcdcdcd0000:#00000000cdcd:'
    '#cdcd0000cdcd:#0000cdcdcdcd:#fafaebebd7d7:#404040404040:#ffff00000000:'
    '#0000ffff0000:#ffffffff0000:#00000000ffff:#ffff0000ffff:#0000ffffffff:'
    '#ffffffffffff'
]

class PrefsCallbacks(object):
    """Holds callbacks that will be used in the PrefsDialg class.
    """

    def __init__(self):
        self.client = gconf.client_get_default()

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

    def on_window_ontop_toggled(self, chk):
        """Changes the activity of window_ontop in gconf
        """
        self.client.set_bool(KEY('/general/window_ontop'), chk.get_active())

    def on_window_losefocus_toggled(self, chk):
        """Changes the activity of window_losefocus in gconf
        """
        self.client.set_bool(KEY('/general/window_losefocus'), chk.get_active())

    def on_window_tabbar_toggled(self, chk):
        """Changes the activity of window_tabbar in gconf
        """
        self.client.set_bool(KEY('/general/window_tabbar'), chk.get_active())

    def on_start_fullscreen_toggled(self, chk):
        """Changes the activity of start_fullscreen in gconf
        """
        self.client.set_bool(KEY('/general/start_fullscreen'), chk.get_active())

    def on_window_height_value_changed(self, hscale):
        """Changes the value of window_height in gconf
        """
        val = hscale.get_value()
        self.client.set_int(KEY('/general/window_height'), int(val))

    def on_prompt_on_quit_toggled(self, chk):
        """Set the `prompt on quit' property in gconf
        """
        self.client.set_bool(KEY('/general/prompt_on_quit'), chk.get_active())

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


class PrefsDialog(SimpleGladeApp):
    """The Guake Preferences dialog.
    """
    def __init__(self):
        """Setup the preferences dialog interface, loading images,
        adding filters to file choosers and connecting some signals.
        """
        super(PrefsDialog, self).__init__(gladefile('prefs.glade'),
                                          root='config-window')
        self.add_callbacks(PrefsCallbacks())

        self.client = gconf.client_get_default()

        # setting evtbox title bg
        eventbox = self.get_widget('eventbox-title')
        eventbox.modify_bg(gtk.STATE_NORMAL,
                           eventbox.get_colormap().alloc_color("#ffffff"))

        # images
        ipath = pixmapfile('guake-notification.png')
        self.get_widget('image_logo').set_from_file(ipath)

        # the first position in tree will store the keybinding path in gconf,
        # and the user doesn't worry with this, lest hide that =D
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

        self.populate_shell_combo()
        self.populate_keys_tree()
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

    def toggle_style_sensitivity(self, chk):
        """If the user chooses to use the gnome default font
        configuration it means that he will not be able to use the
        font selector.
        """
        self.get_widget('font_style').set_sensitive(not chk.get_active())

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
        palette_index = combo.get_active()
        if palette_index == 4:
            return
        self.client.set_string(KEY('/style/font/palette'), 
            PALETTES[palette_index]) 
        self.set_palette_colors(PALETTES[palette_index])

    def on_palette_color_set(self, btn):
        """Changes the value of palette in gconf
        """
        palette = []
        for i in range(16):
            palette.append(hexify_color(
                self.get_widget('palette_%d' % i).get_color()))
        palette = ':'.join(palette)
        self.client.set_string(KEY('/style/font/palette'), palette)
        self.set_palette_name(palette)

    def set_palette_name(self, palette):
        """If the given palette matches an existing one, shows it in the
        combobox
        """
        self.get_widget('palette_name').set_active(4)
        for i in range(len(PALETTES)):
            if palette == PALETTES[i]:
                self.get_widget('palette_name').set_active(i)
    
    def set_palette_colors(self, palette):
        """Updates the color buttons with the given palette
        """
        palette = palette.split(':')
        for i in range(16):
            color = gtk.gdk.color_parse(palette[i])
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

    def load_configs(self):
        """Load configurations for all widgets in General, Scrolling
        and Appearance tabs from gconf.
        """
        # default_shell
        combo = self.get_widget('default_shell')
        # get the value for defualt shell. If unset, set to USER_SHELL_VALUE.
        value = self.client.get_string(KEY('/general/default_shell')) or \
                USER_SHELL_VALUE
        for i in combo.get_model():
            if i[0] == value:
                combo.set_active_iter(i.iter)

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

        # ontop
        value = self.client.get_bool(KEY('/general/window_ontop'))
        self.get_widget('window_ontop').set_active(value)

        # losefocus
        value = self.client.get_bool(KEY('/general/window_losefocus'))
        self.get_widget('window_losefocus').set_active(value)

        # tabbar
        value = self.client.get_bool(KEY('/general/window_tabbar'))
        self.get_widget('window_tabbar').set_active(value)

        # start fullscreen
        value = self.client.get_bool(KEY('/general/start_fullscreen'))
        self.get_widget('start_fullscreen').set_active(value)

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

        # font
        value = self.client.get_string(KEY('/style/font/style'))
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

        # palette
        value = self.client.get_string(KEY('/style/font/palette'))
        self.set_palette_name(value)
        self.set_palette_colors(value)
    
        # background image
        value = self.client.get_string(KEY('/style/background/image'))
        if os.path.isfile(value or ''):
            self.get_widget('background_image').set_filename(value)

        value = self.client.get_int(KEY('/style/background/transparency'))
        self.get_widget('background_transparency').set_value(value)

        # it's a separated method, to be reused.
        self.reload_erase_combos()

    # -- populate functions --

    def populate_shell_combo(self):
        """Read the /etc/shells and looks for installed pythons to
        fill the default_shell combobox.
        """
        cb = self.get_widget('default_shell')
        # append user shell as first option
        cb.append_text(USER_SHELL_VALUE)
        if os.path.exists(SHELLS_FILE):
            lines = open(SHELLS_FILE).readlines()
            for i in lines:
                possible = i.strip()
                if possible and not possible.startswith('#') and \
                   os.path.exists(possible):
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

        accel = self.client.get_string(gconf_path)
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
        return self.keycode == rval.keycode and \
            self.mask == rval.mask

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

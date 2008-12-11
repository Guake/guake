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
import re
import os

import gtk
import gobject
import gconf

from simplegladeapp import SimpleGladeApp
from guake_globals import GCONF_PATH
from common import *
import globalhotkeys

# A regular expression to match possible python interpreters when
# filling interpreters combo in preferences
PYTHONS = re.compile('^python\d\.\d$')

# Path to the shells file, it will be used to start to populate
# interpreters combo, see the next variable, its important to fill the
# rest of the combo too.
SHELLS_FILE = '/etc/shells'

# translating our types to vte types
ERASE_BINDINGS = {'ASCII DEL': 'ascii-delete',
                  'Escape sequence': 'delete-sequence',
                  'Control-H': 'ascii-backspace'}

# These tuples are going to be used to build a treeview with the
# hotkeys used in guake preferences.
GCONF_KEYS = GCONF_PATH + 'keybindings/'
GHOTKEYS = ((GCONF_KEYS+'global/show_hide', _('Toggle terminal visibility')),)
LHOTKEYS = ((GCONF_KEYS+'local/new_tab', _('New tab'),),
            (GCONF_KEYS+'local/close_tab', _('Close tab')),
            (GCONF_KEYS+'local/previous_tab', _('Go to previous tab')),
            (GCONF_KEYS+'local/next_tab', _('Go to next tab'),),
            (GCONF_KEYS+'local/clipboard_copy', _('Copy text to clipboard'),),
            (GCONF_KEYS+'local/clipboard_paste', _('Paste text from clipboard'),),
            (GCONF_KEYS+'local/toggle_fullscreen', _('Toggle Fullscreen'),),
)

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

class PrefsDialog(SimpleGladeApp):
    def __init__(self, guakeinstance):
        super(PrefsDialog, self).__init__(gladefile('prefs.glade'),
                                          root='config-window')

        self.guake = guakeinstance
        self.client = gconf.client_get_default()

        # setting evtbox title bg
        eventbox = self.get_widget('eventbox-title')
        eventbox.modify_bg(gtk.STATE_NORMAL,
                           eventbox.get_colormap().alloc_color("#ffffff"))

        # images
        ipath = pixmapfile('guake-notification.png')
        self.get_widget('image_logo').set_from_file(ipath)
        ipath = pixmapfile('tabdown.svg')
        self.get_widget('image1').set_from_file(ipath)
        ipath = pixmapfile('tabup.svg')
        self.get_widget('image2').set_from_file(ipath)

        # the first position in tree will store the keybinding path in gconf,
        # and the user doesn't worry with this, lest hide that =D
        model = gtk.TreeStore(str, str, object, bool)
        treeview = self.get_widget('treeview-keys')
        treeview.set_model(model)
        treeview.set_rules_hint(True)
        treeview.connect('button-press-event', self.start_editing_cb)

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
        self.bgfilechooser = self.get_widget('bgimage-filechooserbutton')
        self.bgfilechooser.set_preview_widget(self.selection_preview)
        self.bgfilechooser.set_filter(self.file_filter)
        self.bgfilechooser.connect('update-preview', self.update_preview_cb,
                                   self.selection_preview)

    def show(self):
        self.get_widget('config-window').show_all()
        self.get_widget('config-window').present()

    def hide(self):
        self.get_widget('config-window').hide()

    def reload_erase_combos(self):
        # backspace erase binding
        combo = self.get_widget('backspace-binding-combobox')
        binding = self.client.get_string(GCONF_PATH+'general/compat_backspace')
        model = combo.get_model()
        bindex = ERASE_BINDINGS.values().index(binding)
        for i in model:
            value = model.get_value(i.iter, 0)
            if ERASE_BINDINGS.keys().index(value) == bindex:
                combo.set_active_iter(i.iter)

        # delete erase binding
        combo = self.get_widget('delete-binding-combobox')
        binding = self.client.get_string(GCONF_PATH+'general/compat_delete')
        model = combo.get_model()
        bindex = ERASE_BINDINGS.values().index(binding)
        for i in model:
            value = model.get_value(i.iter, 0)
            if ERASE_BINDINGS.keys().index(value) == bindex:
                combo.set_active_iter(i.iter)

    def load_configs(self):
        # shells list
        default = self.client.get_string(GCONF_PATH + 'general/default_shell')
        combo = self.get_widget('shells-combobox')
        model = combo.get_model()
        for i in model:
            value = model.get_value(i.iter, 0)
            if value == default:
                combo.set_active_iter(i.iter)

        # history size
        val = self.client.get_int(GCONF_PATH+'general/history_size')
        self.get_widget('historysize-spinbutton').set_value(val)

        # scrollbar
        ac = self.client.get_bool(GCONF_PATH + 'general/use_scrollbar')
        self.get_widget('show-scrollbar-checkbutton').set_active(ac)

        # hide on lost focus
        ac = self.client.get_bool(GCONF_PATH + 'general/hide_on_lost_focus')
        self.get_widget('hide-onlostfocus-checkbutton').set_active(ac)

        # animate flag
        #ac = self.client.get_bool(GCONF_PATH + 'general/window_animate')
        #self.get_widget('animate-checkbutton').set_active(ac)

        # on top flag
        ac = self.client.get_bool(GCONF_PATH + 'general/window_ontop')
        self.get_widget('ontop-checkbutton').set_active(ac)

        # winsize
        val = float(self.client.get_int(GCONF_PATH + 'general/window_size'))
        self.get_widget('winsize-hscale').set_value(val)

        # tab pos
        val = self.client.get_string(GCONF_PATH + 'general/tabpos')
        if val == 'bottom':
            self.get_widget('tabbottom-radiobutton').set_active(True)
        else:
            self.get_widget('tabtop-radiobutton').set_active(True)

        # font
        val = self.client.get_string(GCONF_PATH + 'style/font/style')
        self.get_widget('fontbutton').set_font_name(val)

        val = self.client.get_string(GCONF_PATH + 'style/font/color')
        try:
            color = gtk.gdk.color_parse(val)
            self.get_widget('font-colorbutton').set_color(color)
        except (ValueError, TypeError):
            warnings.warn('Unable to parse color %s' % val, Warning)

        # background
        val = self.client.get_string(GCONF_PATH+'style/background/color')
        try:
            color = gtk.gdk.color_parse(val)
            self.get_widget('bg-colorbutton').set_color(color)
        except (ValueError, TypeError):
            warnings.warn('Unable to parse color %s' % val, Warning)
            
        use_bgimage = self.client.get_bool(GCONF_PATH+'general/use_bgimage')
        self.get_widget('chk_bg_transparent').set_active(not use_bgimage)
        self.get_widget('chk_bg_transparent').connect('toggled', self.on_chk_bg_transparent_toggled)
        
        val = self.client.get_string(GCONF_PATH+'style/background/image')
        self.get_widget('bgimage-filechooserbutton').set_filename(val)

        val = self.client.get_int(GCONF_PATH+'style/background/transparency')
        self.get_widget('transparency-hscale').set_value(val)

        # it's a separated method, to be reused.
        self.reload_erase_combos()

        # the terminal window can be opened and the user *must* see this window
        self.get_widget('config-window').set_keep_above(True)

    # -- populate functions --

    def populate_shell_combo(self):
        cb = self.get_widget('shells-combobox')
        if os.path.exists(SHELLS_FILE):
            lines = open(SHELLS_FILE).readlines()
            for i in lines:
                possible = i.strip()
                if possible and not possible.startswith('#') and \
                   os.path.exists(possible):
                    cb.append_text(possible)

        for i in os.environ.get('PATH', '').split(os.pathsep):
            if os.path.isdir(i):
                for j in os.listdir(i):
                    if PYTHONS.match(j):
                        cb.append_text(os.path.join(i, j))

    def populate_keys_tree(self):
        model = self.get_widget('treeview-keys').get_model()

        giter = model.append(None)
        model.set(giter, 0, '', 1, _('Global hotkeys'))

        for i in GHOTKEYS:
            child = model.append(giter)
            accel = self.client.get_string(i[0])
            if accel:
                params = gtk.accelerator_parse(accel)
                hotkey = KeyEntry(*params)
            else:
                hotkey = KeyEntry(0, 0)

            model.set(child,
                      0, i[0],
                      1, i[1],
                      2, hotkey,
                      3, True)

        giter = model.append(None)
        model.set(giter, 0, '', 1, _('Local hotkeys'))

        for i in LHOTKEYS:
            child = model.append(giter)
            accel = self.client.get_string(i[0])
            if accel:
                params = gtk.accelerator_parse(accel)
                hotkey = KeyEntry(*params)
            else:
                hotkey = KeyEntry(0, 0)

            model.set(child,
                      0, i[0],
                      1, i[1],
                      2, hotkey,
                      3, True)

        self.get_widget('treeview-keys').expand_all()
        
    # -- callbacks --

    def on_historysize_spinbutton_value_changed(self, spin):
        val = int(spin.get_value())
        self.client.set_int(GCONF_PATH + 'general/history_size', val)
        
    def on_show_scrollbar_checkbutton_toggled(self, chk):
        fbool = chk.get_active()
        self.client.set_bool(GCONF_PATH + 'general/use_scrollbar', fbool)
        self.guake.toggle_scrollbars()
        
    def on_chk_lostfocus_toggled(self, chk):
        fbool = chk.get_active()
        self.client.set_bool(GCONF_PATH + 'general/hide_on_lost_focus', fbool)
        
    def on_shells_combobox_changed(self, combo):
        citer = combo.get_active_iter()
        if not citer:
            return
        shell = combo.get_model().get_value(citer, 0)
        self.client.set_string(GCONF_PATH + 'general/default_shell', shell)

    def on_animate_checkbutton_toggled(self, bnt):
        self.client.set_bool(GCONF_PATH + 'general/window_animate',
                bnt.get_active())

    def on_ontop_checkbutton_toggled(self, bnt):
        self.client.set_bool(GCONF_PATH + 'general/window_ontop',
                             bnt.get_active())
        self.guake.toggle_ontop()

    def on_winsize_hscale_value_changed(self, hscale):
        val = hscale.get_value()
        self.client.set_int(GCONF_PATH + 'general/window_size', int(val))
        self.guake.resize(*self.guake.get_final_window_size())

    def on_tabbottom_radiobutton_toggled(self, bnt):
        st = bnt.get_active() and 'bottom' or 'top'
        self.client.set_string(GCONF_PATH + 'general/tabpos', st)
        self.guake.set_tabpos()
        
    def on_tabtop_radiobutton_toggled(self, bnt):
        st = bnt.get_active() and 'top' or 'bottom'
        self.client.set_string(GCONF_PATH + 'general/tabpos', st)
        self.guake.set_tabpos()

    def on_fontbutton_font_set(self, fb):
        self.client.set_string(GCONF_PATH + 'style/font/style',
                fb.get_font_name())
        self.guake.set_font()

    def on_font_colorbutton_color_set(self, bnt):
        c = hexify_color(bnt.get_color())
        self.client.set_string(GCONF_PATH + 'style/font/color', c)
        self.guake.set_fgcolor()

    def on_bg_colorbutton_color_set(self, bnt):
        c = hexify_color(bnt.get_color())
        self.client.set_string(GCONF_PATH + 'style/background/color', c)
        self.guake.set_bgcolor()

    def on_bgimage_filechooserbutton_selection_changed(self, bnt):
        f = bnt.get_filename()
        if f:
            self.client.set_string(GCONF_PATH + 'style/background/image', f)
            self.guake.set_bgimage()

    def on_chk_bg_transparent_toggled(self, togglebutton):
        value = togglebutton.get_active()
        self.client.set_bool(GCONF_PATH + 'general/use_bgimage', not value)
        self.guake.set_bgimage()
            
    def on_transparency_hscale_value_changed(self, hscale):
        val = hscale.get_value()
        self.client.set_int(GCONF_PATH + 'style/background/transparency',
                int(val))
        self.guake.set_alpha()

    def on_backspace_binding_combobox_changed(self, combo):
        val = combo.get_active_text()
        self.client.set_string(GCONF_PATH+'general/compat_backspace',
                               ERASE_BINDINGS[val])
        self.guake.set_erasebindings()

    def on_delete_binding_combobox_changed(self, combo):
        val = combo.get_active_text()
        self.client.set_string(GCONF_PATH+'general/compat_delete',
                               ERASE_BINDINGS[val])
        self.guake.set_erasebindings()

    def on_reset_compat_defaults_button_clicked(self, bnt):
        # default values were defined in guake.schemas file
        self.client.unset(GCONF_PATH+'general/compat_backspace')
        self.client.unset(GCONF_PATH+'general/compat_delete')
        self.reload_erase_combos()
        self.guake.set_erasebindings()

    def on_key_edited(self, renderer, path, keycode, mask, keyval, model):
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
            parent = self.get_widget('config-window')
            dialog = gtk.MessageDialog(parent,
                                       gtk.DIALOG_MODAL |
                                       gtk.DIALOG_DESTROY_WITH_PARENT,
                                       gtk.MESSAGE_WARNING,
                                       gtk.BUTTONS_OK,
                                       _("The shortcut \"%s\" cannot be used "
                                         "because it will become impossible to "
                                         "type using this key.\n\n"
                                         "Please try with a key such as "
                                         "Control, Alt or Shift at the same "
                                         "time.\n") % key)
            dialog.run()
            dialog.destroy()
            return False

        giter = model.get_iter(path)
        model.set_value(giter, 2, hotkey)

        # old key, used only to disconnect current shortcuts
        accel = self.client.get_string(gconf_path)
        if gconf_path in [x[0] for x in GHOTKEYS]:
            # ungrabing global keys
            globalhotkeys.unbind(accel)
            if not globalhotkeys.bind(key, self.guake.show_hide):
                globalhotkeys.bind(accel, self.guake.show_hide)
                model.set(giter, 2, accel)
                raise ShowableError(_('key binding error'),
                        _('Unable to bind %s key') % key, -1)
        else:
            # ungrabing local keys
            if accel != 'disabled':
                keynum, mask = gtk.accelerator_parse(accel)
                self.guake.accel_group.disconnect_key(keynum, mask)

        # setting the new value on gconf
        self.client.set_string(gconf_path, key)
        self.guake.load_accelerators()

    def on_key_cleared(self, renderer, path, model):
        giter = model.get_iter(path)
        gconf_path = model.get_value(giter, 0)
        accel = self.client.get_string(gconf_path)
        model.set_value(giter, 2, KeyEntry(0, 0))

        # cleared accel must be unbinded
        accel = self.client.get_string(gconf_path)
        if gconf_path in [x[0] for x in GHOTKEYS]:
            globalhotkeys.unbind(accel)

        keynum, mask = gtk.accelerator_parse(accel)
        if keynum:
            self.guake.accel_group.disconnect_key(keynum, mask)

        self.client.set_string(gconf_path, 'disabled')
        self.guake.load_accelerators()

    def cell_data_func(self, column, renderer, model, giter):
        obj = model.get_value(giter, 2)
        if obj:
            renderer.set_property('visible', True)
            renderer.set_property('accel-key', obj.keycode)
            renderer.set_property('accel-mods', obj.mask)
        else:
            renderer.set_property('visible', False)
            renderer.set_property('accel-key', 0)
            renderer.set_property('accel-mods', 0)

    def update_preview_cb(self,file_chooser, preview):
        """
        Used by filechooser to preview image files
        """
        filename = file_chooser.get_preview_filename()
        if filename:
            try:
                mkpb = gtk.gdk.pixbuf_new_from_file_at_size
                pixbuf = mkpb(filename, 256, 256)
                preview.set_from_pixbuf(pixbuf)
                file_chooser.set_preview_widget_active(True)
            except gobject.GError:
                # this exception is raised when user chooses a non-image
                # file or a directory
                pass
        else:
            file_chooser.set_preview_widget_active(False)

    def start_editing_cb(self, treeview, event):
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

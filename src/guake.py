# -*- coding: utf-8; -*-
"""
Copyright (C) 2007 Gabriel Falcão <gabrielteratos@gmail.com>
Copyright (C) 2007 Lincoln de Sousa <lincoln@archlinux-br.org>

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
Free Software Foundation, Inc., 59 Temple Place - Suite 330,
Boston, MA 02111-1307, USA.
"""
import pygtk
import gobject
pygtk.require('2.0')
gobject.threads_init()

import gtk
import vte
from pango import FontDescription
import gconf
import dbus

import os
import sys
import common
from common import _
from simplegladeapp import SimpleGladeApp, bindtextdomain
from statusicon import GuakeStatusIcon
import dbusiface
import globalhotkeys
import guake_globals

# Loading translation
bindtextdomain(guake_globals.name, guake_globals.locale_dir)

SHELLS_FILE = '/etc/shells'
GCONF_PATH = '/apps/guake/'
GCONF_KEYS = GCONF_PATH + 'keybindings/'

GHOTKEYS = ((GCONF_KEYS+'global/show_hide', _('Toggle terminal visibility')),)

LHOTKEYS = ((GCONF_KEYS+'local/new_tab', _('New tab'),),
            (GCONF_KEYS+'local/close_tab', _('Close tab')),
            (GCONF_KEYS+'local/previous_tab', _('Go to previous tab')),
            (GCONF_KEYS+'local/next_tab', _('Go to next tab'),))


class AboutDialog(SimpleGladeApp):
    def __init__(self):
        super(AboutDialog, self).__init__(common.gladefile('about.glade'),
                root='aboutdialog')
        # the terminal window can be opened and the user *must* see this window
        self.get_widget('aboutdialog').set_keep_above(True)

        # images
        ipath = common.pixmapfile('guake.png')
        img = gtk.gdk.pixbuf_new_from_file(ipath)
        self.get_widget('aboutdialog').set_property('logo', img)


class PrefsDialog(SimpleGladeApp):
    def __init__(self, guakeinstance):
        super(PrefsDialog, self).__init__(common.gladefile('prefs.glade'),
                root='config-window')

        self.guake = guakeinstance
        self.client = gconf.client_get_default()

        # images
        ipath = common.pixmapfile('guake.png')
        self.get_widget('image_logo').set_from_file(ipath)
        ipath = common.pixmapfile('tabdown.svg')
        self.get_widget('image1').set_from_file(ipath)
        ipath = common.pixmapfile('tabup.svg')
        self.get_widget('image2').set_from_file(ipath)

        # the first position in tree will store the keybinding path in gconf,
        # and the user doesn't worry with this, lest hide that =D
        model = gtk.TreeStore(str, str, str, bool)
        treeview = self.get_widget('treeview-keys')
        treeview.set_model(model)
        treeview.set_rules_hint(True)

        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('keypath', renderer, text=0)
        column.set_visible(False)
        treeview.append_column(column)

        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_('Action'), renderer, text=1)
        column.set_property('expand', True)
        treeview.append_column(column)

        renderer = gtk.CellRendererText()
        renderer.set_data('column', 1)
        renderer.connect('edited', self.on_key_edited, model)
        column = gtk.TreeViewColumn(_('Shortcut'), renderer, text=2,
                editable=3)
        column.set_property('expand', False)
        treeview.append_column(column)

        self.populate_shell_combo()
        self.populate_keys_tree()
        self.load_configs()
        self.get_widget('config-window').hide()

        # Preview when selecting a bgimage
        self.selection_preview = gtk.Image()
        self.file_filter = gtk.FileFilter()
        self.file_filter.add_pattern("*.jp[e]?g")
        self.file_filter.add_pattern("*.png")
        self.file_filter.add_pattern("*.svg")
        self.bgfilechooser = self.get_widget('bgimage-filechooserbutton')
        self.bgfilechooser.set_preview_widget(self.selection_preview)
        self.bgfilechooser.set_filter(self.file_filter)
        self.bgfilechooser.connect('update-preview', self.update_preview_cb,
                self.selection_preview)

    def show(self):
        self.get_widget('config-window').show_all()

    def hide(self):
        self.get_widget('config-window').hide()
        
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
        self.get_widget('spinHistorySize').set_value(val)

        # scrollbar
        ac = self.client.get_bool(GCONF_PATH + 'general/use_scrollbar')
        self.get_widget('show-scrollbar-checkbutton').set_active(ac)

        # hide on lost focus
        ac = self.client.get_bool(GCONF_PATH + 'general/hide_on_lost_focus')
        self.get_widget('hide-onlostfocus-checkbutton').set_active(ac)

        # animate flag
        ac = self.client.get_bool(GCONF_PATH + 'general/window_animate')
        self.get_widget('animate-checkbutton').set_active(ac)

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
            # unable to parse color
            pass

        # background
        val = self.client.get_string(GCONF_PATH+'style/background/color')
        try:
            color = gtk.gdk.color_parse(val)
            self.get_widget('bg-colorbutton').set_color(color)
        except (ValueError, TypeError):
            # unable to parse color
            pass
            
        self.guake.use_bgimage = self.client.get_bool(GCONF_PATH+'general/use_bgimage')
        self.get_widget('chk_bg_transparent').set_active(not self.guake.use_bgimage)
        self.get_widget('chk_bg_transparent').connect('toggled', self.on_chk_bg_transparent_toggled)
        
        val = self.client.get_string(GCONF_PATH+'style/background/image')
        self.get_widget('bgimage-filechooserbutton').set_filename(val)

        val = self.client.get_int(GCONF_PATH+'style/background/transparency')
        self.get_widget('transparency-hscale').set_value(val)

        # the terminal window can be opened and the user *must* see this window
        self.get_widget('config-window').set_keep_above(True)

    # -- populate functions --

    def populate_shell_combo(self):
        cb = self.get_widget('shells-combobox')
        if os.path.exists(SHELLS_FILE):
            lines = open(SHELLS_FILE).readlines()
            for i in lines:
                possible = i.strip()
                if possible and not possible.startswith('#'):
                    cb.append_text(possible)
        cb.append_text(sys.executable)

    def populate_keys_tree(self):
        model = self.get_widget('treeview-keys').get_model()

        giter = model.append(None)
        model.set(giter, 0, '', 1, _('Global hotkeys'))

        for i in GHOTKEYS:
            child = model.append(giter)
            hotkey = self.client.get_string(i[0])
            model.set(child,
                    0, i[0],
                    1, i[1],
                    2, hotkey,
                    3, True)

        giter = model.append(None)
        model.set(giter, 0, '', 1, _('Local hotkeys'))

        for i in LHOTKEYS:
            child = model.append(giter)
            hotkey = self.client.get_string(i[0])
            model.set(child,
                    0, i[0],
                    1, i[1],
                    2, hotkey,
                    3, True)

        self.get_widget('treeview-keys').expand_all()
        
    # -- callbacks --
    def on_spinHistorySize_value_changed(self, spinBtn):
        val = int(spinBtn.get_value())
        self.client.set_int(GCONF_PATH + 'general/history_size', val)
        
    def on_show_scrollbar_checkbutton_toggled(self, chk):
        bool = chk.get_active()
        self.client.set_bool(GCONF_PATH + 'general/use_scrollbar', bool)
        
    def on_chk_lostfocus_toggled(self, chk):
        bool = chk.get_active()
        self.client.set_bool(GCONF_PATH + 'general/hide_on_lost_focus', bool)
        
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
        c = common.hexify_color(bnt.get_color())
        self.client.set_string(GCONF_PATH + 'style/font/color', c)
        self.guake.set_fgcolor()

    def on_bg_colorbutton_color_set(self, bnt):
        c = common.hexify_color(bnt.get_color())
        self.client.set_string(GCONF_PATH + 'style/background/color', c)
        self.guake.set_bgcolor()

    def on_bgimage_filechooserbutton_selection_changed(self, bnt):
        file = bnt.get_filename()
        if file:
            self.client.set_string(GCONF_PATH + 'style/background/image',
                    file)
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

    def on_key_edited(self, renderer, path, key, model):
        giter = model.get_iter(path)
        gconf_path = model.get_value(giter, 0)
        model.set(giter, 2, key)

        # ungrabing key
        accel = self.client.get_string(gconf_path)
        keynum, mask = gtk.accelerator_parse(accel)
        self.guake.accel_group.disconnect_key(keynum, mask)

        # setting the new value on gconf
        self.client.set_string(gconf_path, key)
        self.guake.load_accelerators()

    def update_preview_cb(self,file_chooser, preview):
        """
        Used by filechooser to preview image files
        """
        filename = file_chooser.get_preview_filename()
        if filename:
            try:
                pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(filename, 256, 256)
                preview.set_from_pixbuf(pixbuf)
                file_chooser.set_preview_widget_active(True)
            except gobject.GError:
                pass #this exception is raised when user chooses a non-image file or a directory
        else:
            file_chooser.set_preview_widget_active(False)


class Guake(SimpleGladeApp):
    def __init__(self):
        super(Guake, self).__init__(common.gladefile('guake.glade'))
        self.client = gconf.client_get_default()

        # default option in case of gconf fails:
        self.use_bgimage = False

        # setting global hotkey!
        globalhotkeys.init()
        key = self.client.get_string(GHOTKEYS[0][0])
        bind_result = globalhotkeys.bind(key, self.show_hide)
        if not bind_result:
            print "Error when binding %s"%key
            import sys
            sys.exit(1)
        # trayicon!
        tray_icon = GuakeStatusIcon()
        tray_icon.connect('popup-menu', self.show_menu)
        tray_icon.connect('activate', self.show_hide)
        tray_icon.show_all()

        # adding images from a different path.
        ipath = common.pixmapfile('new_guakelogo.png')
        self.get_widget('image1').set_from_file(ipath)
        ipath = common.pixmapfile('add_tab.png')
        self.get_widget('image2').set_from_file(ipath)

        self.window = self.get_widget('window-root')
        self.notebook = self.get_widget('notebook-teminals')
        self.toolbar = self.get_widget('toolbar')
        self.mainframe = self.get_widget('mainframe')

        self.accel_group = gtk.AccelGroup()
        self.last_pos = -1
        self.term_list = []
        self.animation_speed = 30
        self.visible = False

        self.window.add_accel_group(self.accel_group)
        self.window.set_keep_above(True)
        self.window.set_geometry_hints(min_width=1, min_height=1)
        self.window.connect('focus-out-event',self.on_window_lostfocus)

        self.load_config()
        self.load_accelerators()
        self.refresh()
        self.add_tab()

    def on_window_lostfocus(self,window, event):
        getb = lambda x:self.client.get_bool(x)
        value = getb(GCONF_PATH+'general/hide_on_lost_focus')
        if value == True:
            self.hide()
        
    def refresh(self):
        # FIXME: vte.Terminal need to be showed with his parent window to
        # can load his configs of back/fore color, fonts, etc.
        self.window.show_all()
        self.window.hide()

    def show_menu(self, *args):
        menu = self.get_widget('tray-menu')
        menu.popup(None, None, None, 3, gtk.get_current_event_time())

    # -- methods exclusivelly called by dbus interface --

    def show_about(self):
        AboutDialog()

    def show_prefs(self):
        PrefsDialog(self).show()

    # -- controls main window visibility and size --

    def show_hide(self, *args):
        screen = self.window.get_screen()
        w, h = screen.get_width(), screen.get_height()
        if not self.visible:
            self.show(w, h)
            self.set_terminal_focus()
        else:
            self.hide()

    def show(self, wwidth, hheight):
        self.window.set_position(gtk.WIN_POS_NONE)
        self.window.set_gravity(gtk.gdk.GRAVITY_NORTH)
        self.visible = True
        self.window.move(0, 0)
        self.window.show()
        self.window.stick()
        self.animate_show()
        if not self.term_list:
            self.add_tab()

    def hide(self):
        self.animate_hide()
        self.window.hide() # FIXME: Don't use hide_all here!
        self.window.unstick()
        self.visible = False

    def animate_show(self, *args):
        width, final_height = self.get_final_window_size()
        if self.client.get_bool(GCONF_PATH+'general/window_animate'):
            self.resize(width, 1)
            for i in range(1, final_height, self.animation_speed):
                self.resize(width, i)
                common.update_ui()
        else:
            self.resize(width, final_height)
            common.update_ui()

    def animate_hide(self,*args):
        if self.client.get_bool(GCONF_PATH+'general/window_animate'):
            width, final_height = self.get_final_window_size()
            l = range(1, final_height, self.animation_speed)
            for i in reversed(l):
                self.resize(width, i)
                common.update_ui()

    def get_window_size(self):
        width = self.window.get_screen().get_width()
        height = self.client.get_int(GCONF_PATH+'general/window_size')
        return width, height

    def get_final_window_size(self):
        width, height = self.get_window_size()
        total_height = self.window.get_screen().get_height()
        final_height = total_height * height / 100
        return width, final_height

    def resize(self, width, height):
        self.window.resize(width, height)
        self.window.set_default_size(width, height)

    # -- configuration --

    def load_config(self):
        self.set_fgcolor()
        self.set_font()
        self.set_bgcolor()
        self.set_bgimage()
        self.set_alpha()
        self.set_tabpos()

    def load_accelerators(self):
        gets = lambda x:self.client.get_string(x)
        ac = gets(GCONF_PATH+'keybindings/local/new_tab')
        key, mask = gtk.accelerator_parse(ac)
        self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                self.accel_add)

        ac = gets(GCONF_PATH+'keybindings/local/previous_tab')
        key, mask = gtk.accelerator_parse(ac)
        self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                self.accel_prev)

        ac = gets(GCONF_PATH+'keybindings/local/next_tab')
        key, mask = gtk.accelerator_parse(ac)
        self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                self.accel_next)

    def accel_add(self, *args):
        self.add_tab()
        return True

    def accel_prev(self, *args):
        self.notebook.prev_page()
        return True

    def accel_next(self, *args):
        self.notebook.next_page()
        return True

    # -- format functions --

    def set_bgcolor(self):
        color = self.client.get_string(GCONF_PATH+'style/background/color')
        bgcolor = gtk.gdk.color_parse(color)
        for i in self.term_list:
            i.set_color_background(bgcolor)
            i.set_background_tint_color(bgcolor)

    def set_bgimage(self):
        image = self.client.get_string(GCONF_PATH+'style/background/image')
        self.use_bgimage = self.client.get_bool(GCONF_PATH+'general/use_bgimage')
        if image and os.path.exists(image):
            for i in self.term_list:
                i.set_background_image_file(image)
                i.set_background_transparent(not self.use_bgimage)
                
    def set_fgcolor(self):
        color = self.client.get_string(GCONF_PATH+'style/font/color')
        fgcolor = gtk.gdk.color_parse(color)
        for i in self.term_list:
            i.set_color_dim(fgcolor)
            i.set_color_cursor(fgcolor)
            i.set_color_highlight(fgcolor)
            i.set_color_foreground(fgcolor)

    def set_font(self):
        font_name = self.client.get_string(GCONF_PATH+'style/font/style')
        font = FontDescription(font_name)
        for i in self.term_list:
            i.set_font(font)

    def set_alpha(self):
        alpha = self.client.get_int(GCONF_PATH+'style/background/transparency')
        self.use_bgimage = self.client.get_bool(GCONF_PATH+'general/use_bgimage')
        for i in self.term_list:
            i.set_background_transparent(not self.use_bgimage)
            i.set_background_saturation(alpha / 100.0)

    def set_tabpos(self):
        pos = self.client.get_string(GCONF_PATH+'general/tabpos')
        if pos == 'bottom':
            self.mainframe.reorder_child(self.notebook, 0)
            self.notebook.set_tab_pos(gtk.POS_BOTTOM)
        else:
            self.mainframe.reorder_child(self.notebook, 1)
            self.notebook.set_tab_pos(gtk.POS_TOP)
           
    # -- callbacks --

    def on_prefs_menuitem_activate(self, *args):
        PrefsDialog(self).show()

    def on_about_menuitem_activate(self, *args):
        AboutDialog()

    def on_add_button_clicked(self, *args):
        self.add_tab()

    def on_terminal_exited(self, term, widget):
        self.delete_tab(self.notebook.page_num(widget))

    def on_close_button_close_clicked(self, widget, index):
        self.delete_tab(self.notebook.page_num(self.term_list[index]))
        self.set_terminal_focus()

    # -- tab related functions --

    def add_tab(self):
        last_added = len(self.term_list)
        self.term_list.append(vte.Terminal())
        self.term_list[last_added].set_sensitive(False)
        # TODO: make new terminal opens in the same dir of the already in use.
        shell_name = self.client.get_string(GCONF_PATH+'general/default_shell')
        self.term_list[last_added].fork_command(shell_name or "bash",
                directory=os.path.expanduser('~'))
        
        image = gtk.Image()
        image.set_from_file(common.pixmapfile('close.svg'))
        
        label = gtk.Label(_('Terminal %s') % (last_added+1))
        label.connect('button-press-event', self.set_terminal_focus)

        button = gtk.Button()
        button.set_image(image)
        button.set_relief(gtk.RELIEF_NONE)
        button.connect('clicked', self.on_close_button_close_clicked,
                last_added)

        hbox = gtk.HBox(False, False)
        hbox.set_border_width(1)
        hbox.pack_start(label)
        hbox.pack_start(button)
        hbox.show_all()

        mhbox = gtk.HBox()
        mhbox.pack_start(self.term_list[last_added], True, True)

        # showing scrollbar based in gconf setting:
        scrollbar_visible = self.client.get_bool(GCONF_PATH+'general/use_scrollbar')
        if scrollbar_visible:
            adj = self.term_list[last_added].get_adjustment()
            scroll = gtk.VScrollbar(adj)
            mhbox.pack_start(scroll, False, False)

        mhbox.show_all()
            
        self.term_list[last_added].set_background_transparent(not self.use_bgimage)
        # TODO: maybe the better way is give these choices to the user...
        self.term_list[last_added].set_audible_bell(False) # without boring beep
        self.term_list[last_added].set_visible_bell(False) # without visible beep
        self.term_list[last_added].set_scroll_on_output(True) # auto scroll
        self.term_list[last_added].set_scroll_on_keystroke(True) # auto scroll
        #self.term_list[last_added].set_scroll_background(True)
        history_size = self.client.get_int(GCONF_PATH+'general/history_size')
        self.term_list[last_added].set_scrollback_lines(history_size) # history size
        self.term_list[last_added].set_sensitive(True)
        
        self.term_list[last_added].set_flags(gtk.CAN_DEFAULT)
        self.term_list[last_added].set_flags(gtk.CAN_FOCUS)
        self.term_list[last_added].connect('child-exited',
                self.on_terminal_exited, mhbox)
        self.term_list[last_added].grab_focus()

        self.notebook.append_page(mhbox, hbox)
        self.notebook.connect('switch-page', self.set_last_pos)
        self.notebook.connect('focus-tab', self.set_terminal_focus)

        self.set_tabs_visible()
        self.load_config()
        self.term_list[last_added].show()
        self.notebook.set_current_page(last_added)
        self.last_pos = last_added

    def delete_tab(self, pagepos):
        self.term_list.pop(pagepos)
        self.notebook.remove_page(pagepos)
        self.set_tabs_visible()
        if not self.term_list:
            self.hide()

    def set_terminal_focus(self):
        self.notebook.set_current_page(self.last_pos)
        self.term_list[self.last_pos].grab_focus()

    def set_tabs_visible(self):
        if self.notebook.get_n_pages() == 1:
            self.notebook.set_show_tabs(False)
        else:
            self.notebook.set_show_tabs(True)

    def set_last_pos(self, notebook, page, page_num):
        self.last_pos = page_num


def main():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-s', '--show-hide', dest='show_hide',
            action='store_true', default=False,
            help=_('Toggles the visibility of the terminal window'))

    parser.add_option('-p', '--preferences', dest='show_preferences',
            action='store_true', default=False,
            help=_('Shows Guake preference window'))

    parser.add_option('-a', '--about', dest='show_about',
            action='store_true', default=False,
            help=_('Shows Guake\'s about info'))

    parser.add_option('-q', '--quit', dest='quit',
            action='store_true', default=False,
            help=_('Says to Guake go away =('))

    options, args = parser.parse_args()

    bus = dbus.SessionBus()
    try:
        remote_object = bus.get_object('org.gnome.Guake.DBus', '/DBusInterface')
    except dbus.DBusException:
        return

    if options.show_hide:
        remote_object.show_hide()
        sys.exit(0)

    if options.show_preferences:
        remote_object.show_prefs()
        sys.exit(0)

    if options.show_about:
        remote_object.show_about()
        sys.exit(0)

    if options.quit:
        remote_object.quit()
        sys.exit(0)

    # here we know that guake was called without any parameter and it is
    # already running, so, lets toggle glade visibility and exit!
    remote_object.show_hide()
    sys.exit(0)


if __name__ == '__main__':
    from dbusiface import dbus_init
    from common import test_gconf, ShowableError
    main()

    if not test_gconf():
        raise ShowableError(_('Guake can not init!'),
            _('Gconf Error.\n'
              'Have you installed <b>guake.schemas</b> properlly?'))

    g = Guake()
    dbus_init(g)
    g.run()

# -*- coding: utf-8; -*-
"""
Copyright (C) 2007 Gabriel Falcão <gabrielteratos@gmail.com>
Copyright (C) 2007,2008 Lincoln de Sousa <lincoln@minaslivre.org>

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
import pynotify
import gconf
import dbus

import os
import signal
import sys
from thread import start_new_thread
from time import sleep

import globalhotkeys
from simplegladeapp import SimpleGladeApp, bindtextdomain
from prefs import PrefsDialog, GHOTKEYS
from common import *
from guake_globals import *

pynotify.init('Guake!')

GNOME_FONT_PATH = '/desktop/gnome/interface/monospace_font_name'

# Loading translation
bindtextdomain(name, locale_dir)

class GConfHandler(object):
    """Handles gconf changes, if any gconf variable is changed, a
    different method is called to handle this change.
    """
    def __init__(self, guake):
        """Constructor of GConfHandler, just add the guake dir to the
        gconf client and bind the keys to its handler methods.
        """
        self.guake = guake

        client = gconf.client_get_default()
        client.add_dir(GCONF_PATH, gconf.CLIENT_PRELOAD_RECURSIVE)

        notify_add = client.notify_add

        #notify_add(KEY('/general/default_shell'), self.shell_changed)
        #notify_add(KEY('/general/use_login_shell'), self.login_shell_toggled)
        #notify_add(KEY('/general/use_popup'), self.popup_toggled)
        #notify_add(KEY('/general/window_losefocus'), self.losefocus_toggled)

        notify_add(KEY('/general/show_resizer'), self.show_resizer_toggled)

        notify_add(KEY('/general/use_trayicon'), self.trayicon_toggled)
        notify_add(KEY('/general/window_ontop'), self.ontop_toggled)
        notify_add(KEY('/general/window_tabbar'), self.tabbar_toggled)
        notify_add(KEY('/general/window_size'), self.size_changed)

        notify_add(KEY('/general/use_scrollbar'), self.scrollbar_toggled)
        notify_add(KEY('/general/history_size'), self.history_size_changed)
        notify_add(KEY('/general/scroll_output'), self.keystroke_output)
        notify_add(KEY('/general/scroll_keystroke'), self.keystroke_toggled)

        notify_add(KEY('/general/use_default_font'), self.default_font_toggled)
        notify_add(KEY('/style/font/style'), self.fstyle_changed)
        notify_add(KEY('/style/font/color'), self.fcolor_changed)
        notify_add(KEY('/style/background/color'), self.bgcolor_changed)
        notify_add(KEY('/style/background/image'), self.bgimage_changed)
        notify_add(KEY('/style/background/opacity'), self.bgopacity_changed)

    def show_resizer_toggled(self, client, connection_id, entry, data):
        """If the gconf var show_resizer be changed, this method will
        be called and will show/hide the resizer.
        """
        if entry.value.get_bool():
            self.guake.resizer.show()
        else:
            self.guake.resizer.hide()

    def trayicon_toggled(self, client, connection_id, entry, data):
        """If the gconf var use_trayicon be changed, this method will
        be called and will show/hide the trayicon.
        """
        self.guake.tray_icon.set_visible(entry.value.get_bool())

    def ontop_toggled(self, client, connection_id, entry, data):
        """If the gconf var window_ontop be changed, this method will
        be called and will set the keep_above attribute in guake's
        main window.
        """
        self.guake.window.set_keep_above(entry.value.get_bool())

    def tabbar_toggled(self, client, connection_id, entry, data):
        """If the gconf var use_tabbar be changed, this method will be
        called and will show/hide the tabbar.
        """
        if entry.value.get_bool():
            self.guake.toolbar.show()
        else:
            self.guake.toolbar.hide()

    def size_changed(self, client, connection_id, entry, data):
        """If the gconf var window_size be changed, this method will
        be called and will call the resize function in guake.
        """
        width, height = self.guake.get_final_window_size()
        self.guake.resize(width, height)

    def scrollbar_toggled(self, client, connection_id, entry, data):
        """If the gconf var use_scrollbar be changed, this method will
        be called and will show/hide scrollbars of all terminals open.
        """
        for i in self.guake.term_list:
            # There is an hbox in each tab of the main notebook and it
            # contains a Terminal and a Scrollbar. Since only have the
            # Terminal here, we're going to use this to get the
            # scrollbar and hide/show it.
            hbox = i.get_parent()
            terminal, scrollbar = hbox.get_children()
            if entry.value.get_bool():
                scrollbar.show()
            else:
                scrollbar.hide()

    def history_size_changed(self, client, connection_id, entry, data):
        """If the gconf var history_size be changed, this method will
        be called and will set the scrollback_lines property of all
        terminals open.
        """
        for i in self.guake.term_list:
            i.set_scrollback_lines(entry.value.get_int())

    def keystroke_output(self, client, connection_id, entry, data):
        """If the gconf var scroll_output be changed, this method will
        be called and will set the scroll_on_output in all terminals
        open.
        """
        for i in self.guake.term_list:
            i.set_scroll_on_output(entry.value.get_bool())

    def keystroke_toggled(self, client, connection_id, entry, data):
        """If the gconf var scroll_keystroke be changed, this method
        will be called and will set the scroll_on_keystroke in all
        terminals open.
        """
        for i in self.guake.term_list:
            i.set_scroll_on_keystroke(entry.value.get_bool())

    def default_font_toggled(self, client, connection_id, entry, data):
        """If the gconf var use_default_font be changed, this method
        will be called and will change the font style to the gnome
        default or to the choosen font in style/font/style in all
        terminals open.
        """
        if entry.value.get_bool():
            key = GNOME_FONT_PATH
        else:
            key = KEY('/style/font/style')

        font = FontDescription(client.get_string(key))
        for i in self.guake.term_list:
            i.set_font(font)

    def fstyle_changed(self, client, connection_id, entry, data):
        """If the gconf var style/font/style be changed, this method
        will be called and will change the font style in all terminals
        open.
        """
        font = FontDescription(entry.value.get_string())
        for i in self.guake.term_list:
            i.set_font(font)

    def fcolor_changed(self, client, connection_id, entry, data):
        """If the gconf var style/font/color be changed, this method
        will be called and will change the font color in all terminals
        open.
        """
        fgcolor = gtk.gdk.color_parse(entry.value.get_string())
        for i in self.guake.term_list:
            i.set_color_dim(fgcolor)
            i.set_color_foreground(fgcolor)

    def bgcolor_changed(self, client, connection_id, entry, data):
        """If the gconf var style/background/color be changed, this
        method will be called and will change the background color in
        all terminals open.
        """
        bgcolor = gtk.gdk.color_parse(entry.value.get_string())
        for i in self.guake.term_list:
            i.set_color_background(bgcolor)
            i.set_background_tint_color(bgcolor)

    def bgimage_changed(self, client, connection_id, entry, data):
        """If the gconf var style/background/image be changed, this
        method will be called and will change the background image and
        will set the transparent flag to false if an image is set in
        all terminals open.
        """
        image = entry.value.get_string()
        for i in self.guake.term_list:
            if image and os.path.exists(image):
                i.set_background_image_file(image)
                i.set_background_transparent(False)
            else:
                i.set_background_transparent(True)

    def bgopacity_changed(self, client, connection_id, entry, data):
        """If the gconf var style/background/opacity be changed, this
        method will be called and will set the saturation and opacity
        properties in all terminals open.
        """
        opacity = entry.value.get_int()
        for i in self.guake.term_list:
            i.set_background_saturation(opacity / 100.0)
            i.set_opacity(opacity)


class AboutDialog(SimpleGladeApp):
    """The About Guake dialog class
    """
    def __init__(self):
        super(AboutDialog, self).__init__(gladefile('about.glade'),
                                          root='aboutdialog')
        dialog = self.get_widget('aboutdialog')

        # the terminal window can be opened and the user *must* see
        # this window
        dialog.set_keep_above(True)

        # images
        ipath = pixmapfile('guake-notification.png')
        img = gtk.gdk.pixbuf_new_from_file(ipath)
        dialog.set_property('logo', img)

        dialog.set_name('Guake!')
        dialog.set_version(version)


class Guake(SimpleGladeApp):
    """Guake main class. Handles specialy the main window.
    """
    def __init__(self):
        super(Guake, self).__init__(gladefile('guake.glade'))
        self.client = gconf.client_get_default()

        # setting global hotkey and showing a pretty notification =)
        globalhotkeys.init()
        key = self.client.get_string(GHOTKEYS[0][0])
        keyval, mask = gtk.accelerator_parse(key)
        label = gtk.accelerator_get_label(keyval, mask)

        # trayicon!
        img = pixmapfile('guake-tray.png')
        self.tray_icon = gtk.status_icon_new_from_file(img)
        self.tray_icon.set_tooltip(_('Guake-Terminal'))
        self.tray_icon.connect('popup-menu', self.show_menu)
        self.tray_icon.connect('activate', self.show_hide)

        # adding images from a different path.
        ipath = pixmapfile('guake.png')
        self.get_widget('image1').set_from_file(ipath)
        ipath = pixmapfile('add_tab.png')
        self.get_widget('image2').set_from_file(ipath)

        # important widgets
        self.window = self.get_widget('window-root')
        self.notebook = self.get_widget('notebook-teminals')
        self.tabs = self.get_widget('hbox-tabs')
        self.toolbar = self.get_widget('toolbar')
        self.mainframe = self.get_widget('mainframe')
        self.resizer = self.get_widget('resizer')

        # List of vte.Terminal widgets, it will be useful when needed
        # to get a widget by the current page in self.notebook
        self.term_list = []

        # This is the pid of shells forked by each terminal. Will be
        # used to kill the process when closing a tab
        self.pid_list = []

        # It's intended to know which tab was selected to
        # close/rename. This attribute will be set in
        # self.show_tab_menu
        self.selected_tab = None

        # holds the number of created tabs. This counter will not be
        # reset to avoid problems of repeated tab names.
        self.tab_counter = 0

        # holds visibility/fullscreen status =)
        self.visible = False
        self.fullscreen = False

        self.accel_group = gtk.AccelGroup()
        self.window.add_accel_group(self.accel_group)
        self.window.set_geometry_hints(min_width=1, min_height=1)
        self.window.connect('focus-out-event', self.on_window_losefocus)
        self.get_widget('context-menu').set_accel_group(self.accel_group)

        # resizer stuff
        self.resizer.connect('motion-notify-event', self.on_resizer_drag)

        # adding the first tab on guake
        self.add_tab()

        # loading configuration stuff
        GConfHandler(self)
        self.load_config()
        self.load_accel_map()
        self.load_accelerators()

        if not globalhotkeys.bind(key, self.show_hide):
            filename = pixmapfile('guake-notification.png')
            notification = pynotify.Notification(
                _('Guake!'),
                _('A problem happened when binding <b>%s</b> key.\n'
                  'Please use guake properties form to choose another '
                  'key') % label, filename)
            notification.show()

        elif self.client.get_bool(KEY('/general/use_popup')):
            # Pop-up that shows that guake is working properly (if not
            # unset in the preferences windows)
            self.startup_notification(label)

    def startup_notification(self, label):
        """Shows a startup notification if guake starts correctly.
        """
        filename = pixmapfile('guake-notification.png')
        notification = pynotify.Notification(
            _('Guake!'),
            _('Guake is already running,\n'
              'press <b>%s</b> to use it.') % label, filename)
        notification.show()

    def on_resizer_drag(self, widget, event):
        (x, y), mod = event.device.get_state(widget.window)

        max_height = self.window.get_screen().get_height()
        percent = y / (max_height / 100)
        
        if percent < 1:
            percent = 1
            
        if 'GDK_BUTTON1_MASK' in mod.value_names:
            self.client.set_int(KEY('/general/window_size'), int(percent))

    def on_window_losefocus(self, window, event):
        value = self.client.get_bool(KEY('/general/window_losefocus'))
        if value and self.visible:
            self.hide()

    def show_menu(self, *args):
        menu = self.get_widget('tray-menu')
        menu.popup(None, None, None, 3, gtk.get_current_event_time())

    def show_context_menu(self, terminal, event):
        if event.button != 3:
            return False

        guake_clipboard = gtk.clipboard_get()
        if not guake_clipboard.wait_is_text_available():
            self.get_widget('context_paste').set_sensitive(False)
        else:
            self.get_widget('context_paste').set_sensitive(True)
        context_menu = self.get_widget('context-menu')
        context_menu.popup(None, None, None, 3, gtk.get_current_event_time())
        return True

    def show_tab_menu(self, target, event):
        if event.button == 3:
            self.selected_tab = target
            menu = self.get_widget('tab-menu')
            menu.popup(None, None, None, 3, event.get_time())
        self.set_terminal_focus()

    # -- methods exclusivelly called by dbus interface --

    def show_about(self):
        """Hides the main window and creates an instance of the About
        Dialog.
        """
        self.hide()
        AboutDialog()

    def show_prefs(self):
        """Hides the main window and creates an instance of the
        Preferences window.
        """
        #self.hide()
        PrefsDialog().show()

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
        # setting window in all desktops
        self.get_widget('window-root').stick()

        # add tab must be called before window.show to avoid a
        # blank screen before adding the tab.
        if not self.term_list:
            self.add_tab()

        self.visible = True
        self.resize(*self.get_final_window_size())
        self.window.show_all()
        self.window.move(0, 0)

        try:
            # does it work in other gtk backends
            time = gtk.gdk.x11_get_server_time(self.window.window)
        except AttributeError:
            time = 0

        self.window.window.show()
        self.window.window.focus(time)

    def hide(self):
        self.window.hide() # Don't use hide_all here!
        self.visible = False

    def get_final_window_size(self):
        screen = self.window.get_screen()
        height = self.client.get_int(KEY('/general/window_size'))

        # avoiding X Window system error
        max_height = screen.get_height()
        if height > max_height:
            height = max_height

	# get the width just from the first/default monitor in the
	# future we might create a field to select which monitor you
	# wanna use
        width = screen.get_monitor_geometry(0).width

        total_height = self.window.get_screen().get_height()
        final_height = total_height * height / 100
        return width, final_height

    def resize(self, width, height):
        self.window.resize(width, height)

    # -- configuration --

    def load_config(self):
        """"Just a proxy for all the configuration stuff.
        """
        self.client.notify(KEY('/general/use_trayicon'))
        self.client.notify(KEY('/general/window_tabbar'))
        self.client.notify(KEY('/general/window_ontop'))
        self.client.notify(KEY('/general/window_size'))
        self.client.notify(KEY('/general/use_scrollbar'))
        self.client.notify(KEY('/general/history_size'))
        self.client.notify(KEY('/general/show_resizer'))
        self.client.notify(KEY('/style/font/style'))
        self.client.notify(KEY('/style/font/color'))
        self.client.notify(KEY('/style/background/color'))
        self.client.notify(KEY('/style/background/image'))
        self.client.notify(KEY('/style/background/opacity'))
        self.client.notify(KEY('/general/use_default_font'))

        return
        self.set_erasebindings()

    def load_accel_map(self):
        """Sets the accel map of quit context option.
        """
        key, mask = gtk.accelerator_parse('<Control>q')
        gtk.accel_map_add_entry('<Guake>/Quit', key, mask)
        btn = self.get_widget('context_close')
        btn.set_accel_path('<Guake>/Quit')

    def load_accelerators(self):
        """Reads all gconf paths under /apps/guake/keybindings/local
        and adds to the main accel_group.
        """
        gets = lambda x:self.client.get_string(x)
        ac = gets(KEY('/keybindings/local/new_tab'))
        key, mask = gtk.accelerator_parse(ac)
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.accel_add)

        ac = gets(KEY('/keybindings/local/close_tab'))
        key, mask = gtk.accelerator_parse(ac)
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.on_context_close_tab_activate)

        ac = gets(KEY('/keybindings/local/previous_tab'))
        key, mask = gtk.accelerator_parse(ac)
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.accel_prev)

        ac = gets(KEY('/keybindings/local/next_tab'))
        key, mask = gtk.accelerator_parse(ac)
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.accel_next)

        ac = gets(KEY('/keybindings/local/rename_tab'))
        key, mask = gtk.accelerator_parse(ac)
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.accel_rename)

        ac = gets(KEY('/keybindings/local/clipboard_copy'))
        key, mask = gtk.accelerator_parse(ac)
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.accel_copy_clipboard)

        ac = gets(KEY('/keybindings/local/clipboard_paste'))
        key, mask = gtk.accelerator_parse(ac)
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.accel_paste_clipboard)

        ac = gets(KEY('/keybindings/local/toggle_fullscreen'))
        key, mask = gtk.accelerator_parse(ac)
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.accel_toggle_fullscreen)

    def accel_add(self, *args):
        """Callback to add a new tab. Called by the accel key.
        """
        self.add_tab()
        return True

    def accel_prev(self, *args):
        """Callback to go to the previous tab. Called by the accel key.
        """
        if self.notebook.get_current_page() == 0:
            self.notebook.set_current_page(self.notebook.get_n_pages()-1)
        else:
            self.notebook.prev_page()
        return True

    def accel_next(self, *args):
        """Callback to go to the next tab. Called by the accel key.
        """
        if self.notebook.get_current_page()+1 == self.notebook.get_n_pages():
            self.notebook.set_current_page(0)
        else:
            self.notebook.next_page()
        return True

    def accel_rename(self, *args):
        """Callback to show the rename tab dialog. Called by the accel
        key.
        """
        pagepos = self.notebook.get_current_page()
        self.selected_tab = self.tabs.get_children()[pagepos]
        self.on_rename_activate()
        return True

    def accel_copy_clipboard(self, *args):
        """Callback to copy text in the shown terminal. Called by the
        accel key.
        """
        pos = self.notebook.get_current_page()
        self.term_list[pos].copy_clipboard()
        return True

    def accel_paste_clipboard(self, *args):
        """Callback to paste text in the shown terminal. Called by the
        accel key.
        """
        pos = self.notebook.get_current_page()
        self.term_list[pos].paste_clipboard()
        return True

    def accel_toggle_fullscreen(self, *args):
        """Callback toggle the fullscreen status of the main
        window. It uses the toolbar_visible_in_fullscreen variable
        from gconf to decide if the tabbar will or not be
        shown. Called by the accel key.
        """
        val = self.client.get_bool(KEY('general/toolbar_visible_in_fullscreen'))

        if not self.fullscreen:
            self.window.fullscreen()
            self.fullscreen = True

            # The resizer widget really don't need to be shown in
            # fullscreen mode, but tabbar will only be shown if a
            # hidden gconf key is false.
            self.resizer.hide()
            if not val:
                self.toolbar.hide()
        else:
            self.window.unfullscreen()
            self.fullscreen = False

            # making sure that tabbar and resizer will come back to
            # their default state.
            self.client.notify(KEY('/general/window_tabbar'))
            self.client.notify(KEY('/general/show_resizer'))

        return True

    # -- format functions --

    def set_erasebindings(self):
        bkspace = self.client.get_string(GCONF_PATH+'general/compat_backspace')
        delete = self.client.get_string(GCONF_PATH+'general/compat_delete')
        for i in self.term_list:
            i.set_backspace_binding(bkspace)
            i.set_delete_binding(delete)

    # -- callbacks --

    def on_prefs_menuitem_activate(self, *args):
        self.show_prefs()

    def on_about_menuitem_activate(self, *args):
        self.show_about()

    def on_add_button_clicked(self, *args):
        self.add_tab()

    def on_terminal_exited(self, term, widget):
        self.delete_tab(self.notebook.page_num(widget), kill=False)

    def on_rename_activate(self, *args):
        entry = gtk.Entry()
        entry.set_text(self.selected_tab.get_label())
        entry.set_property('can-default', True)
        entry.show()

        vbox = gtk.VBox()
        vbox.set_border_width(6)
        vbox.show()

        dialog = gtk.Dialog("Rename tab",
                            self.window,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        dialog.set_size_request(300, -1)
        dialog.vbox.pack_start(vbox)
        dialog.set_border_width(4)
        dialog.set_has_separator(False)
        dialog.set_default_response(gtk.RESPONSE_ACCEPT)
        dialog.add_action_widget(entry, gtk.RESPONSE_ACCEPT)
        entry.reparent(vbox)

        response = dialog.run()
        dialog.destroy()

        if response == gtk.RESPONSE_ACCEPT:
            self.selected_tab.set_label(entry.get_text())

        self.set_terminal_focus()

    def on_close_activate(self, *args):
        pagepos = self.tabs.get_children().index(self.selected_tab)
        self.delete_tab(pagepos)

    # -- Context menu callbacks --

    def on_context_preferences_activate(self, widget):
        self.show_prefs()

    def on_context_copy_activate(self, widget):
        current_pos = self.notebook.get_current_page()
        self.term_list[current_pos].copy_clipboard()

    def on_context_paste_activate(self, widget):
        current_pos = self.notebook.get_current_page()
        self.term_list[current_pos].paste_clipboard()

    def on_context_close_tab_activate(self, *args):
        pagepos = self.notebook.get_current_page()
        self.delete_tab(pagepos)

    def on_context_close_activate(self, widget):
        gtk.main_quit()

    # -- tab related functions --

    def add_tab(self):
        last_added = len(self.term_list)
        self.term_list.append(vte.Terminal())

        active_pagepos = self.notebook.get_current_page()
        directory = os.path.expanduser('~')
        if active_pagepos >= 0:
            cwd = "/proc/%d/cwd" % self.pid_list[active_pagepos]
            if os.path.exists(cwd):
                directory = cwd

        shell = self.client.get_string(KEY('/general/default_shell')) or 'sh'
        pid = self.term_list[last_added].\
            fork_command(shell, directory=directory)

        self.pid_list.append(pid)

        # Adding a new radio button to the tabbar
        label = _('Terminal %s') % self.tab_counter
        tabs = self.tabs.get_children()
        parent = tabs and tabs[0] or None
        bnt = gtk.RadioButton(group=parent, label=label)
        bnt.set_property('can-focus', False)
        bnt.set_property('draw-indicator', False)
        bnt.connect('button-press-event', self.show_tab_menu)
        bnt.connect('clicked', lambda *x:
                        self.notebook.set_current_page (last_added))
        bnt.show()

        self.tabs.pack_start(bnt, expand=False, padding=1)
        self.tab_counter += 1

        # preparing the way to the scrollbar...
        mhbox = gtk.HBox()
        mhbox.pack_start(self.term_list[last_added], True, True)
        self.term_list[last_added].show()

        adj = self.term_list[last_added].get_adjustment()
        scroll = gtk.VScrollbar(adj)
        scroll.set_no_show_all(True)
        mhbox.pack_start(scroll, False, False)
        mhbox.show()

        # configuring the terminal widget
        word_chars = self.client.get_string(KEY('/general/word_chars'))
        self.term_list[last_added].set_word_chars(word_chars)
        self.term_list[last_added].set_audible_bell(False)
        self.term_list[last_added].set_visible_bell(False)
        self.term_list[last_added].set_sensitive(True)
        self.term_list[last_added].set_flags(gtk.CAN_DEFAULT)
        self.term_list[last_added].set_flags(gtk.CAN_FOCUS)
        self.term_list[last_added].connect('button-press-event',
                                           self.show_context_menu)
        self.term_list[last_added].connect('child-exited',
                                           self.on_terminal_exited,
                                           mhbox)

        self.term_list[last_added].grab_focus()
        self.notebook.append_page(mhbox, None)
        self.notebook.set_current_page(last_added)
        self.load_config()

    def delete_tab(self, pagepos, kill=True):
        """This function will destroy the notebook page, terminal and
        tab widgets and will call the function to kill interpreter
        forked by vte.
        """
        self.notebook.remove_page(pagepos)
        self.tabs.get_children()[pagepos].destroy()
        self.term_list.pop(pagepos).destroy()
        pid = self.pid_list.pop(pagepos)

        if kill:
            start_new_thread(self.delete_shell, (pid,))

        if not self.term_list:
            self.hide()
            # avoiding the delay on next Guake show request
            self.add_tab()

    def delete_shell(self, pid):
        """This function will kill the shell on a tab, trying to send
        a sigterm and if it doesn't work, a sigkill. Between these two
        signals, we have a timeout of 3 seconds, so is recommended to
        call this in another thread. This doesn't change any thing in
        UI, so you can use python's start_new_thread.
        """
        os.kill(pid, signal.SIGTERM)
        num_tries = 30

        while num_tries > 0:
            if os.waitpid(pid, os.WNOHANG)[0] != 0:
                break
            sleep(0.1)
            num_tries -= 1

        if num_tries == 0:
            try:
                os.kill(pid, signal.SIGKILL)
                os.waitpid(pid, 0)
            except OSError:
                # if this part of code was reached, means that SIGTERM
                # did the work and SIGKILL wasnt needed.
                pass

    def set_terminal_focus(self):
        page = self.notebook.get_current_page()
        self.term_list[page].grab_focus()

    def select_current_tab(self, notebook, user_data, page):
        self.tabs.get_children()[page].set_active(True)

def main():
    """Parses the command line parameters and decide if dbus methods
    should be called or not.
    """
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
    main()

    if not test_gconf():
        raise ShowableError(_('Guake can not init!'),
            _('Gconf Error.\n'
              'Have you installed <b>guake.schemas</b> properlly?'))

    guake = Guake()
    dbus_init(guake)
    guake.run()

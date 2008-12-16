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
import warnings
from thread import start_new_thread
from time import sleep

import dbusiface
import globalhotkeys
from simplegladeapp import SimpleGladeApp, bindtextdomain
from statusicon import GuakeStatusIcon
from prefs import PrefsDialog, GHOTKEYS
from common import *
from guake_globals import *

pynotify.init('Guake!')

# Loading translation
bindtextdomain(name, locale_dir)

class GuakeGConf(object):
    def __init__(self, guakeinstance):
        self.guake = guakeinstance
        self.guake.client.add_dir("/apps/guake", gconf.CLIENT_PRELOAD_NONE)

        self.guake.client.notify_add("/apps/guake/general/show_resizer",
                                     self.on_show_resizer_toggled)
        self.guake.client.notify_add("/apps/guake/general/show_toolbar",
                                     self.on_show_toolbar_toggled)

    def on_show_resizer_toggled(self, client, connection_id, entry, data):
        if entry.value.get_bool():
            self.guake.resizer.show()
        else:
            self.guake.resizer.hide()
            
    def on_show_toolbar_toggled(self, client, connection_id, entry, data):
        if entry.value.get_bool():
            self.guake.toolbar.show()
        else:
            self.guake.toolbar.hide()


class AboutDialog(SimpleGladeApp):
    def __init__(self):
        super(AboutDialog, self).__init__(gladefile('about.glade'),
                                          root='aboutdialog')
        ad = self.get_widget('aboutdialog')

        # the terminal window can be opened and the user *must* see
        # this window
        ad.set_keep_above(True)

        # images
        ipath = pixmapfile('guake-notification.png')
        img = gtk.gdk.pixbuf_new_from_file(ipath)
        ad.set_property('logo', img)

        ad.set_name('Guake!')
        ad.set_version(version)


class Guake(SimpleGladeApp):
    def __init__(self):
        super(Guake, self).__init__(gladefile('guake.glade'))
        self.client = gconf.client_get_default()
        self.gconf = GuakeGConf(self)
        # setting global hotkey and showing a pretty notification =)
        globalhotkeys.init()
        key = self.client.get_string(GHOTKEYS[0][0])
        keyval, mask = gtk.accelerator_parse(key)
        label = gtk.accelerator_get_label(keyval, mask)

        # trayicon!
        tray_icon = GuakeStatusIcon()
        tray_icon.connect('popup-menu', self.show_menu)
        tray_icon.connect('activate', self.show_hide)
        tray_icon.show_all()

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

        # some day we're going to have animation when showing/hiding
        # guake's main window.
        self.animation_speed = 30

        self.accel_group = gtk.AccelGroup()
        self.window.add_accel_group(self.accel_group)
        self.window.set_geometry_hints(min_width=1, min_height=1)
        self.window.connect('focus-out-event', self.on_window_lostfocus)
        self.get_widget('context-menu').set_accel_group(self.accel_group)

        # resizer stuff
        self.resizer.connect('motion-notify-event', self.on_resizer_drag)

        self.load_accel_map()
        self.load_config()
        self.load_accelerators()
        self.refresh()
        self.add_tab()
        self.toggle_ontop()

        # Pop-up that shows that guake is working properly (if not
        # unset in the preferences windows)
        filename = pixmapfile('guake-notification.png')
        if not globalhotkeys.bind(key, self.show_hide):
            n = pynotify.Notification(_('Guake!'),
                _('A problem happened when binding <b>%s</b> key.\n'
                  'Please use guake properties form to choose another '
                  'key') % label, filename)
        else:
            n = pynotify.Notification(_('Guake!'),
                _('Guake is already running,\n'
                  'press <b>%s</b> to use it.') % label, filename)
        n.show()

    def on_resizer_drag(self, widget, event):
        (x, y), mod = event.device.get_state(widget.window)

        max_height = self.window.get_screen().get_height()
        percent = y / (max_height / 100)
        
        if percent < 1:
            percent = 1
            
        if 'GDK_BUTTON1_MASK' in mod.value_names:
            self.client.set_int(GCONF_PATH + 'general/window_size', int(percent))
            self.resize(*self.get_final_window_size())

    def on_window_lostfocus(self,window, event):
        getb = lambda x:self.client.get_bool(x)
        value = getb(GCONF_PATH+'general/hide_on_lost_focus')
        if value and not self.visible:
            self.hide()

    def check_widgets_visibility(self):
        gbool = lambda x: self.client.get_bool(GCONF_PATH+'general/%s' % x)
        
        show_resizer = gbool('show_resizer')
        show_toolbar = gbool('show_toolbar')
        
        if not show_resizer:
            self.resizer.hide()
        else:
            self.resizer.show()

        if not show_toolbar:
            self.toolbar.hide()
        else:
            if not self.fullscreen:
                self.toolbar.show()
            else:
                self.toolbar.hide()
        
    def refresh(self):
        # FIXME: vte.Terminal need to be shown with his parent window to
        # can load his configs of back/fore color, fonts, etc.
        self.window.show_all()
        self.window.hide()
        self.check_widgets_visibility()

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
        self.hide()
        AboutDialog()

    def show_prefs(self):
        self.hide()
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
        self.window.hide() # FIXME: Don't use hide_all here!
        self.visible = False

    def get_window_size(self):
	screen = self.window.get_screen()
        height = self.client.get_int(GCONF_PATH+'general/window_size')
        # avoiding X Window system error
        max_height = screen.get_height()

        if height > max_height:
            height = max_height

	# get the width just from the first/default monitor
	# in the future we might create a field to select which monitor you wanna use
	width = screen.get_monitor_geometry(0).width
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
        self.set_erasebindings()

    def load_accel_map(self):
        # Sets the accel map of quit context option.
        key, mask = gtk.accelerator_parse('<Control>q')
        gtk.accel_map_add_entry('<main>/Quit', key, mask)
        self.get_widget('context_close').set_accel_path('<main>/Quit')

    def load_accelerators(self):
        gets = lambda x:self.client.get_string(x)
        ac = gets(GCONF_PATH+'keybindings/local/new_tab')
        key, mask = gtk.accelerator_parse(ac)
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.accel_add)

        ac = gets(GCONF_PATH+'keybindings/local/close_tab')
        key, mask = gtk.accelerator_parse(ac)
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.on_context_close_tab_activate)

        ac = gets(GCONF_PATH+'keybindings/local/previous_tab')
        key, mask = gtk.accelerator_parse(ac)
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.accel_prev)

        ac = gets(GCONF_PATH+'keybindings/local/next_tab')
        key, mask = gtk.accelerator_parse(ac)
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.accel_next)

        ac = gets(GCONF_PATH+'keybindings/local/clipboard_copy')
        key, mask = gtk.accelerator_parse(ac)
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.accel_copy_clipboard)

        ac = gets(GCONF_PATH+'keybindings/local/clipboard_paste')
        key, mask = gtk.accelerator_parse(ac)
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.accel_paste_clipboard)

        ac = gets(GCONF_PATH+'keybindings/local/toggle_fullscreen')
        key, mask = gtk.accelerator_parse(ac)
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.accel_toggle_fullscreen)

    def accel_add(self, *args):
        self.add_tab()
        return True

    def accel_prev(self, *args):
        if self.notebook.get_current_page() == 0:
            self.notebook.set_current_page(self.notebook.get_n_pages()-1)
        else:
            self.notebook.prev_page()
        return True

    def accel_next(self, *args):
        if self.notebook.get_current_page()+1 == self.notebook.get_n_pages():
            self.notebook.set_current_page(0)
        else:
            self.notebook.next_page()
        return True

    def accel_copy_clipboard(self, *args):
        pos = self.notebook.get_current_page()
        self.term_list[pos].copy_clipboard()
        return True

    def accel_paste_clipboard(self, *args):
        pos = self.notebook.get_current_page()
        self.term_list[pos].paste_clipboard()
        return True

    def accel_toggle_fullscreen(self, *args):
        gbool = lambda x: self.client.get_bool(GCONF_PATH+'general/%s' % x)
        tabs_visible = gbool("toolbar_visible_in_fullscreen")
        if not self.fullscreen:
            self.window.fullscreen()
            self.fullscreen = True
            self.resizer.hide()
            if not tabs_visible:
                self.toolbar.hide()
        else:
            self.window.unfullscreen()
            self.fullscreen = False
            self.check_widgets_visibility()
        return True

    def toggle_scrollbars(self):
        b = self.client.get_bool(GCONF_PATH+'general/use_scrollbar')
        for i in self.term_list:
            # this hbox contains a Terminal and a Scrollbar, and we only
            # have the Terminal, so we're going to use this to get the bar
            # and hide/show it.
            hbox = i.get_parent()
            terminal, scrollbar = hbox.get_children()
            if b:
                scrollbar.show()
            else:
                scrollbar.hide()

    def toggle_ontop(self):
        b = self.client.get_bool(GCONF_PATH+'general/window_ontop')
        self.window.set_keep_above(b)

    # -- format functions --

    def set_bgcolor(self):
        color = self.client.get_string(GCONF_PATH+'style/background/color')
        bgcolor = gtk.gdk.color_parse(color)
        for i in self.term_list:
            i.set_color_background(bgcolor)
            i.set_background_tint_color(bgcolor)

    def set_bgimage(self):
        image = self.client.get_string(GCONF_PATH+'style/background/image')
        use_bgimage = self.client.get_bool(GCONF_PATH+'general/use_bgimage')
        if image and os.path.exists(image):
            for i in self.term_list:
                i.set_background_image_file(image)
                i.set_background_transparent(not use_bgimage)
                
    def set_fgcolor(self):
        color = self.client.get_string(GCONF_PATH+'style/font/color')
        fgcolor = gtk.gdk.color_parse(color)
        for i in self.term_list:
            i.set_color_dim(fgcolor)
            i.set_color_foreground(fgcolor)

    def set_font(self):
        font_name = self.client.get_string(GCONF_PATH+'style/font/style')
        font = FontDescription(font_name)
        for i in self.term_list:
            i.set_font(font)

    def set_alpha(self):
        alpha = self.client.get_int(GCONF_PATH+'style/background/transparency')
        use_bgimage = self.client.get_bool(GCONF_PATH+'general/use_bgimage')
        for i in self.term_list:
            i.set_background_transparent(not use_bgimage)
            i.set_background_saturation(alpha / 100.0)

    def set_erasebindings(self):
        backspace = self.client.get_string(GCONF_PATH+'general/compat_backspace')
        delete = self.client.get_string(GCONF_PATH+'general/compat_delete')
        for i in self.term_list:
            i.set_backspace_binding(backspace)
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

        # setting the word chars in the terminal
        word_chars = self.client.get_string(GCONF_PATH+'general/word_chars')
        self.term_list[last_added].set_word_chars(word_chars)

        shell_name = self.client.get_string(GCONF_PATH+'general/default_shell')

        if len(self.term_list):
            active_pagepos = self.notebook.get_current_page()
        else:
            active_pagepos = -1

        directory = os.path.expanduser('~')
        if active_pagepos >= 0:
            cwd = "/proc/%d/cwd" % self.pid_list[active_pagepos]
            if os.path.exists(cwd):
                directory = cwd
            
        pid = self.term_list[last_added].\
            fork_command(shell_name or "bash", directory=directory)

        self.pid_list.append(pid)
        self.term_list[last_added].connect('button-press-event',
                self.show_context_menu)

        # Adding a new radio button to the tabbar
        tabs = self.tabs.get_children()
        parent = tabs and tabs[0] or None

        self.tab_counter += 1

        label = _('Terminal %s') % self.tab_counter
        bnt = gtk.RadioButton(group=parent, label=label)

        bnt.set_property('can-focus', False)
        bnt.set_property('draw-indicator', False)

        bnt.connect('button-press-event', self.show_tab_menu)
        bnt.connect('clicked', lambda *x:
                        self.notebook.set_current_page (last_added))
        bnt.show()

        self.tabs.pack_start(bnt, expand=False, padding=1)

        # preparing the way to the scrollbar...
        mhbox = gtk.HBox()
        mhbox.pack_start(self.term_list[last_added], True, True)

        adj = self.term_list[last_added].get_adjustment()
        scroll = gtk.VScrollbar(adj)
        use_scrollbar = self.client.get_bool(GCONF_PATH+'general/use_scrollbar')
        if not use_scrollbar:
            scroll.set_no_show_all(True)
        mhbox.pack_start(scroll, False, False)
        mhbox.show_all()

        use_bgimage = self.client.get_bool(GCONF_PATH+'general/use_bgimage')
        self.term_list[last_added].set_background_transparent(not use_bgimage)

        # TODO: maybe the better way is give these choices to the user...
        self.term_list[last_added].set_audible_bell(False) # without boring beep
        self.term_list[last_added].set_visible_bell(False) # without visible beep
        self.term_list[last_added].set_scroll_on_output(True) # auto scroll
        self.term_list[last_added].set_scroll_on_keystroke(True) # auto scroll

        history_size = self.client.get_int(GCONF_PATH+'general/history_size')
        self.term_list[last_added].set_scrollback_lines(history_size) # history size
        self.term_list[last_added].set_sensitive(True)
        
        self.term_list[last_added].set_flags(gtk.CAN_DEFAULT)
        self.term_list[last_added].set_flags(gtk.CAN_FOCUS)
        self.term_list[last_added].connect('child-exited',
                self.on_terminal_exited, mhbox)
        self.term_list[last_added].grab_focus()

        self.notebook.append_page(mhbox, None)

        self.load_config()
        self.term_list[last_added].show()
        self.notebook.set_current_page(last_added)

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
        """This function will kill the shell on a tab, trying to sent
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

    g = Guake()
    dbus_init(g)
    g.run()

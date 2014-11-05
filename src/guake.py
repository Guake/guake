#!/usr/bin/env python2
# -*- coding: utf-8; -*-
"""
Copyright (C) 2007-2012 Lincoln de Sousa <lincoln@minaslivre.org>
Copyright (C) 2007 Gabriel Falcão <gabrielteratos@gmail.com>

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

from __future__ import absolute_import
from __future__ import division

import dbus
import gconf
import gobject
import gtk
import logging
import os
import posix
import pygtk
import re
import signal
import subprocess
import sys
import vte
import xdg.Exceptions

from pango import FontDescription
from thread import start_new_thread
from time import sleep
from urllib import quote_plus
from urllib import url2pathname
from urlparse import urlsplit
from xdg.DesktopEntry import DesktopEntry
from xml.sax.saxutils import escape as xml_escape

import guake.globalhotkeys
import guake.notifier

from guake.common import ShowableError
from guake.common import _
from guake.common import clamp
from guake.common import gladefile
from guake.common import pixmapfile
from guake.common import shell_quote
from guake.common import test_gconf
from guake.dbusiface import DBUS_NAME
from guake.dbusiface import DBUS_PATH
from guake.dbusiface import DbusManager
from guake.globals import ALIGN_BOTTOM
from guake.globals import ALIGN_CENTER
from guake.globals import ALIGN_LEFT
from guake.globals import ALIGN_RIGHT
from guake.globals import ALWAYS_ON_PRIMARY
from guake.globals import GCONF_PATH
from guake.globals import KEY
from guake.globals import LOCALE_DIR
from guake.globals import NAME
from guake.globals import QUICK_OPEN_MATCHERS
from guake.globals import TERMINAL_MATCH_EXPRS
from guake.globals import TERMINAL_MATCH_TAGS
from guake.globals import VERSION
from guake.prefs import GKEY
from guake.prefs import LKEY
from guake.prefs import PrefsDialog
from guake.simplegladeapp import SimpleGladeApp
from guake.simplegladeapp import bindtextdomain
libutempter = None
try:
    from atexit import register as at_exit_call
    from ctypes import cdll
    libutempter = cdll.LoadLibrary('libutempter.so.0')
    if libutempter is not None:
        # We absolutly need to remove the old tty from the utmp !!!!!!!!!!
        at_exit_call(libutempter.utempter_remove_added_record)
except Exception as e:
    libutempter = None
    sys.stderr.write('[WARN] Unable to load the library libutempter !\n')
    sys.stderr.write('[WARN] The <wall> command will not work in guake !\n')
    sys.stderr.write('[WARN] ' + str(e) + '\n')

GCONF_MONOSPACE_FONT_PATH = '/desktop/gnome/interface/monospace_font_name'
DCONF_MONOSPACE_FONT_PATH = 'org.gnome.desktop.interface'
DCONF_MONOSPACE_FONT_KEY = 'monospace-font-name'

instance = None

pygtk.require('2.0')
gobject.threads_init()

# Loading translation
bindtextdomain(NAME, LOCALE_DIR)


# Setting gobject program name
gobject.set_prgname(NAME)


class PromptQuitDialog(gtk.MessageDialog):

    """Prompts the user whether to quit or not if there are procs running.
    """

    def __init__(self, parent, running_procs):
        super(PromptQuitDialog, self).__init__(
            parent,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO)

        self.set_keep_above(True)
        self.set_markup(_('Do you really want to quit Guake!?'))
        if running_procs == 1:
            self.format_secondary_markup(
                _("<b>There is one process still running.</b>")
            )
        elif running_procs > 1:
            self.format_secondary_markup(
                _("<b>There are %d processes running.</b>" % running_procs)
            )


class AboutDialog(SimpleGladeApp):

    """The About Guake dialog class
    """

    def __init__(self):
        super(AboutDialog, self).__init__(gladefile('about.glade'),
                                          root='aboutdialog')
        dialog = self.get_widget('aboutdialog')

        # images
        ipath = pixmapfile('guake-notification.png')
        img = gtk.gdk.pixbuf_new_from_file(ipath)
        dialog.set_property('logo', img)

        dialog.set_name('Guake!')
        dialog.set_version(VERSION)


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

        # these keys does not need to be watched.
        # notify_add(KEY('/general/default_shell'), self.shell_changed)
        # notify_add(KEY('/general/use_login_shell'), self.login_shell_toggled)
        # notify_add(KEY('/general/use_popup'), self.popup_toggled)
        # notify_add(KEY('/general/window_losefocus'), self.losefocus_toggled)
        # notify_add(KEY('/general/use_vte_titles'), self.use_vte_titles_changed)
        # notify_add(KEY('/general/quick_open_enable'), self.on_quick_open_enable_changed)
        # notify_add(KEY('/general/quick_open_in_current_terminal'), self.on_quick_open_in_current_terminal_changed)

        # Notification is not required for mouse_display/display_n because
        # set_final_window_rect polls gconf and is called whenever Guake is
        # shown or resized

        notify_add(KEY('/general/show_resizer'), self.show_resizer_toggled)

        notify_add(KEY('/general/use_trayicon'), self.trayicon_toggled)
        notify_add(KEY('/general/window_ontop'), self.ontop_toggled)
        notify_add(KEY('/general/window_tabbar'), self.tabbar_toggled)
        notify_add(KEY('/general/window_height'), self.size_changed)
        notify_add(KEY('/general/window_width'), self.size_changed)
        notify_add(KEY('/general/window_height_f'), self.size_changed)
        notify_add(KEY('/general/window_width_f'), self.size_changed)
        notify_add(KEY('/general/window_valignment'), self.alignment_changed)
        notify_add(KEY('/general/window_halignment'), self.alignment_changed)
        notify_add(KEY('/style/cursor_blink_mode'), self.cursor_blink_mode_changed)
        notify_add(KEY('/style/cursor_shape'), self.cursor_shape_changed)

        notify_add(KEY('/general/use_scrollbar'), self.scrollbar_toggled)
        notify_add(KEY('/general/history_size'), self.history_size_changed)
        notify_add(KEY('/general/scroll_output'), self.keystroke_output)
        notify_add(KEY('/general/scroll_keystroke'), self.keystroke_toggled)

        notify_add(KEY('/general/use_default_font'), self.default_font_toggled)
        notify_add(KEY('/style/font/style'), self.fstyle_changed)
        notify_add(KEY('/style/font/color'), self.fcolor_changed)
        notify_add(KEY('/style/font/palette'), self.fpalette_changed)
        notify_add(KEY('/style/background/color'), self.bgcolor_changed)
        notify_add(KEY('/style/background/image'), self.bgimage_changed)
        notify_add(KEY('/style/background/transparency'),
                   self.bgtransparency_changed)

        notify_add(KEY('/general/compat_backspace'), self.backspace_changed)
        notify_add(KEY('/general/compat_delete'), self.delete_changed)

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
        if hasattr(self.guake.tray_icon, 'set_status'):
            self.guake.tray_icon.set_status(entry.value.get_bool())
        else:
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

    def alignment_changed(self, client, connection_id, entry, data):
        """If the gconf var window_halignment be changed, this method will
        be called and will call the move function in guake.
        """
        self.guake.set_final_window_rect()

    def size_changed(self, client, connection_id, entry, data):
        """If the gconf var window_height or window_width are changed,
        this method will be called and will call the resize function
        in guake.
        """
        self.guake.set_final_window_rect()

    def cursor_blink_mode_changed(self, client, connection_id, entry, data):
        """Called when cursor blink mode settings has been changed
        """
        for term in self.guake.term_list:
            term.set_property("cursor-blink-mode", entry.value.get_int())

    def cursor_shape_changed(self, client, connection_id, entry, data):
        """Called when the cursor shape settings has been changed
        """
        for term in self.guake.term_list:
            term.set_property("cursor-shape", entry.value.get_int())

    def scrollbar_toggled(self, client, connection_id, entry, data):
        """If the gconf var use_scrollbar be changed, this method will
        be called and will show/hide scrollbars of all terminals open.
        """
        for term in self.guake.term_list:
            # There is an hbox in each tab of the main notebook and it
            # contains a Terminal and a Scrollbar. Since only have the
            # Terminal here, we're going to use this to get the
            # scrollbar and hide/show it.
            hbox = term.get_parent()
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
        default or to the chosen font in style/font/style in all
        terminals open.
        """
        font_name = None
        if entry.value.get_bool():
            # cannot directly use the Gio API since it requires to rework completely
            # the library inclusion, remove dependencies on gobject and so on.
            # Instead, issuing a direct command line request
            proc = subprocess.Popen(['gsettings', 'get', DCONF_MONOSPACE_FONT_PATH,
                                     DCONF_MONOSPACE_FONT_KEY], stdout=subprocess.PIPE)
            font_name = proc.stdout.readline().replace("'", "")
            if font_name is None:
                # Back to gconf
                font_name = client.get_string(GCONF_MONOSPACE_FONT_PATH)
        else:
            key = KEY('/style/font/style')
            font_name = client.get_string(key)

        if not font_name:
            print "Error: unable to find font name !!!"
            return
        font = FontDescription(font_name)
        if not font:
            return
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
            i.set_color_dim(i.custom_fgcolor or fgcolor)
            i.set_color_foreground(i.custom_fgcolor or fgcolor)
            i.set_color_bold(i.custom_fgcolor or fgcolor)

    def fpalette_changed(self, client, connection_id, entry, data):
        """If the gconf var style/font/palette be changed, this method
        will be called and will change the color scheme in all terminals
        open.
        """
        fgcolor = gtk.gdk.color_parse(
            client.get_string(KEY('/style/font/color')))
        bgcolor = gtk.gdk.color_parse(
            client.get_string(KEY('/style/background/color')))
        palette = [gtk.gdk.color_parse(color) for color in
                   entry.value.get_string().split(':')]
        for i in self.guake.term_list:
            i.set_colors(fgcolor, bgcolor, palette)

    def bgcolor_changed(self, client, connection_id, entry, data):
        """If the gconf var style/background/color be changed, this
        method will be called and will change the background color in
        all terminals open.
        """
        bgcolor = gtk.gdk.color_parse(entry.value.get_string())
        for i in self.guake.term_list:
            i.set_color_background(i.custom_bgcolor or bgcolor)
            i.set_background_tint_color(i.custom_bgcolor or bgcolor)

    def bgimage_changed(self, client, connection_id, entry, data):
        """If the gconf var style/background/image be changed, this
        method will be called and will change the background image and
        will set the transparent flag to false if an image is set in
        all terminals open.
        """
        self.guake.set_background_image(entry.value.get_string())

    def bgtransparency_changed(self, client, connection_id, entry, data):
        """If the gconf var style/background/transparency be changed, this
        method will be called and will set the saturation and transparency
        properties in all terminals open.
        """
        self.guake.set_background_transparency(entry.value.get_int())

    def backspace_changed(self, client, connection_id, entry, data):
        """If the gconf var compat_backspace be changed, this method
        will be called and will change the binding configuration in
        all terminals open.
        """
        for i in self.guake.term_list:
            i.set_backspace_binding(entry.value.get_string())

    def delete_changed(self, client, connection_id, entry, data):
        """If the gconf var compat_delete be changed, this method
        will be called and will change the binding configuration in
        all terminals open.
        """
        for i in self.guake.term_list:
            i.set_delete_binding(entry.value.get_string())


class GConfKeyHandler(object):

    """Handles changes in keyboard shortcuts.
    """

    def __init__(self, guake):
        """Constructor of Keyboard, only receives the guake instance
        to be used in internal methods.
        """
        self.guake = guake
        self.accel_group = None  # see reload_accelerators
        self.client = gconf.client_get_default()

        notify_add = self.client.notify_add
        notify_add(GKEY('show_hide'), self.reload_globals)

        keys = ['toggle_fullscreen', 'new_tab', 'close_tab', 'rename_current_tab',
                'previous_tab', 'next_tab', 'clipboard_copy', 'clipboard_paste',
                'quit', 'zoom_in', 'zoom_out', 'increase_height', 'decrease_height', "search_on_web",
                'switch_tab1', 'switch_tab2', 'switch_tab3', 'switch_tab4', 'switch_tab5',
                'switch_tab6', 'switch_tab7', 'switch_tab8', 'switch_tab9', 'switch_tab10'
                ]
        for key in keys:
            notify_add(LKEY(key), self.reload_accelerators)
            self.client.notify(LKEY(key))

    def reload_globals(self, client, connection_id, entry, data):
        """Unbind all global hotkeys and rebind the show_hide
        method. If more global hotkeys should be added, just connect
        the gconf key to the watch system and add.
        """
        self.guake.hotkeys.unbind_all()
        key = entry.get_value().get_string()
        if not self.guake.hotkeys.bind(key, self.guake.show_hide):
            raise ShowableError(_('key binding error'),
                                _('Unable to bind global <b>%s</b> key') % xml_escape(key),
                                -1)

    def reload_accelerators(self, *args):
        """Reassign an accel_group to guake main window and guake
        context menu and calls the load_accelerators method.
        """
        if self.accel_group:
            self.guake.window.remove_accel_group(self.accel_group)
        self.accel_group = gtk.AccelGroup()
        self.guake.window.add_accel_group(self.accel_group)
        self.guake.context_menu.set_accel_group(self.accel_group)
        self.load_accelerators()

    def load_accelerators(self):
        """Reads all gconf paths under /apps/guake/keybindings/local
        and adds to the main accel_group.
        """
        gets = lambda x: self.client.get_string(LKEY(x))
        key, mask = gtk.accelerator_parse(gets('quit'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_quit)

        key, mask = gtk.accelerator_parse(gets('new_tab'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_add)

        key, mask = gtk.accelerator_parse(gets('close_tab'))
        if key > 0:
            self.accel_group.connect_group(
                key, mask, gtk.ACCEL_VISIBLE,
                self.guake.close_tab)

        key, mask = gtk.accelerator_parse(gets('previous_tab'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_prev)

        key, mask = gtk.accelerator_parse(gets('next_tab'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_next)

        key, mask = gtk.accelerator_parse(gets('rename_current_tab'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_rename_current_tab)

        key, mask = gtk.accelerator_parse(gets('clipboard_copy'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_copy_clipboard)

        key, mask = gtk.accelerator_parse(gets('clipboard_paste'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_paste_clipboard)

        key, mask = gtk.accelerator_parse(gets('toggle_fullscreen'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_toggle_fullscreen)

        key, mask = gtk.accelerator_parse(gets('zoom_in'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_zoom_in)

        key, mask = gtk.accelerator_parse(gets('zoom_in_alt'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_zoom_in)

        key, mask = gtk.accelerator_parse(gets('zoom_out'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_zoom_out)

        key, mask = gtk.accelerator_parse(gets('increase_height'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_increase_height)

        key, mask = gtk.accelerator_parse(gets('decrease_height'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_decrease_height)

        for tab in xrange(1, 11):
            key, mask = gtk.accelerator_parse(gets('switch_tab%d' % tab))
            if key > 0:
                self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                               self.guake.gen_accel_switch_tabN(tab - 1))

        try:
            key, mask = gtk.accelerator_parse(gets('search_on_web'))
            if key > 0:
                self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                               self.guake.search_on_web)
        except Exception as e:
            print "Exception occured: %s" % (str(e,))


class GuakeTerminal(vte.Terminal):

    """Just a vte.Terminal with some properties already set.
    """

    def __init__(self):
        super(GuakeTerminal, self).__init__()
        self.configure_terminal()
        self.add_matches()
        self.connect('button-press-event', self.button_press)
        self.matched_value = ''
        self.font_scale_index = 0
        self.pid = None
        self.custom_bgcolor = None
        self.custom_fgcolor = None

    def configure_terminal(self):
        """Sets all customized properties on the terminal
        """
        client = gconf.client_get_default()
        word_chars = client.get_string(KEY('/general/word_chars'))
        self.set_word_chars(word_chars)
        self.set_audible_bell(False)
        self.set_visible_bell(False)
        self.set_sensitive(True)
        self.set_flags(gtk.CAN_DEFAULT)
        self.set_flags(gtk.CAN_FOCUS)
        cursor_blink_mode = client.get_int(KEY('/style/cursor_blink_mode'))
        client.set_int(KEY('/style/cursor_blink_mode'), cursor_blink_mode)
        cursor_shape = client.get_int(KEY('/style/cursor_shape'))
        client.set_int(KEY('/style/cursor_shape'), cursor_shape)

    def add_matches(self):
        """Adds all regular expressions declared in
        guake.globals.TERMINAL_MATCH_EXPRS to the terminal to make vte
        highlight text that matches them.
        """
        for expr in TERMINAL_MATCH_EXPRS:
            tag = self.match_add(expr)
            self.match_set_cursor_type(tag, gtk.gdk.HAND2)

        for _useless, match, _otheruseless in QUICK_OPEN_MATCHERS:
            tag = self.match_add(match)
            self.match_set_cursor_type(tag, gtk.gdk.HAND2)

    def get_current_directory(self):
        directory = os.path.expanduser('~')
        if self.pid is not None:
            cwd = os.readlink("/proc/%d/cwd" % self.pid)
            if os.path.exists(cwd):
                directory = cwd
        return directory

    def button_press(self, terminal, event):
        """Handles the button press event in the terminal widget. If
        any match string is caught, another application is open to
        handle the matched resource uri.
        """
        self.matched_value = ''
        matched_string = self.match_check(
            int(event.x / self.get_char_width()),
            int(event.y / self.get_char_height()))

        if (event.button == 1
                and event.get_state() & gtk.gdk.CONTROL_MASK
                and matched_string):
            print "matched string:", matched_string
            value, tag = matched_string
            # First searching in additional matchers
            found = False
            client = gconf.client_get_default()
            use_quick_open = client.get_bool(KEY("/general/quick_open_enable"))
            quick_open_in_current_terminal = client.get_bool(KEY("/general/quick_open_in_current_terminal"))
            cmdline = client.get_string(KEY("/general/quick_open_command_line"))
            if use_quick_open:
                for _useless, _otheruseless, extractor in QUICK_OPEN_MATCHERS:
                    g = re.compile(extractor).match(value)
                    if g and len(g.groups()) == 2:
                        filename = g.group(1)
                        line_number = g.group(2)
                        filepath = filename
                        if not quick_open_in_current_terminal:
                            curdir = self.get_current_directory()
                            filepath = os.path.join(curdir, filename)
                            if not os.path.exists(filepath):
                                logging.info("Cannot open file %s, it doesn't exists locally"
                                             "(current dir: %s)", filepath,
                                             os.path.curdir)
                                continue
                        # for quick_open_in_current_terminal, we run the command line directly in
                        # the tab so relative path is enough.
                        #
                        # We do not test for file existence, because it doesn't work in ssh
                        # sessions.
                        logging.debug("Opening file %s at line %s", filepath, line_number)
                        resolved_cmdline = cmdline % {"file_path": filepath,
                                                      "line_number": line_number}
                        logging.debug("Command line: %s", resolved_cmdline)
                        if quick_open_in_current_terminal:
                            logging.debug("Executing it in current tab")
                            instance.execute_command(resolved_cmdline)
                        else:
                            logging.debug("Executing it independently")
                            subprocess.call(resolved_cmdline, shell=True)
                        found = True
                        break
            if not found:
                print "found tag:", tag
                print "found item:", value
                print "TERMINAL_MATCH_TAGS", TERMINAL_MATCH_TAGS
                if tag in TERMINAL_MATCH_TAGS:
                    if TERMINAL_MATCH_TAGS[tag] == 'schema':
                        # value here should not be changed, it is right and
                        # ready to be used.
                        pass
                    elif TERMINAL_MATCH_TAGS[tag] == 'http':
                        value = 'http://%s' % value
                    elif TERMINAL_MATCH_TAGS[tag] == 'https':
                        value = 'https://%s' % value
                    elif TERMINAL_MATCH_TAGS[tag] == 'ftp':
                        value = 'ftp://%s' % value
                    elif TERMINAL_MATCH_TAGS[tag] == 'email':
                        value = 'mailto:%s' % value

                if value:
                    cmd = ["xdg-open", value]
                    print "Opening link: {}".format(cmd)
                    subprocess.Popen(cmd, shell=False)
                    # gtk.show_uri(self.window.get_screen(), value,
                    #              gtk.gdk.x11_get_server_time(self.window))
        elif event.button == 3 and matched_string:
            self.matched_value = matched_string[0]

    def set_font(self, font):
        self.font = font
        self.set_font_scale_index(0)

    def set_font_scale_index(self, scale_index):
        self.font_scale_index = clamp(scale_index, -6, 12)

        font = FontDescription(self.font.to_string())
        scale_factor = 2 ** (self.font_scale_index / 6)
        new_size = int(scale_factor * font.get_size())

        if font.get_size_is_absolute():
            font.set_absolute_size(new_size)
        else:
            font.set_size(new_size)

        super(GuakeTerminal, self).set_font(font)

    font_scale = property(
        fset=set_font_scale_index,
        fget=lambda self: self.font_scale_index
    )

    def increase_font_size(self):
        self.font_scale += 1

    def decrease_font_size(self):
        self.font_scale -= 1


class GuakeTerminalBox(gtk.HBox):

    """A box to group the terminal and a scrollbar.
    """

    def __init__(self):
        super(GuakeTerminalBox, self).__init__()
        self.terminal = GuakeTerminal()
        self.add_terminal()
        self.add_scroll_bar()

    def add_terminal(self):
        """Packs the terminal widget.
        """
        self.pack_start(self.terminal, True, True)
        self.terminal.show()

    def add_scroll_bar(self):
        """Packs the scrollbar.
        """
        adj = self.terminal.get_adjustment()
        scroll = gtk.VScrollbar(adj)
        scroll.set_no_show_all(True)
        self.pack_start(scroll, False, False)


class Guake(SimpleGladeApp):

    """Guake main class. Handles specialy the main window.
    """

    def __init__(self):
        super(Guake, self).__init__(gladefile('guake.glade'))
        self.client = gconf.client_get_default()

        # setting global hotkey and showing a pretty notification =)
        guake.globalhotkeys.init()

        # Cannot use "getattr(gtk.Window().get_style(), "base")[int(gtk.STATE_SELECTED)]"
        # since theme has not been applied before first show_all
        self.selected_color = None

        self.isPromptQuitDialogOpened = False

        # trayicon!
        try:
            import appindicator
        except ImportError:
            img = pixmapfile('guake-tray.png')
            self.tray_icon = gtk.status_icon_new_from_file(img)
            self.tray_icon.set_tooltip(_('Guake Terminal'))
            self.tray_icon.connect('popup-menu', self.show_menu)
            self.tray_icon.connect('activate', self.show_hide)
        else:
            self.tray_icon = appindicator.Indicator(_("guake-indicator"), _("guake-tray"), appindicator.CATEGORY_OTHER)
            self.tray_icon.set_icon("guake-tray")
            self.tray_icon.set_status(appindicator.STATUS_ACTIVE)
            menu = self.get_widget('tray-menu')
            show = gtk.MenuItem(_('Show'))
            show.set_sensitive(True)
            show.connect('activate', self.show_hide)
            show.show()
            menu.prepend(show)
            self.tray_icon.set_menu(menu)

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

        # check and set ARGB for real transparency
        screen = self.window.get_screen()
        colormap = screen.get_rgba_colormap()
        if colormap is None:
            self.has_argb = False
        else:
            self.window.set_colormap(colormap)
            self.has_argb = self.window.get_screen().is_composited()

            def composited_changed(screen):
                self.has_argb = screen.is_composited()
                self.set_background_transparency(
                    self.client.get_int(KEY('/style/background/transparency')))
                self.set_background_image(
                    self.client.get_string(KEY('/style/background/image')))

            self.window.get_screen().connect("composited-changed",
                                             composited_changed)

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

        # holds fullscreen status
        self.is_fullscreen = False

        # holds the timestamp of the losefocus event
        self.losefocus_time = 0

        # holds the timestamp of the previous show/hide action
        self.prev_showhide_time = 0

        # double click stuff
        def double_click(hbox, event):
            """Handles double clicks on tabs area and when receive
            one, calls add_tab.
            """
            if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
                self.add_tab()
        evtbox = self.get_widget('event-tabs')
        evtbox.connect('button-press-event', double_click)

        # Flag to prevent guake hide when window_losefocus is true and
        # user tries to use the context menu.
        self.showing_context_menu = False

        def hide_context_menu(menu):
            """Turn context menu flag off to make sure it is not being
            shown.
            """
            self.showing_context_menu = False
        self.get_widget('context-menu').connect('hide', hide_context_menu)
        self.get_widget('tab-menu').connect('hide', hide_context_menu)
        self.window.connect('focus-out-event', self.on_window_losefocus)

        # Handling the delete-event of the main window to avoid
        # problems when closing it.
        def destroy(*args):
            self.hide()
            return True
        self.window.connect('delete-event', destroy)

        # Flag to completely disable losefocus hiding
        self.disable_losefocus_hiding = False

        # this line is important to resize the main window and make it
        # smaller.
        self.window.set_geometry_hints(min_width=1, min_height=1)

        # special trick to avoid the "lost guake on Ubuntu 'Show Desktop'" problem.
        # DOCK makes the window foundable after having being "lost" after "Show Desktop"
        self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DOCK)
        # Restore back to normal behavior
        self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_NORMAL)

        # resizer stuff
        self.resizer.connect('motion-notify-event', self.on_resizer_drag)

        # adding the first tab on guake
        self.add_tab()

        # loading and setting up configuration stuff
        GConfHandler(self)
        GConfKeyHandler(self)
        self.hotkeys = guake.globalhotkeys.GlobalHotkey()
        self.load_config()

        key = self.client.get_string(GKEY('show_hide'))
        keyval, mask = gtk.accelerator_parse(key)
        label = gtk.accelerator_get_label(keyval, mask)
        filename = pixmapfile('guake-notification.png')

        if self.client.get_bool(KEY('/general/start_fullscreen')):
            self.fullscreen()

        if not self.hotkeys.bind(key, self.show_hide):
            guake.notifier.show_message(
                _('Guake!'),
                _('A problem happened when binding <b>%s</b> key.\n'
                  'Please use Guake Preferences dialog to choose another '
                  'key') % xml_escape(label), filename)
            self.client.set_bool(KEY('/general/use_trayicon'), True)

        elif self.client.get_bool(KEY('/general/use_popup')):
            # Pop-up that shows that guake is working properly (if not
            # unset in the preferences windows)
            guake.notifier.show_message(
                _('Guake!'),
                _('Guake is now running,\n'
                  'press <b>%s</b> to use it.') % xml_escape(label), filename)

    def set_background_transparency(self, transparency):
        for i in self.term_list:
            i.set_background_saturation(transparency / 100.0)
            if self.has_argb:
                i.set_opacity(int((100 - transparency) / 100.0 * 65535))

    def set_background_image(self, image):
        for i in self.term_list:
            if image and os.path.exists(image):
                i.set_background_image_file(image)
                i.set_background_transparent(False)
            else:
                """We need to clear the image if it's not set but there is
                a bug in vte python bindings which doesn't allow None to be
                passed to set_background_image (C GTK function expects NULL).
                The user will need to restart Guake after clearing the image.
                i.set_background_image(None)
                """
                if self.has_argb:
                    i.set_background_transparent(False)
                else:
                    i.set_background_transparent(True)

    def set_bgcolor(self, bgcolor, tab=None):
        """Set the background color of `tab' or the current tab to `bgcolor'."""
        if not self.term_list:
            self.add_tab()
        index = tab or self.notebook.get_current_page()
        self.term_list[index].custom_bgcolor = gtk.gdk.color_parse(bgcolor)

    def set_fgcolor(self, fgcolor, tab=None):
        """Set the foreground color of `tab' or the current tab to `fgcolor'."""
        if not self.term_list:
            self.add_tab()
        index = tab or self.notebook.get_current_page()
        self.term_list[index].custom_fgcolor = gtk.gdk.color_parse(fgcolor)

    def execute_command(self, command, tab=None):
        """Execute the `command' in the `tab'. If tab is None, the
        command will be executed in the currently selected
        tab. Command should end with '\n', otherwise it will be
        appended to the string.
        """
        if not self.term_list:
            self.add_tab()

        if command[-1] != '\n':
            command += '\n'

        index = self.notebook.get_current_page()
        self.term_list[tab or index].feed_child(command)

    def on_resizer_drag(self, widget, event):
        """Method that handles the resize drag. It does not actuall
        moves the main window. It just set the new window size in
        gconf.
        """
        (x, y), mod = event.device.get_state(widget.window)
        if 'GDK_BUTTON1_MASK' not in mod.value_names:
            return

        screen = self.window.get_screen()
        x, y, _ = screen.get_root_window().get_pointer()
        screen_no = screen.get_monitor_at_point(x, y)

        max_height = screen.get_monitor_geometry(screen_no).height
        percent = y / (max_height / 100)

        if percent < 1:
            percent = 1

        self.client.set_int(KEY('/general/window_height'), int(percent))

    def on_window_losefocus(self, window, event):
        """Hides terminal main window when it loses the focus and if
        the window_losefocus gconf variable is True.
        """
        if self.disable_losefocus_hiding or self.showing_context_menu:
            return

        if self.isPromptQuitDialogOpened:
            return

        value = self.client.get_bool(KEY('/general/window_losefocus'))
        visible = window.get_property('visible')
        if value and visible:
            self.losefocus_time = \
                gtk.gdk.x11_get_server_time(self.window.window)
            self.hide()

    def show_menu(self, status_icon, button, activate_time):
        """Show the tray icon menu.
        """
        menu = self.get_widget('tray-menu')
        menu.popup(None, None, gtk.status_icon_position_menu,
                   button, activate_time, status_icon)

    def show_context_menu(self, terminal, event):
        """Show the context menu, only with a right click on a vte
        Terminal.
        """
        if event.button != 3:
            return False

        self.showing_context_menu = True

        guake_clipboard = gtk.clipboard_get()
        if not guake_clipboard.wait_is_text_available():
            self.get_widget('context_paste').set_sensitive(False)
        else:
            self.get_widget('context_paste').set_sensitive(True)

        current_selection = ''
        current_term = self.term_list[self.notebook.get_current_page()]
        if current_term.get_has_selection():
            current_term.copy_clipboard()
            guake_clipboard = gtk.clipboard_get()
            current_selection = guake_clipboard.wait_for_text().rstrip()

            if len(current_selection) > 20:
                current_selection = current_selection[:17] + "..."

        if current_selection:
            self.get_widget('context_search_on_web').set_label(_("Search on Web: '%s'") % current_selection)
            self.get_widget('context_search_on_web').set_sensitive(True)
        else:
            self.get_widget('context_search_on_web').set_label(_("Search on Web (no selection)"))
            self.get_widget('context_search_on_web').set_sensitive(False)

        context_menu = self.get_widget('context-menu')
        context_menu.popup(None, None, None, 3, gtk.get_current_event_time())
        return True

    def show_rename_current_tab_dialog(self, target, event):
        """On double-click over a tab, show the rename dialog.
        """
        if event.button == 1:
            if event.type == gtk.gdk._2BUTTON_PRESS:
                self.accel_rename_current_tab()
                self.set_terminal_focus()
                self.selected_tab.pressed()
                return

    def show_tab_menu(self, target, event):
        """Shows the tab menu with a right click. After that, the
        focus come back to the terminal.
        """
        if event.button == 3:
            self.showing_context_menu = True
            self.selected_tab = target
            menu = self.get_widget('tab-menu')
            menu.popup(None, None, None, 3, event.get_time())
        self.set_terminal_focus()

    def show_about(self, *args):
        """Hides the main window and creates an instance of the About
        Dialog.
        """
        self.hide()
        AboutDialog()

    def show_prefs(self, *args):
        """Hides the main window and creates an instance of the
        Preferences window.
        """
        self.hide()
        PrefsDialog().show()

    def show_hide(self, *args):
        """Toggles the main window visibility
        """
        event_time = self.hotkeys.get_current_event_time()

        if self.losefocus_time and \
                self.losefocus_time >= event_time and \
                (self.losefocus_time - event_time) < 10:
            self.losefocus_time = 0
            return

        # limit rate at which the visibility can be toggled.
        if self.prev_showhide_time and event_time and \
                (event_time - self.prev_showhide_time) < 65:
            return
        self.prev_showhide_time = event_time

        GDK_WINDOW_STATE_STICKY = 8
        GDK_WINDOW_STATE_WITHDRAWN = 1
        GDK_WINDOW_STATE_ABOVE = 32

        if self.window.window:
            print "DBG: gtk.gdk.WindowState =", self.window.window.get_state()
            print "DBG: gtk.gdk.WindowState =", int(self.window.window.get_state())
            print ("DBG: GDK_WINDOW_STATE_STICKY? %s" %
                   (bool(int(self.window.window.get_state()) & GDK_WINDOW_STATE_STICKY),))
            print ("DBG: GDK_WINDOW_STATE_WITHDRAWN? %s" %
                   (bool(int(self.window.window.get_state()) & GDK_WINDOW_STATE_WITHDRAWN,)))
            print ("DBG: GDK_WINDOW_STATE_ABOVE? %s" %
                   (bool(int(self.window.window.get_state()) & GDK_WINDOW_STATE_ABOVE,)))
        if not self.window.get_property('visible'):
            print "DBG: Showing the terminal"
            self.show()
            self.set_terminal_focus()
        elif (self.client.get_bool(KEY('/general/focus_if_open')) and
                self.window.window and
                (int(self.window.window.get_state()) & GDK_WINDOW_STATE_STICKY or
                 int(self.window.window.get_state()) & GDK_WINDOW_STATE_WITHDRAWN
                 )):
            print "DBG: Restoring the focus to the terminal"
            self.window.window.focus()
            self.set_terminal_focus()
        else:
            print "DBG: hiding the terminal"
            self.hide()

    def show(self):
        """Shows the main window and grabs the focus on it.
        """
        # setting window in all desktops
        window_rect = self.set_final_window_rect()
        self.get_widget('window-root').stick()

        # add tab must be called before window.show to avoid a
        # blank screen before adding the tab.
        if not self.term_list:
            self.add_tab()

        self.window.set_keep_below(False)
        self.window.show_all()

        if self.selected_color is None:
            self.selected_color = getattr(self.window.get_style(), "light")[int(gtk.STATE_SELECTED)]

            # Reapply the tab color to all button in the tab list, since at least one don't have the select color
            # set. This needs to happen AFTER the first show_all, since before the gtk has not loaded the right
            # colors yet.
            for tab in self.tabs.get_children():
                if isinstance(tab, gtk.RadioButton):
                    tab.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.Color(str(self.selected_color)))

        # this work arround an issue in fluxbox
        self.window.move(window_rect.x, window_rect.y)

        self.client.notify(KEY('/general/window_height'))

        try:
            # does it work in other gtk backends
            time = gtk.gdk.x11_get_server_time(self.window.window)
        except AttributeError:
            time = 0

        self.window.window.show()
        self.window.window.focus(time)

        # This is here because vte color configuration works only
        # after the widget is shown.
        self.client.notify(KEY('/style/font/color'))
        self.client.notify(KEY('/style/background/color'))

    def hide(self):
        """Hides the main window of the terminal and sets the visible
        flag to False.
        """
        self.window.hide()  # Don't use hide_all here!

    def get_final_window_monitor(self):
        """Gets the final screen number for the main window of guake.
        """

        screen = self.window.get_screen()

        # fetch settings
        use_mouse = self.client.get_bool(KEY('/general/mouse_display'))
        dest_screen = self.client.get_int(KEY('/general/display_n'))

        if use_mouse:
            x, y, _ = screen.get_root_window().get_pointer()
            dest_screen = screen.get_monitor_at_point(x, y)

        # If Guake is configured to use a screen that is not currently attached,
        # default to 'primary display' option.
        n_screens = screen.get_n_monitors()
        if dest_screen > n_screens - 1:
            self.client.set_bool(KEY('/general/mouse_display'), False)
            self.client.set_int(KEY('/general/display_n'), dest_screen)
            dest_screen = screen.get_primary_monitor()

        # Use primary display if configured
        if dest_screen == ALWAYS_ON_PRIMARY:
            dest_screen = screen.get_primary_monitor()

        return dest_screen

    def set_final_window_rect(self):
        """Sets the final size and location of the main window of guake. The height
        is the window_height property, width is window_width and the
        horizontal alignment is given by window_alignment.
        """

        # fetch settings
        height_percents = self.client.get_float(KEY('/general/window_height_f'))
        if not height_percents:
            height_percents = self.client.get_int(KEY('/general/window_height'))

        width_percents = self.client.get_float(KEY('/general/window_width_f'))
        if not width_percents:
            width_percents = self.client.get_int(KEY('/general/window_width'))
        halignment = self.client.get_int(KEY('/general/window_halignment'))
        valignment = self.client.get_int(KEY('/general/window_valignment'))

        print "height_percents", height_percents
        print "width_percents", width_percents
        print "halignment", halignment
        print "valignment", valignment

        # get the rectangle just from the destination monitor
        screen = self.window.get_screen()
        monitor = self.get_final_window_monitor()
        window_rect = screen.get_monitor_geometry(monitor)

        if os.environ.get('DESKTOP_SESSION') == "ubuntu":
            unity_hide = self.client.get_int(KEY('/apps/compiz-1/plugins/'
                                                 'unityshell/screen0/options/launcher_hide_mode'))
            # launcher_hide_mode = 1 => autohide
            if unity_hide != 1:
                # Size of the icons for Unity in Ubuntu <= 12.04
                # TODO Ubuntu 12.10 use dconf :
                # /org/compiz/profiles/unity/plugins/unityshell/icon-size
                unity_icon_size = self.client.get_int(KEY('/apps/compiz-1/'
                                                          'plugins/unityshell/screen0/options/icon_size'))
                if not unity_icon_size:
                    # If not found, it should be because of newer implementation of unity.
                    # Dock is 64 pixel of width on my system, hope this is so on others...
                    unity_dock = 64
                else:
                    unity_dock = unity_icon_size + 17
                print "correcting window width because of launcher width {} (from {} to {})".format(
                    unity_dock, window_rect.width, window_rect.width - unity_dock)

                window_rect.width = window_rect.width - unity_dock

        total_width = window_rect.width
        total_height = window_rect.height

        print "total_width", total_width
        print "total_height", total_height

        window_rect.height = window_rect.height * height_percents / 100
        window_rect.width = window_rect.width * width_percents / 100

        print "window_rect.x", window_rect.x
        print "window_rect.y", window_rect.y
        print "window_rect.height", window_rect.height
        print "window_rect.width", window_rect.width

        if window_rect.width < total_width:
            if halignment == ALIGN_CENTER:
                print "aligning to center!"
                window_rect.x += (total_width - window_rect.width) / 2
            elif halignment == ALIGN_LEFT:
                print "aligning to left!"
                window_rect.x += 0
            elif halignment == ALIGN_RIGHT:
                print "aligning to right!"
                window_rect.x += total_width - window_rect.width
        if window_rect.height < total_height:
            if valignment == ALIGN_BOTTOM:
                window_rect.y += (total_height - window_rect.height)

        self.window.resize(window_rect.width, window_rect.height)
        self.window.move(window_rect.x, window_rect.y)
        print "Moving/Resizing to: window_rect", window_rect

        return window_rect

    def get_running_fg_processes(self):
        """Get the number processes for each terminal/tab. The code is taken
        from gnome-terminal.
        """
        total_procs = 0
        term_idx = 0
        for terminal in self.term_list:
            fdpty = terminal.get_pty()
            term_pid = self.pid_list[term_idx]
            fgpid = posix.tcgetpgrp(fdpty)
            if not (fgpid == -1 or fgpid == term_pid):
                total_procs += 1
            term_idx += 1
        return total_procs

    # -- configuration --

    def load_config(self):
        """"Just a proxy for all the configuration stuff.
        """
        self.client.notify(KEY('/general/use_trayicon'))
        self.client.notify(KEY('/general/prompt_on_quit'))
        self.client.notify(KEY('/general/window_tabbar'))
        self.client.notify(KEY('/general/mouse_display'))
        self.client.notify(KEY('/general/display_n'))
        self.client.notify(KEY('/general/window_ontop'))
        self.client.notify(KEY('/general/window_height'))
        self.client.notify(KEY('/general/window_width'))
        self.client.notify(KEY('/general/use_scrollbar'))
        self.client.notify(KEY('/general/history_size'))
        self.client.notify(KEY('/general/show_resizer'))
        self.client.notify(KEY('/general/use_vte_titles'))
        self.client.notify(KEY('/general/quick_open_enable'))
        self.client.notify(KEY('/general/quick_open_command_line'))
        self.client.notify(KEY('/style/cursor_shape'))
        self.client.notify(KEY('/style/font/style'))
        self.client.notify(KEY('/style/font/color'))
        self.client.notify(KEY('/style/font/palette'))
        self.client.notify(KEY('/style/background/color'))
        self.client.notify(KEY('/style/background/image'))
        self.client.notify(KEY('/style/background/transparency'))
        self.client.notify(KEY('/general/use_default_font'))
        self.client.notify(KEY('/general/compat_backspace'))
        self.client.notify(KEY('/general/compat_delete'))

    def accel_quit(self, *args):
        """Callback to prompt the user whether to quit Guake or not.
        """
        if self.client.get_bool(KEY('/general/prompt_on_quit')):
            procs = self.get_running_fg_processes()
            if procs >= 1:
                self.isPromptQuitDialogOpened = True
                dialog = PromptQuitDialog(self.window, procs)
                response = dialog.run() == gtk.RESPONSE_YES
                dialog.destroy()
                self.isPromptQuitDialogOpened = False
                if response:
                    gtk.main_quit()
            else:
                gtk.main_quit()
        else:
            gtk.main_quit()

    def accel_zoom_in(self, *args):
        """Callback to zoom in.
        """
        for term in self.term_list:
            term.increase_font_size()
        return True

    def accel_zoom_out(self, *args):
        """Callback to zoom out.
        """
        for term in self.term_list:
            term.decrease_font_size()
        return True

    def accel_increase_height(self, *args):
        """Callback to increase height.
        """
        try:
            height = self.client.get_float(KEY('/general/window_height'))
        except:
            height = self.client.get_int(KEY('/general/window_height'))

        self.client.set_int(KEY('/general/window_height'), int(height) + 2)
        return True

    def accel_decrease_height(self, *args):
        """Callback to decrease height.
        """
        try:
            height = self.client.get_float(KEY('/general/window_height'))
        except:
            height = self.client.get_int(KEY('/general/window_height'))

        self.client.set_int(KEY('/general/window_height'), int(height) - 2)
        return True

    def accel_add(self, *args):
        """Callback to add a new tab. Called by the accel key.
        """
        self.add_tab()
        return True

    def accel_prev(self, *args):
        """Callback to go to the previous tab. Called by the accel key.
        """
        if self.notebook.get_current_page() == 0:
            self.notebook.set_current_page(self.notebook.get_n_pages() - 1)
        else:
            self.notebook.prev_page()
        return True

    def accel_next(self, *args):
        """Callback to go to the next tab. Called by the accel key.
        """
        if self.notebook.get_current_page() + 1 == self.notebook.get_n_pages():
            self.notebook.set_current_page(0)
        else:
            self.notebook.next_page()
        return True

    def gen_accel_switch_tabN(self, N):
        """Generates callback (which called by accel key) to go to the Nth tab.
        """
        def callback(*args):
            if N >= 0 and N < self.notebook.get_n_pages():
                self.notebook.set_current_page(N)
            return True

        return callback

    def accel_rename_current_tab(self, *args):
        """Callback to show the rename tab dialog. Called by the accel
        key.
        """
        pagepos = self.notebook.get_current_page()
        self.selected_tab = self.tabs.get_children()[pagepos]
        self.on_rename_current_tab_activate()
        return True

    def accel_copy_clipboard(self, *args):
        """Callback to copy text in the shown terminal. Called by the
        accel key.
        """
        current_term = self.term_list[self.notebook.get_current_page()]

        if current_term.get_has_selection():
            current_term.copy_clipboard()
        elif current_term.matched_value:
            guake_clipboard = gtk.clipboard_get()
            guake_clipboard.set_text(current_term.matched_value)

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
        window. Called by the accel key.
        """
        if not self.is_fullscreen:
            self.fullscreen()
        else:
            self.unfullscreen()
        return True

    def fullscreen(self):
        self.window.fullscreen()
        self.is_fullscreen = True

        # The resizer widget really don't need to be shown in
        # fullscreen mode, but tabbar will only be shown if a
        # hidden gconf key is false.
        self.resizer.hide()
        if not self.client.get_bool(KEY('general/toolbar_visible_in_fullscreen')):
            self.toolbar.hide()

    def unfullscreen(self):
        self.set_final_window_rect()
        self.window.unfullscreen()
        self.is_fullscreen = False

        # making sure that tabbar and resizer will come back to
        # their default state.
        self.client.notify(KEY('/general/window_tabbar'))
        self.client.notify(KEY('/general/show_resizer'))

        # make sure the window size is correct after returning
        # from fullscreen. broken on old compiz/metacity versions :C
        self.client.notify(KEY('/general/window_height'))

    # -- callbacks --

    def on_terminal_exited(self, term, widget):
        """When a terminal is closed, shell process should be killed,
        this is the method that does that, or, at least calls
        `delete_tab' method to do the work.
        """
        if libutempter is not None:
            libutempter.utempter_remove_record(term.get_pty())
        self.delete_tab(self.notebook.page_num(widget), kill=False)

    def on_terminal_title_changed(self, vte, box):
        use_them = self.client.get_bool(KEY("/general/use_vte_titles"))
        if not use_them:
            return
        page = self.notebook.page_num(box)
        tab = self.tabs.get_children()[page]
        # if tab has been renamed by user, don't override.
        if not getattr(tab, 'custom_label_set', False):
            tab.set_label(vte.get_window_title())

    def on_rename_current_tab_activate(self, *args):
        """Shows a dialog to rename the current tab.
        """
        entry = gtk.Entry()
        entry.set_text(self.selected_tab.get_label())
        entry.set_property('can-default', True)
        entry.show()

        vbox = gtk.VBox()
        vbox.set_border_width(6)
        vbox.show()

        dialog = gtk.Dialog(_("Rename tab"),
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

        self.disable_losefocus_hiding = True
        response = dialog.run()
        self.disable_losefocus_hiding = False

        if response == gtk.RESPONSE_ACCEPT:
            new_text = entry.get_text()
            self.selected_tab.set_label(new_text)
            # if user sets empty name, consider he wants default behavior.
            setattr(self.selected_tab, 'custom_label_set', bool(new_text))
            # trigger titling handler in case that custom label has been reset
            current_vte = self.term_list[self.notebook.get_current_page()]
            current_vte.emit('window-title-changed')

        dialog.destroy()
        self.set_terminal_focus()

    def on_close_activate(self, *args):
        """Tab context menu close handler
        """
        tabs = self.tabs.get_children()
        pagepos = tabs.index(self.selected_tab)
        self.delete_tab(pagepos)

    def on_drag_data_received(self, widget, context,
                              x, y,
                              selection,
                              target,
                              timestamp,
                              box):
        droppeduris = selection.get_uris()

        # url-unquote the list, strip file:// schemes, handle .desktop-s
        pathlist = []
        app = None
        for uri in droppeduris:
            scheme, _, path, _, _ = urlsplit(uri)

            if scheme != "file":
                pathlist.append(uri)
            else:
                filename = url2pathname(path)

                desktopentry = DesktopEntry()
                try:
                    desktopentry.parse(filename)
                except xdg.Exceptions.ParsingError:
                    pathlist.append(filename)
                    continue

                if desktopentry.getType() == 'Link':
                    pathlist.append(desktopentry.getURL())

                if desktopentry.getType() == 'Application':
                    app = desktopentry.getExec()

        if app and len(droppeduris) == 1:
            text = app
        else:
            text = str.join("", (shell_quote(path) + " " for path in pathlist))

        box.terminal.feed_child(text)
        return True

    # -- tab related functions --

    def close_tab(self, *args):
        """Closes the current tab.
        """
        pagepos = self.notebook.get_current_page()
        self.delete_tab(pagepos)

    def rename_tab(self, tab_index, new_text):
        """Rename an already added tab by its index.
        """
        try:
            tab = self.tabs.get_children()[tab_index]
        except IndexError:
            pass
        else:
            tab.set_label(new_text)
            setattr(tab, 'custom_label_set', new_text != "-")
            current_vte = self.term_list[tab_index]
            current_vte.emit('window-title-changed')

    def rename_current_tab(self, new_text):
        """Sets the `self.selected_tab' var with the selected radio
        button and change its label to `new_text'.
        """
        pagepos = self.notebook.get_current_page()
        self.selected_tab = self.tabs.get_children()[pagepos]
        self.selected_tab.set_label(new_text)

        # it's hard to pass an empty string as a command line argument,
        # so we'll interpret single dash "-" as a "reset custom title" request
        setattr(self.selected_tab, 'custom_label_set', new_text != "-")

        # trigger titling handler in case that custom label has been reset
        current_vte = self.term_list[self.notebook.get_current_page()]
        current_vte.emit('window-title-changed')

    def get_current_dir(self):
        """Gets the working directory of the current tab to create a
        new one in the same dir.
        """
        active_pagepos = self.notebook.get_current_page()
        directory = os.path.expanduser('~')
        if active_pagepos >= 0:
            cwd = os.readlink("/proc/%d/cwd" % self.pid_list[active_pagepos])
            if os.path.exists(cwd):
                directory = cwd
        return directory

    def get_fork_params(self, default_params=None):
        """Return all parameters to be passed to the fork_command
        method of a vte terminal. Params returned can be expanded by
        the `params' parameter that receive a dictionary.
        """
        # use dictionary to pass named params to work around command
        # parameter in fork_command not accepting None as argument.
        # When we pass None as command, vte starts the default user
        # shell.
        params = {}

        shell = self.client.get_string(KEY('/general/default_shell'))
        if shell and os.path.exists(shell):
            params['command'] = shell

        login_shell = self.client.get_bool(KEY('/general/use_login_shell'))
        if login_shell:
            params['argv'] = ['-']

        if self.client.get_bool(KEY('/general/open_tab_cwd')):
            params['directory'] = self.get_current_dir()
        params['loglastlog'] = login_shell

        # Leting caller change/add values to fork params.
        if default_params:
            params.update(default_params)

        # Environment variables are not actually parameters but they
        # need to be set before calling terminal.fork_command()
        # method. So I found this place good to do it.
        self.update_proxy_vars()
        return params

    def update_proxy_vars(self):
        """This method updates http{s,}_proxy environment variables
        with values found in gconf.
        """
        proxy = '/system/http_proxy/'
        if self.client.get_bool(proxy + 'use_http_proxy'):
            host = self.client.get_string(proxy + 'host')
            port = self.client.get_int(proxy + 'port')
            if self.client.get_bool(proxy + 'use_same_proxy'):
                ssl_host = host
                ssl_port = port
            else:
                ssl_host = self.client.get_string('/system/proxy/secure_host')
                ssl_port = self.client.get_int('/system/proxy/secure_port')

            if self.client.get_bool(proxy + 'use_authentication'):
                auth_user = self.client.get_string(
                    proxy + 'authentication_user')
                auth_pass = self.client.get_string(
                    proxy + 'authentication_password')
                auth_pass = quote_plus(auth_pass, '')
                os.environ['http_proxy'] = 'http://%s:%s@%s:%d' % (
                    auth_user, auth_pass, host, port)
                os.environ['https_proxy'] = 'http://%s:%s@%s:%d' % (
                    auth_user, auth_pass, ssl_host, ssl_port)
            else:
                os.environ['http_proxy'] = 'http://%s:%d' % (host, port)
                os.environ['https_proxy'] = 'http://%s:%d' % (
                    ssl_host, ssl_port)

    def add_tab(self, directory=None):
        """Adds a new tab to the terminal notebook.
        """
        box = GuakeTerminalBox()
        box.terminal.grab_focus()
        box.terminal.drag_dest_set(gtk.DEST_DEFAULT_MOTION |
                                   gtk.DEST_DEFAULT_DROP |
                                   gtk.DEST_DEFAULT_HIGHLIGHT,
                                   [('text/uri-list', gtk.TARGET_OTHER_APP, 0)],
                                   gtk.gdk.ACTION_COPY
                                   )
        box.terminal.connect('button-press-event', self.show_context_menu)
        box.terminal.connect('child-exited', self.on_terminal_exited, box)
        box.terminal.connect('window-title-changed',
                             self.on_terminal_title_changed, box)
        box.terminal.connect('drag-data-received',
                             self.on_drag_data_received,
                             box)

        # -- Ubuntu has a patch to libvte which disables mouse scrolling in apps
        # -- like vim and less by default. If this is the case, enable it back.
        if hasattr(box.terminal, "set_alternate_screen_scroll"):
            box.terminal.set_alternate_screen_scroll(True)

        box.show()

        self.term_list.append(box.terminal)

        # We can choose the directory to vte launch. It is important
        # to be used by dbus interface. I'm testing if directory is a
        # string because when binded to a signal, the first param can
        # be a button not a directory.
        default_params = {}
        if isinstance(directory, basestring):
            default_params['directory'] = directory

        final_params = self.get_fork_params(default_params)
        pid = box.terminal.fork_command(**final_params)
        if libutempter is not None:
            # After the fork_command we add this new tty to utmp !
            libutempter.utempter_add_record(box.terminal.get_pty(), os.uname()[1])
        box.terminal.pid = pid
        self.pid_list.append(pid)

        # Adding a new radio button to the tabbar
        label = box.terminal.get_window_title() or _("Terminal")
        tabs = self.tabs.get_children()
        parent = tabs and tabs[0] or None

        bnt = gtk.RadioButton(group=parent, label=label, use_underline=False)
        bnt.set_property('can-focus', False)
        bnt.set_property('draw-indicator', False)
        bnt.connect('button-press-event', self.show_tab_menu)
        bnt.connect('button-press-event', self.show_rename_current_tab_dialog)
        bnt.connect('clicked',
                    lambda *x: self.notebook.set_current_page(
                        self.notebook.page_num(box)
                    ))
        if self.selected_color is not None:
            bnt.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.Color(str(self.selected_color)))
        drag_drop_type = ("text/plain", gtk.TARGET_SAME_APP, 80)
        bnt.drag_dest_set(gtk.DEST_DEFAULT_ALL, [drag_drop_type], gtk.gdk.ACTION_MOVE)
        bnt.connect("drag_data_received", self.on_drop_tab)
        bnt.drag_source_set(gtk.gdk.BUTTON1_MASK, [drag_drop_type], gtk.gdk.ACTION_MOVE)
        bnt.connect("drag_data_get", self.on_drag_tab)
        bnt.show()

        self.tabs.pack_start(bnt, expand=False, padding=1)

        self.notebook.append_page(box, None)
        self.notebook.set_current_page(self.notebook.page_num(box))
        box.terminal.grab_focus()
        self.load_config()

        if self.is_fullscreen:
            self.fullscreen()

    def on_drag_tab(self, widget, context, selection, targetType, eventTime):
        tab_pos = self.tabs.get_children().index(widget)
        selection.set(selection.target, 32, str(tab_pos))

    def on_drop_tab(self, widget, context, x, y, selection, targetType, data):
        old_tab_pos = int(selection.get_text())
        new_tab_pos = self.tabs.get_children().index(widget)
        self.move_tab(old_tab_pos, new_tab_pos)

    def move_tab(self, old_tab_pos, new_tab_pos):
        self.notebook.reorder_child(self.notebook.get_nth_page(old_tab_pos), new_tab_pos)
        self.pid_list.insert(new_tab_pos, self.pid_list.pop(old_tab_pos))
        self.term_list.insert(new_tab_pos, self.term_list.pop(old_tab_pos))
        self.tabs.reorder_child(self.tabs.get_children()[old_tab_pos], new_tab_pos)

    def delete_tab(self, pagepos, kill=True):
        """This function will destroy the notebook page, terminal and
        tab widgets and will call the function to kill interpreter
        forked by vte.
        """
        self.tabs.get_children()[pagepos].destroy()
        self.notebook.remove_page(pagepos)
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
        try:
            os.kill(pid, signal.SIGHUP)
        except OSError:
            pass
        num_tries = 30

        while num_tries > 0:
            try:
                # Try to wait for the pid to be closed. If it does not
                # exist anymore, an OSError is raised and we can
                # safely ignore it.
                if os.waitpid(pid, os.WNOHANG)[0] != 0:
                    break
            except OSError:
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
        """Grabs the focus on the current tab.
        """
        page = self.notebook.get_current_page()
        self.term_list[page].grab_focus()

    def select_current_tab(self, notebook, user_data, page):
        """When current self.notebook page is changed, the tab bar
        made with radio buttons must be updated and this method does
        this work.
        """
        self.tabs.get_children()[page].set_active(True)

    def select_tab(self, tab_index):
        """Select an already added tab by its index.
        """
        try:
            self.tabs.get_children()[tab_index].set_active(True)
        except IndexError:
            pass

    def get_selected_tab(self):
        """return the selected tab index, it also set the
        self.selected_tab var.
        """
        pagepos = self.notebook.get_current_page()
        self.selected_tab = self.tabs.get_children()[pagepos]
        return pagepos

    def search_on_web(self, *args):
        """search on web the selected text
        """
        current_term = self.term_list[self.notebook.get_current_page()]

        if current_term.get_has_selection():
            current_term.copy_clipboard()
            guake_clipboard = gtk.clipboard_get()
            search_query = guake_clipboard.wait_for_text()
            search_query = quote_plus(search_query)
            if search_query:
                search_url = "https://www.google.com/#q=%s&safe=off" % (search_query,)
                gtk.show_uri(current_term.window.get_screen(), search_url,
                             gtk.gdk.x11_get_server_time(current_term.window))
        return True


def main():
    """Parses the command line parameters and decide if dbus methods
    should be called or not. If there is already a guake instance
    running it will be used and a True value will be returned,
    otherwise, false will be returned.
    """
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-f', '--fullscreen', dest='fullscreen',
                      action='store_true', default=False,
                      help=_('Put Guake in fullscreen mode'))

    parser.add_option('-t', '--toggle-visibility', dest='show_hide',
                      action='store_true', default=False,
                      help=_('Toggles the visibility of the terminal window'))

    parser.add_option('--show', dest="show",
                      action='store_true', default=False,
                      help=_('Shows Guake main window'))

    parser.add_option('--hide', dest='hide',
                      action='store_true', default=False,
                      help=_('Hides Guake main window'))

    parser.add_option('-p', '--preferences', dest='show_preferences',
                      action='store_true', default=False,
                      help=_('Shows Guake preference window'))

    parser.add_option('-a', '--about', dest='show_about',
                      action='store_true', default=False,
                      help=_('Shows Guake\'s about info'))

    parser.add_option('-n', '--new-tab', dest='new_tab',
                      action='store', default='',
                      help=_('Add a new tab (with current directory set to NEW_TAB)'))

    parser.add_option('-s', '--select-tab', dest='select_tab',
                      action='store', default='',
                      help=_('Select a tab (SELECT_TAB is the index of the tab)'))

    parser.add_option('-g', '--selected-tab', dest='selected_tab',
                      action='store_true', default=False,
                      help=_('Return the selected tab index.'))

    parser.add_option('-e', '--execute-command', dest='command',
                      action='store', default='',
                      help=_('Execute an arbitrary command in the selected tab.'))

    parser.add_option('-i', '--tab-index', dest='tab_index',
                      action='store', default='0',
                      help=_('Specify the tab to rename. Default is 0.'))

    parser.add_option('--bgcolor', dest='bgcolor',
                      action='store', default='',
                      help=_('Set the hexadecimal (#rrggbb) background color of the selected tab.'))

    parser.add_option('--fgcolor', dest='fgcolor',
                      action='store', default='',
                      help=_('Set the hexadecimal (#rrggbb) foreground color of the selected tab.'))

    parser.add_option('--rename-tab', dest='rename_tab',
                      metavar='TITLE',
                      action='store', default='',
                      help=_('Rename the specified tab. Reset to default if TITLE is a single dash "-".'))

    parser.add_option('-r', '--rename-current-tab', dest='rename_current_tab',
                      metavar='TITLE',
                      action='store', default='',
                      help=_('Rename the current tab. Reset to default if TITLE is a single dash "-".'))

    parser.add_option('-q', '--quit', dest='quit',
                      action='store_true', default=False,
                      help=_('Says to Guake go away =('))

    options = parser.parse_args()[0]

    # Trying to get an already running instance of guake. If it is not
    # possible, lets create a new instance. This function will return
    # a boolean value depending on this decision.
    try:
        bus = dbus.SessionBus()
        remote_object = bus.get_object(DBUS_NAME, DBUS_PATH)
        already_running = True
    except dbus.DBusException:
        global instance
        instance = Guake()
        remote_object = DbusManager(instance)
        already_running = False

    only_show_hide = True

    if options.fullscreen:
        remote_object.fullscreen()

    if options.show:
        remote_object.show()

    if options.hide:
        remote_object.hide()

    if options.show_preferences:
        remote_object.show_prefs()
        only_show_hide = False

    if options.new_tab:
        remote_object.add_tab(options.new_tab)
        only_show_hide = False

    if options.select_tab:
        selected = int(options.select_tab)
        remote_object.select_tab(selected)
        only_show_hide = False

    if options.selected_tab:
        selected = remote_object.get_selected_tab()
        sys.stdout.write('%d\n' % selected)
        only_show_hide = False

    if options.command:
        remote_object.execute_command(options.command)
        only_show_hide = False

    if options.tab_index and options.rename_tab:
        remote_object.rename_tab(int(options.tab_index), options.rename_tab)

    if options.bgcolor:
        remote_object.set_bgcolor(options.bgcolor)
        only_show_hide = False

    if options.fgcolor:
        remote_object.set_fgcolor(options.fgcolor)
        only_show_hide = False

    if options.rename_current_tab:
        remote_object.rename_current_tab(options.rename_current_tab)
        only_show_hide = False

    if options.show_about:
        remote_object.show_about()
        only_show_hide = False

    if options.quit:
        remote_object.quit()
        only_show_hide = False

    if already_running and only_show_hide:
        # here we know that guake was called without any parameter and
        # it is already running, so, lets toggle its visibility.
        remote_object.show_hide()

    if not already_running:
        startup_script = instance.client.get_string(KEY("/general/startup_script"))
        if startup_script:
            print "Calling startup script: ", startup_script
            pid = subprocess.Popen([startup_script], shell=True, stdin=None, stdout=None,
                                   stderr=None, close_fds=True)
            print "Script started with pid", pid
            # Please ensure this is the last line !!!!
    return already_running

if __name__ == '__main__':
    if not test_gconf():
        raise ShowableError(_('Guake can not init!'),
                            _('Gconf Error.\n'
                              'Have you installed <b>guake.schemas</b> properly?'))

    if not main():
        gtk.main()

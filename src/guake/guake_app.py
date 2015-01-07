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

import gconf
import gobject
import gtk
import os
import pygtk
import sys
import xdg.Exceptions

from urllib import quote_plus
from urllib import url2pathname
from urlparse import urlsplit
from xdg.DesktopEntry import DesktopEntry
from xml.sax.saxutils import escape as xml_escape

import guake.globalhotkeys
import guake.notifier

from guake.about import AboutDialog
from guake.common import _
from guake.common import gladefile
from guake.common import pixmapfile
from guake.common import shell_quote
from guake.gconfhandler import GConfHandler
from guake.gconfhandler import GConfKeyHandler
from guake.globals import ALIGN_BOTTOM
from guake.globals import ALIGN_CENTER
from guake.globals import ALIGN_LEFT
from guake.globals import ALIGN_RIGHT
from guake.globals import ALWAYS_ON_PRIMARY
from guake.globals import GKEY
from guake.globals import KEY
from guake.globals import LOCALE_DIR
from guake.globals import NAME
from guake.guake_notebook import GuakeNotebook
from guake.prefs import PrefsDialog
from guake.simplegladeapp import SimpleGladeApp
from guake.simplegladeapp import bindtextdomain
from guake.terminal import GuakeTerminalBox


libutempter = None
try:
    # this allow to run some commands that requires libuterm to
    # be injected in current process, as: wall
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
        self.hidden = True
        self.forceHide = False

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
            self.tray_icon = appindicator.Indicator(
                _("guake-indicator"), _("guake-tray"), appindicator.CATEGORY_OTHER)
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
        self.mainframe = self.get_widget('mainframe')
        self.mainframe.remove(self.get_widget('notebook-teminals'))
        self.notebook = GuakeNotebook()
        self.notebook.set_name("notebook-teminals")
        self.notebook.set_property("tab_pos", "bottom")
        self.notebook.set_property("show_tabs", False)
        self.notebook.set_property("show_border", False)
        self.notebook.set_property("visible", True)
        self.notebook.set_property("has_focus", True)
        self.notebook.set_property("can_focus", True)
        self.notebook.set_property("is_focus", True)
        self.notebook.set_property("enable_popup", True)
        self.notebook.connect("switch_page", self.select_current_tab)
        self.mainframe.add(self.notebook)
        self.set_tab_position()

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
        for t in self.notebook.iter_terminals():
            t.set_background_saturation(transparency / 100.0)
            if self.has_argb:
                t.set_opacity(int((100 - transparency) / 100.0 * 65535))

    def set_background_image(self, image):
        for t in self.notebook.iter_terminals():
            if image and os.path.exists(image):
                t.set_background_image_file(image)
                t.set_background_transparent(False)
            else:
                """We need to clear the image if it's not set but there is
                a bug in vte python bindings which doesn't allow None to be
                passed to set_background_image (C GTK function expects NULL).
                The user will need to restart Guake after clearing the image.
                r.set_background_image(None)
                """
                if self.has_argb:
                    t.set_background_transparent(False)
                else:
                    t.set_background_transparent(True)

    def set_bgcolor(self, bgcolor, tab=None):
        """Set the background color of `tab' or the current tab to `bgcolor'."""
        if not self.notebook.has_term():
            self.add_tab()
        index = tab or self.notebook.get_current_page()
        for terminal in self.notebook.get_terminals_for_tab(index):
            terminal.custom_bgcolor = gtk.gdk.color_parse(bgcolor)

    def set_fgcolor(self, fgcolor, tab=None):
        """Set the foreground color of `tab' or the current tab to `fgcolor'."""
        if not self.notebook.has_term():
            self.add_tab()
        index = tab or self.notebook.get_current_page()
        for terminal in self.notebook.get_terminals_for_tab(index):
            terminal.custom_fgcolor = gtk.gdk.color_parse(fgcolor)

    def execute_command(self, command, tab=None):
        """Execute the `command' in the `tab'. If tab is None, the
        command will be executed in the currently selected
        tab. Command should end with '\n', otherwise it will be
        appended to the string.
        """
        if not self.notebook.has_term():
            self.add_tab()

        if command[-1] != '\n':
            command += '\n'

        index = self.notebook.get_current_page()
        index = tab or self.notebook.get_current_page()
        for terminal in self.notebook.get_terminals_for_tab(index):
            terminal.feed_child(command)
            break

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

        window_rect = self.window.get_size()
        self.window.resize(window_rect[0], y)
        # self.client.set_int(KEY('/general/window_height'), int(percent))

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
        current_term = self.notebook.get_current_terminal()
        if current_term.get_has_selection():
            current_term.copy_clipboard()
            guake_clipboard = gtk.clipboard_get()
            current_selection = guake_clipboard.wait_for_text().rstrip()

            if len(current_selection) > 20:
                current_selection = current_selection[:17] + "..."

        if current_selection:
            self.get_widget('context_search_on_web').set_label(
                _("Search on Web: '%s'") % current_selection)
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
        if self.forceHide:
            self.forceHide = False
            return

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

        print "DBG Window display"
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
            return

        # Disable the focus_if_open feature
        #  - if doesn't work seamlessly on all system
        #  - self.window.window.get_state doesn't provides us the right information on all
        #    systems, especially on MATE/XFCE
        #
        # if self.client.get_bool(KEY('/general/focus_if_open')):
        #     restore_focus = False
        #     if self.window.window:
        #         state = int(self.window.window.get_state())
        #         if ((state & GDK_WINDOW_STATE_STICKY or
        #                 state & GDK_WINDOW_STATE_WITHDRAWN
        #              )):
        #             restore_focus = True
        #     else:
        #         restore_focus = True
        # if not self.hidden:
        # restore_focus = True
        #     if restore_focus:
        #         print "DBG: Restoring the focus to the terminal"
        #         self.hide()
        #         self.show()
        #         self.window.window.focus()
        #         self.set_terminal_focus()
        #         return

        print "DBG: hiding the terminal"
        self.hide()

    def show(self):
        """Shows the main window and grabs the focus on it.
        """
        self.hidden = False

        # setting window in all desktops
        window_rect = self.set_final_window_rect()
        self.get_widget('window-root').stick()

        # add tab must be called before window.show to avoid a
        # blank screen before adding the tab.
        if not self.notebook.has_term():
            self.add_tab()

        self.window.set_keep_below(False)
        self.window.show_all()

        if self.selected_color is None:
            self.selected_color = getattr(self.window.get_style(), "light")[int(gtk.STATE_SELECTED)]

            # Reapply the tab color to all button in the tab list, since at least one don't have the
            # select color set. This needs to happen AFTER the first show_all, since before the gtk
            # has not loaded the right colors yet.
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

    def hide_from_remote(self):
        """Hides the main window of the terminal and sets the visible
        flag to False.
        """
        print "hide from remote"
        self.forceHide = True
        self.hide()

    def show_from_remote(self):
        """Show the main window of the terminal and sets the visible
        flag to False.
        """
        print "show from remote"
        self.forceHide = True
        self.show()

    def hide(self):
        """Hides the main window of the terminal and sets the visible
        flag to False.
        """
        self.hidden = True
        self.get_widget('window-root').unstick()
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

        # print "height_percents", height_percents
        # print "width_percents", width_percents
        # print "halignment", halignment
        # print "valignment", valignment

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
                unity_icon_size = self.client.get_int(KEY(
                    '/apps/compiz-1/plugins/unityshell/screen0/options/icon_size'))
                if not unity_icon_size:
                    # If not found, it should be because of newer implementation of unity.
                    # Dock is 64 pixel of width on my system, hope this is so on others...
                    unity_dock = 64
                else:
                    unity_dock = unity_icon_size + 17
                print ("correcting window width because of launcher width {} "
                       "(from {} to {})".format(
                           unity_dock, window_rect.width, window_rect.width - unity_dock))

                window_rect.width = window_rect.width - unity_dock

        total_width = window_rect.width
        total_height = window_rect.height

        # print "total_width", total_width
        # print "total_height", total_height

        window_rect.height = window_rect.height * height_percents / 100
        window_rect.width = window_rect.width * width_percents / 100

        # print "window_rect.x", window_rect.x
        # print "window_rect.y", window_rect.y
        # print "window_rect.height", window_rect.height
        # print "window_rect.width", window_rect.width

        if window_rect.width < total_width:
            if halignment == ALIGN_CENTER:
                # print "aligning to center!"
                window_rect.x += (total_width - window_rect.width) / 2
            elif halignment == ALIGN_LEFT:
                # print "aligning to left!"
                window_rect.x += 0
            elif halignment == ALIGN_RIGHT:
                # print "aligning to right!"
                window_rect.x += total_width - window_rect.width
        if window_rect.height < total_height:
            if valignment == ALIGN_BOTTOM:
                window_rect.y += (total_height - window_rect.height)

        self.window.resize(window_rect.width, window_rect.height)
        self.window.move(window_rect.x, window_rect.y)
        # print "Moving/Resizing to: window_rect", window_rect

        return window_rect

    def get_running_fg_processes(self):
        """Get the number of processes for each terminal/tab. The code is taken
        from gnome-terminal.
        """
        return self.notebook.get_running_fg_processes()

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
        for term in self.notebook.iter_terminals():
            term.increase_font_size()
        return True

    def accel_zoom_out(self, *args):
        """Callback to zoom out.
        """
        for term in self.notebook.iter_terminals():
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
        current_term = self.notebook.get_current_terminal()

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
        self.notebook.get_current_terminal().paste_clipboard()
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

    def accel_toggle_hide_on_lose_focus(self, *args):
        """Callback toggle whether the window should hide when it loses
        focus. Called by the accel key.
        """
        # use temporary setting -- don't change conf key
        self.disable_losefocus_hiding = not self.disable_losefocus_hiding
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

        # don't hide on lose focus until the rename is finished
        current_hide_setting = self.disable_losefocus_hiding
        self.disable_losefocus_hiding = True
        response = dialog.run()
        self.disable_losefocus_hiding = current_hide_setting

        if response == gtk.RESPONSE_ACCEPT:
            new_text = entry.get_text()
            self.selected_tab.set_label(new_text)
            # if user sets empty name, consider he wants default behavior.
            setattr(self.selected_tab, 'custom_label_set', bool(new_text))
            # trigger titling handler in case that custom label has been reset
            current_vte = self.notebook.get_current_terminal()
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
            terminals = self.notebook.get_terminals_for_tab(tab_index)
            for current_vte in terminals:
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
        current_vte = self.notebook.get_current_terminal()
        current_vte.emit('window-title-changed')

    def get_current_dir(self):
        """Gets the working directory of the current tab to create a
        new one in the same dir.
        """
        active_terminal = self.notebook.get_current_terminal()
        directory = os.path.expanduser('~')
        if active_terminal:
            cwd = os.readlink("/proc/%d/cwd" % active_terminal.get_pid())
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

        self.notebook.append_tab(box.terminal)

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
        self.tabs.reorder_child(self.tabs.get_children()[old_tab_pos], new_tab_pos)

    def delete_tab(self, pagepos, kill=True):
        """This function will destroy the notebook page, terminal and
        tab widgets and will call the function to kill interpreter
        forked by vte.
        """
        self.tabs.get_children()[pagepos].destroy()
        self.notebook.delete_tab(pagepos, kill=kill)

        if not self.notebook.has_term():
            self.hide()
            # avoiding the delay on next Guake show request
            self.add_tab()
        else:
            self.set_terminal_focus()

    def set_terminal_focus(self):
        """Grabs the focus on the current tab.
        """
        self.notebook.get_current_terminal().grab_focus()

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
            return tab_index
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
        current_term = self.notebook.get_current_terminal()

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

    def set_tab_position(self, *args):
        if self.client.get_bool(KEY('/general/tab_ontop')):
            self.mainframe.reorder_child(self.notebook, 2)
        else:
            self.mainframe.reorder_child(self.notebook, 0)
        self.mainframe.pack_start(self.mainframe, expand=True, fill=True, padding=0)

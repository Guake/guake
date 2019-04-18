# -*- coding: utf-8; -*-
"""
Copyright (C) 2018 Mario Aichinger <aichingm@gmail.com>
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
import datetime
import logging
import os
import platform
import subprocess
import time

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gdk
from gi.repository import GdkX11
from gi.repository import Gtk
from guake.globals import ALIGN_BOTTOM
from guake.globals import ALIGN_CENTER
from guake.globals import ALIGN_LEFT
from guake.globals import ALIGN_RIGHT
from guake.globals import ALIGN_TOP
from guake.globals import ALWAYS_ON_PRIMARY

log = logging.getLogger(__name__)


def get_server_time(widget):
    try:
        return GdkX11.x11_get_server_time(widget.get_window())
    except (TypeError, AttributeError):
        # Issue: https://github.com/Guake/guake/issues/1071
        # Wayland does not seem to like `x11_get_server_time`.
        # Use local timestamp instead
        ts = time.time()
        return ts


# Decorator for save-tabs-when-changed
def save_tabs_when_changed(func):
    """Decorator for save-tabs-when-changed
    """

    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        log.debug("mom, I've been called: %s %s", func.__name__, func)

        # Find me the Guake!
        clsname = args[0].__class__.__name__
        g = None
        if clsname == 'Guake':
            g = args[0]
        elif getattr(args[0], 'get_guake', None):
            g = args[0].get_guake()
        elif getattr(args[0], 'get_notebook', None):
            g = args[0].get_notebook().guake
        elif getattr(args[0], 'guake', None):
            g = args[0].guake
        elif getattr(args[0], 'notebook', None):
            g = args[0].notebook.guake

        # Tada!
        if g and g.settings.general.get_boolean('save-tabs-when-changed'):
            g.save_tabs()

    return wrapper


def save_preferences(filename):
    # XXX: Hardcode?
    prefs = subprocess.check_output(['dconf', 'dump', '/apps/guake/'])
    with open(filename, 'wb') as f:
        f.write(prefs)


def restore_preferences(filename):
    # XXX: Hardcode?
    with open(filename, 'rb') as f:
        prefs = f.read()
    p = subprocess.Popen(['dconf', 'load', '/apps/guake/'], stdin=subprocess.PIPE)
    p.communicate(input=prefs)


class TabNameUtils():

    @classmethod
    def shorten(cls, text, settings):
        use_vte_titles = settings.general.get_boolean('use-vte-titles')
        if not use_vte_titles:
            return text
        max_name_length = settings.general.get_int("max-tab-name-length")
        if max_name_length != 0 and len(text) > max_name_length:
            text = "..." + text[-max_name_length:]
        return text


class HidePrevention():

    def __init__(self, window):
        """Create a new HidePrevention object like `HidePrevention(window)`
        """
        if not isinstance(window, Gtk.Window):
            raise ValueError("window must be of type Gtk.Window, not of type %s" % type(window))
        self.window = window

    def may_hide(self):
        """returns True if the window is allowed to hide and
        False if `prevent()` is called from some where
        """
        return getattr(self.window, 'can_hide', True)

    def prevent(self):
        """sets a flag on the window object which indicates to
        may_hide that the window is NOT allowed to be hidden.
        """
        setattr(self.window, 'can_hide', False)

    def allow(self):
        """sets the flag so that it indicates to may_hide that the window is allowed to be hidden
        """
        setattr(self.window, 'can_hide', True)


class FullscreenManager():

    def __init__(self, settings, window):
        self.settings = settings
        self.window = window
        self.is_in_fullscreen = False

    def is_fullscreen(self):
        return getattr(self.window, 'is_fullscreen', False)

    def fullscreen(self):
        self.window.fullscreen()
        setattr(self.window, 'is_fullscreen', True)

    def unfullscreen(self):
        setattr(self.window, 'is_fullscreen', False)
        self.window.unfullscreen()
        # FIX to unfullscreen after show, fullscreen, hide, unfullscreen
        # (unfullscreen breaks/does not shrink window size)
        RectCalculator.set_final_window_rect(self.settings, self.window)

    def toggle(self):
        if self.is_fullscreen():
            self.unfullscreen()
        else:
            self.fullscreen()


class RectCalculator():

    @classmethod
    def set_final_window_rect(cls, settings, window):
        """Sets the final size and location of the main window of guake. The height
        is the window_height property, width is window_width and the
        horizontal alignment is given by window_alignment.
        """
        # fetch settings
        height_percents = settings.general.get_int('window-height')

        width_percents = settings.general.get_int('window-width')
        halignment = settings.general.get_int('window-halignment')
        valignment = settings.general.get_int('window-valignment')

        vdisplacement = settings.general.get_int('window-vertical-displacement')
        hdisplacement = settings.general.get_int('window-horizontal-displacement')

        log.debug("set_final_window_rect")
        log.debug("  height_percents = %s", height_percents)
        log.debug("  width_percents = %s", width_percents)
        log.debug("  halignment = %s", halignment)
        log.debug("  valignment = %s", valignment)
        log.debug("  vdisplacement = %s", vdisplacement)
        log.debug("  hdisplacement = %s", hdisplacement)

        # get the rectangle just from the destination monitor
        screen = window.get_screen()
        monitor = cls.get_final_window_monitor(settings, window)
        window_rect = screen.get_monitor_geometry(monitor)
        log.debug("Current monitor geometry")
        log.debug("  window_rect.x: %s", window_rect.x)
        log.debug("  window_rect.y: %s", window_rect.y)
        log.debug("  window_rect.height: %s", window_rect.height)
        log.debug("  window_rect.width: %s", window_rect.width)
        log.debug("is unity: %s", cls.is_using_unity(settings, window))

        # TODO PORT remove this UNITY is DEAD
        if cls.is_using_unity(settings, window):

            # For Ubuntu 12.10 and above, try to use dconf:
            # see if unity dock is hidden => unity_hide
            # and the width of unity dock => unity_dock
            # and the position of the unity dock. => unity_pos
            # found = False
            unity_hide = 0
            unity_dock = 0
            unity_pos = "Left"
            # float() conversion might mess things up. Add 0.01 so the comparison will always be
            # valid, even in case of float("10.10") = 10.099999999999999
            if float(platform.linux_distribution()[1]) + 0.01 >= 12.10:
                try:
                    unity_hide = int(
                        subprocess.check_output([
                            '/usr/bin/dconf', 'read',
                            '/org/compiz/profiles/unity/plugins/unityshell/launcher-hide-mode'
                        ])
                    )
                    unity_dock = int(
                        subprocess.check_output([
                            '/usr/bin/dconf', 'read',
                            '/org/compiz/profiles/unity/plugins/unityshell/icon-size'
                        ]) or "48"
                    )
                    unity_pos = subprocess.check_output([
                        '/usr/bin/dconf', 'read', '/com/canonical/unity/launcher/launcher-position'
                    ]) or "Left"
                    # found = True
                except Exception as e:
                    # in case of error, just ignore it, 'found' will not be set to True and so
                    # we execute the fallback
                    pass
            # FIXME: remove self.client dependency
            # if not found:
            #     # Fallback: try to bet from gconf
            #     unity_hide = self.client.get_int(
            #         KEY('/apps/compiz-1/plugins/unityshell/screen0/options/launcher_hide_mode')
            #     )
            #     unity_icon_size = self.client.get_int(
            #         KEY('/apps/compiz-1/plugins/unityshell/screen0/options/icon_size')
            #     )
            #     unity_dock = unity_icon_size + 17

            # launcher_hide_mode = 1 => autohide
            # only adjust guake window width if Unity dock is positioned "Left" or "Right"
            if unity_hide != 1 and unity_pos not in ("Left", "Right"):
                log.debug(
                    "correcting window width because of launcher position %s "
                    "and width %s (from %s to %s)", unity_pos, unity_dock, window_rect.width,
                    window_rect.width - unity_dock
                )

                window_rect.width = window_rect.width - unity_dock

        total_width = window_rect.width
        total_height = window_rect.height

        log.debug("Correcteed monitor size:")
        log.debug("  total_width: %s", total_width)
        log.debug("  total_height: %s", total_height)

        window_rect.height = int(float(window_rect.height) * float(height_percents) / 100.0)
        window_rect.width = int(float(window_rect.width) * float(width_percents) / 100.0)

        if window_rect.width < total_width:
            if halignment == ALIGN_CENTER:
                # log.debug("aligning to center!")
                window_rect.x += (total_width - window_rect.width) / 2
            elif halignment == ALIGN_LEFT:
                # log.debug("aligning to left!")
                window_rect.x += 0 + hdisplacement
            elif halignment == ALIGN_RIGHT:
                # log.debug("aligning to right!")
                window_rect.x += total_width - window_rect.width - hdisplacement
        if window_rect.height < total_height:
            if valignment == ALIGN_BOTTOM:
                window_rect.y += (total_height - window_rect.height)

        if valignment == ALIGN_TOP:
            window_rect.y += vdisplacement
        elif valignment == ALIGN_BOTTOM:
            window_rect.y -= vdisplacement

        if width_percents == 100 and height_percents == 100:
            log.debug("MAXIMIZING MAIN WINDOW")
            window.maximize()
        elif not FullscreenManager(settings, window).is_fullscreen():
            log.debug("RESIZING MAIN WINDOW TO THE FOLLOWING VALUES:")
            window.unmaximize()
            log.debug("  window_rect.x: %s", window_rect.x)
            log.debug("  window_rect.y: %s", window_rect.y)
            log.debug("  window_rect.height: %s", window_rect.height)
            log.debug("  window_rect.width: %s", window_rect.width)
            # Note: move_resize is only on GTK3
            window.resize(window_rect.width, window_rect.height)
            window.move(window_rect.x, window_rect.y)
            window.move(window_rect.x, window_rect.y)
            log.debug("Updated window position: %r", window.get_position())

        return window_rect

    @classmethod
    def get_final_window_monitor(cls, settings, window):
        """Gets the final screen number for the main window of guake.
        """

        screen = window.get_screen()

        # fetch settings
        use_mouse = settings.general.get_boolean('mouse-display')
        dest_screen = settings.general.get_int('display-n')

        if use_mouse:

            # TODO PORT get_pointer is deprecated
            # https://developer.gnome.org/gtk3/stable/GtkWidget.html#gtk-widget-get-pointer
            win, x, y, _ = screen.get_root_window().get_pointer()
            dest_screen = screen.get_monitor_at_point(x, y)

        # If Guake is configured to use a screen that is not currently attached,
        # default to 'primary display' option.
        n_screens = screen.get_n_monitors()
        if dest_screen > n_screens - 1:
            settings.general.set_boolean('mouse-display', False)
            settings.general.set_int('display-n', dest_screen)
            dest_screen = screen.get_primary_monitor()

        # Use primary display if configured
        if dest_screen == ALWAYS_ON_PRIMARY:
            dest_screen = screen.get_primary_monitor()

        return dest_screen

    # TODO PORT remove this UNITY is DEAD
    @classmethod
    def is_using_unity(cls, settings, window):
        linux_distrib = platform.linux_distribution()
        if linux_distrib[0].lower() != "ubuntu":
            return False

        # http://askubuntu.com/questions/70296/is-there-an-environment-variable-that-is-set-for-unity
        if float(linux_distrib[1]) - 0.01 < 11.10:
            if os.environ.get('DESKTOP_SESSION', '').lower() == "gnome".lower():
                return True
        else:
            if os.environ.get('XDG_CURRENT_DESKTOP', '').lower() == "unity".lower():
                return True
        return False

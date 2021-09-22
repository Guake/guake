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
import enum
import logging
import subprocess
import time
import os

import cairo

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gdk
from gi.repository import Gtk
from guake.globals import ALIGN_BOTTOM
from guake.globals import ALIGN_CENTER
from guake.globals import ALIGN_LEFT
from guake.globals import ALIGN_RIGHT
from guake.globals import ALIGN_TOP
from guake.globals import ALWAYS_ON_PRIMARY

try:
    from gi.repository import GdkX11
except ImportError:
    GdkX11 = False

log = logging.getLogger(__name__)


def gdk_is_x11_display(instance):
    if GdkX11:
        return isinstance(instance, GdkX11.X11Display)
    return False


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
    """Decorator for save-tabs-when-changed"""

    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        log.debug("mom, I've been called: %s %s", func.__name__, func)

        # Find me the Guake!
        clsname = args[0].__class__.__name__
        g = None
        if clsname == "Guake":
            g = args[0]
        elif getattr(args[0], "get_guake", None):
            g = args[0].get_guake()
        elif getattr(args[0], "get_notebook", None):
            g = args[0].get_notebook().guake
        elif getattr(args[0], "guake", None):
            g = args[0].guake
        elif getattr(args[0], "notebook", None):
            g = args[0].notebook.guake

        # Tada!
        if g and g.settings.general.get_boolean("save-tabs-when-changed"):
            g.save_tabs()

    return wrapper


def save_preferences(filename):
    # XXX: Hardcode?
    prefs = subprocess.check_output(["dconf", "dump", "/apps/guake/"])
    with open(filename, "wb") as f:
        f.write(prefs)


def restore_preferences(filename):
    # XXX: Hardcode?
    with open(filename, "rb") as f:
        prefs = f.read()
    with subprocess.Popen(["dconf", "load", "/apps/guake/"], stdin=subprocess.PIPE) as p:
        p.communicate(input=prefs)


class TabNameUtils:
    @classmethod
    def shorten(cls, text, settings):
        use_vte_titles = settings.general.get_boolean("use-vte-titles")
        if not use_vte_titles:
            return text
        max_name_length = settings.general.get_int("max-tab-name-length")
        if max_name_length != 0 and len(text) > max_name_length:
            text = "..." + text[-max_name_length:]
        return text


class HidePrevention:
    def __init__(self, window):
        """Create a new HidePrevention object like `HidePrevention(window)`"""
        if not isinstance(window, Gtk.Window):
            raise ValueError(f"window must be of type Gtk.Window, not of type {type(window)}")
        self.window = window

    def may_hide(self):
        """returns True if the window is allowed to hide and
        False if `prevent()` is called from some where
        """
        return getattr(self.window, "can_hide", True)

    def prevent(self):
        """sets a flag on the window object which indicates to
        may_hide that the window is NOT allowed to be hidden.
        """
        setattr(self.window, "can_hide", False)

    def allow(self):
        """sets the flag so that it indicates to may_hide that the window is allowed to be hidden"""
        setattr(self.window, "can_hide", True)


class FullscreenManager:
    FULLSCREEN_ATTR = "is_fullscreen"

    def __init__(self, settings, window, guake=None):
        self.settings = settings
        self.window = window
        self.guake = guake
        self.window_state = None

    def is_fullscreen(self):
        return getattr(self.window, self.FULLSCREEN_ATTR, False)

    def set_window_state(self, window_state):
        self.window_state = window_state
        setattr(
            self.window,
            self.FULLSCREEN_ATTR,
            bool(window_state & Gdk.WindowState.FULLSCREEN),
        )

        if not window_state & Gdk.WindowState.WITHDRAWN:
            if self.is_fullscreen():
                self.fullscreen()
            elif window_state & Gdk.WindowState.FOCUSED and self.guake.hidden:
                self.unfullscreen()

    def fullscreen(self):
        self.window.fullscreen()
        setattr(self.window, self.FULLSCREEN_ATTR, True)
        self.toggle_fullscreen_hide_tabbar()

    def unfullscreen(self):
        self.window.unfullscreen()
        setattr(self.window, self.FULLSCREEN_ATTR, False)
        self.toggle_fullscreen_hide_tabbar()

        # FIX to unfullscreen after show, fullscreen, hide, unfullscreen
        # (unfullscreen breaks/does not shrink window size)
        RectCalculator.set_final_window_rect(self.settings, self.window)

    def toggle(self):
        if self.is_fullscreen():
            self.unfullscreen()
        else:
            self.fullscreen()

    def toggle_fullscreen_hide_tabbar(self):
        if self.is_fullscreen():
            if (
                self.settings.general.get_boolean("fullscreen-hide-tabbar")
                and self.guake
                and self.guake.notebook_manager
            ):
                self.guake.notebook_manager.set_notebooks_tabbar_visible(False)
        else:
            if self.guake and self.guake.notebook_manager:
                v = self.settings.general.get_boolean("window-tabbar")
                self.guake.notebook_manager.set_notebooks_tabbar_visible(v)


class RectCalculator:
    @classmethod
    def set_final_window_rect(cls, settings, window):
        """Sets the final size and location of the main window of guake. The height
        is the window_height property, width is window_width and the
        horizontal alignment is given by window_alignment.
        """
        # fetch settings
        height_percents = settings.general.get_int("window-height")
        width_percents = settings.general.get_int("window-width")
        halignment = settings.general.get_int("window-halignment")
        valignment = settings.general.get_int("window-valignment")
        vdisplacement = settings.general.get_int("window-vertical-displacement")
        hdisplacement = settings.general.get_int("window-horizontal-displacement")

        log.debug("set_final_window_rect")
        log.debug("  height_percents = %s", height_percents)
        log.debug("  width_percents = %s", width_percents)
        log.debug("  halignment = %s", halignment)
        log.debug("  valignment = %s", valignment)
        log.debug("  hdisplacement = %s", hdisplacement)
        log.debug("  vdisplacement = %s", vdisplacement)

        # get the rectangle just from the destination monitor
        screen = window.get_screen()
        monitor = cls.get_final_window_monitor(settings, window)
        window_rect = screen.get_monitor_geometry(monitor)
        log.debug("Current monitor geometry")
        log.debug("  window_rect.x: %s", window_rect.x)
        log.debug("  window_rect.y: %s", window_rect.y)
        log.debug("  window_rect.height: %s", window_rect.height)
        log.debug("  window_rect.width: %s", window_rect.width)

        total_height = window_rect.height
        total_width = window_rect.width

        if halignment == ALIGN_CENTER:
            log.debug("aligning to center!")
            window_rect.width = int(float(total_width) * float(width_percents) / 100.0)
            window_rect.x += (total_width - window_rect.width) / 2
        elif halignment == ALIGN_LEFT:
            log.debug("aligning to left!")
            window_rect.width = int(
                float(total_width - hdisplacement) * float(width_percents) / 100.0
            )
            window_rect.x += hdisplacement
        elif halignment == ALIGN_RIGHT:
            log.debug("aligning to right!")
            window_rect.width = int(
                float(total_width - hdisplacement) * float(width_percents) / 100.0
            )
            window_rect.x += total_width - window_rect.width - hdisplacement

        window_rect.height = int(float(total_height) * float(height_percents) / 100.0)
        if valignment == ALIGN_TOP:
            window_rect.y += vdisplacement
        elif valignment == ALIGN_BOTTOM:
            window_rect.y += total_height - window_rect.height - vdisplacement

        if width_percents == 100 and height_percents == 100:
            log.debug("MAXIMIZING MAIN WINDOW")
            window.move(window_rect.x, window_rect.y)
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
            log.debug("Updated window position: %r", window.get_position())

        return window_rect

    @classmethod
    def get_final_window_monitor(cls, settings, window):
        """Gets the final screen number for the main window of guake."""

        screen = window.get_screen()

        # fetch settings
        use_mouse = settings.general.get_boolean("mouse-display")
        dest_screen = settings.general.get_int("display-n")

        if use_mouse:

            # TODO PORT get_pointer is deprecated
            # https://developer.gnome.org/gtk3/stable/GtkWidget.html#gtk-widget-get-pointer
            win, x, y, _ = screen.get_root_window().get_pointer()
            dest_screen = screen.get_monitor_at_point(x, y)

        # If Guake is configured to use a screen that is not currently attached,
        # default to 'primary display' option.
        n_screens = screen.get_n_monitors()
        if dest_screen > n_screens - 1:
            settings.general.set_boolean("mouse-display", False)
            settings.general.set_int("display-n", dest_screen)
            dest_screen = screen.get_primary_monitor()

        # Use primary display if configured
        if dest_screen == ALWAYS_ON_PRIMARY:
            dest_screen = screen.get_primary_monitor()

        return dest_screen


class ImageLayoutMode(enum.IntEnum):
    SCALE = 0
    TILE = 1
    CENTER = 2
    STRETCH = 3


class BackgroundImageManager:
    def __init__(self, window, filename=None, layout_mode=ImageLayoutMode.SCALE):
        self.window = window
        self.filename = ""
        self.bg_surface = self.load_from_file(filename) if filename else None
        self.target_surface = None
        self.target_info = (-1, -1, -1)  # (width, height, model)
        self._layout_mode = layout_mode

    @property
    def layout_mode(self):
        return self._layout_mode

    @layout_mode.setter
    def layout_mode(self, mode):
        mode = ImageLayoutMode(mode)
        if mode not in ImageLayoutMode:
            raise ValueError("Unknown layout mode")
        self._layout_mode = mode
        self.window.queue_draw()

    def load_from_file(self, filename):
        if not filename:
            # Clear the background image
            self.bg_surface = None
            self.window.queue_draw()
            return

        if not os.path.exists(filename):
            raise FileNotFoundError(f"Background file not found: {filename}")

        if self.filename:
            # Cached rendered surface
            if os.path.samefile(self.filename, filename):
                return self.bg_surface

        self.filename = filename
        img = Gtk.Image.new_from_file(filename)
        pixbuf = img.get_pixbuf()
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, pixbuf.get_width(), pixbuf.get_height())
        cr = cairo.Context(surface)
        Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()

        self.bg_surface = surface
        self.target_info = (-1, -1, -1)
        self.window.queue_draw()
        return surface

    def render_target(self, width, height, mode, scale_mode=cairo.FILTER_BILINEAR):
        """Paint bacground image to the specific size target surface with different layout mode"""
        if not self.bg_surface:
            return None

        # Check if target surface has been rendered
        if self.target_info == (width, height, mode):
            return self.target_surface

        # Render new target
        self.target_info = (width, height, mode)
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        cr = cairo.Context(surface)
        cr.set_operator(cairo.OPERATOR_SOURCE)

        xscale = width / self.bg_surface.get_width()
        yscale = height / self.bg_surface.get_height()
        if mode == ImageLayoutMode.SCALE:
            ratio = max(xscale, yscale)
            xoffset = (width - (self.bg_surface.get_width() * ratio)) / 2.0
            yoffset = (height - (self.bg_surface.get_height() * ratio)) / 2.0
            cr.translate(xoffset, yoffset)
            cr.scale(ratio, ratio)
            cr.set_source_surface(self.bg_surface, 0, 0)
            cr.get_source().set_filter(scale_mode)
        elif mode == ImageLayoutMode.TILE:
            cr.set_source_surface(self.bg_surface, 0, 0)
            cr.get_source().set_extend(cairo.EXTEND_REPEAT)
        elif mode == ImageLayoutMode.CENTER:
            x = (width - self.bg_surface.get_width()) / 2.0
            y = (height - self.bg_surface.get_height()) / 2.0
            cr.translate(x, y)
            cr.set_source_surface(self.bg_surface, 0, 0)
        elif mode == ImageLayoutMode.STRETCH:
            cr.scale(xscale, yscale)
            cr.set_source_surface(self.bg_surface, 0, 0)
            cr.get_source().set_filter(scale_mode)
        cr.paint()

        self.target_surface = surface
        return surface

    def draw(self, widget, cr):
        if not self.bg_surface:
            return

        # Step 1. Get target surface
        #         (paint background image into widget size surface by layout mode)
        surface = self.render_target(
            widget.get_allocated_width(), widget.get_allocated_height(), self.layout_mode
        )

        cr.save()
        # Step 2. Paint target surface to context (in our case, the RootTerminalBox)
        #
        #         At this step, RootTerminalBox will be painted to our background image,
        #         and all the draw done by VTE has been overlapped.
        #
        cr.set_source_surface(surface, 0, 0)
        cr.paint()

        # Step 3. Re-paint child draw result to a new surface
        #
        #         We need to re-paint what we overlapped in previous step,
        #         so we paint our child (again, in lifecycle view) into a similar surface.
        #
        child = widget.get_child()
        child_surface = cr.get_target().create_similar(
            cairo.CONTENT_COLOR_ALPHA, child.get_allocated_width(), child.get_allocated_height()
        )
        child_cr = cairo.Context(child_surface)

        # Re-paint child draw into child context (which using child_surface as target)
        widget.propagate_draw(child, child_cr)

        # Step 3.1 Re-paint search revealer
        child_sr_surface = None
        if getattr(widget, "search_revealer", None):
            child_sr = widget.search_revealer
            child_sr_surface = cr.get_target().create_similar(
                cairo.CONTENT_COLOR_ALPHA,
                child_sr.get_allocated_width(),
                child_sr.get_allocated_height(),
            )
            child_sr_cr = cairo.Context(child_surface)

            # Re-paint child draw into child context (which using child_surface as target)
            widget.propagate_draw(child_sr, child_sr_cr)

        # Step 4. Paint child surface into our context (RootTerminalBox)
        #
        #         Before this step, we have two important context/surface
        #             1. cr       / RootTerminalBox
        #             2. child_cr / child (RootTerminalBox's child)
        #         And current context have these draw:
        #             1. cr       - background image
        #             2. child_cr - child re-paint (split terminal, VTE draw ...etc)
        #         In this step, we are going to paint child_cr result back to cr,
        #         so in the end, we will get background image + other child stuff
        #
        # DEBUG: If you don't believe, use cairo.Surface.wrte_to_png(filename) to check what is
        #        inside the surface.
        #
        cr.set_source_surface(child_surface, 0, 0)
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.paint()

        # Paint search revealer
        if child_sr_surface:
            cr.set_source_surface(child_sr_surface, 0, 0)
            cr.set_operator(cairo.OPERATOR_OVER)
            cr.paint()

        cr.restore()

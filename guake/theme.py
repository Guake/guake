import inspect
import itertools
import logging
import os

from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib
from gi.repository import Gdk
from gi.repository import Gtk
from textwrap import dedent

from guake.paths import GUAKE_THEME_DIR

# Create a custom logger
logger = logging.getLogger(__name__)

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler(os.path.expandvars("$HOME/.config/guake/") + "guake.log")
c_handler.setLevel(logging.WARNING)
f_handler.setLevel(logging.ERROR)

# Create formatters and add it to handlers
c_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
f_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)


def _line_():
    """Returns the current line number in our program."""
    return str(inspect.currentframe().f_back.f_lineno)


def _file_():
    return str(__file__)


# Reference:
# https://gitlab.gnome.org/GNOME/gnome-tweaks/blob/master/gtweak/utils.py (GPL)


def get_resource_dirs(resource):
    """Returns a list of all known resource dirs for a given resource.

    :param str resource:
        Name of the resource (e.g. "themes")
    :return:
        A list of resource dirs
    """
    dirs = [
        os.path.join(dir, resource)
        for dir in itertools.chain(
            GLib.get_system_data_dirs(), GUAKE_THEME_DIR, GLib.get_user_data_dir()
        )
    ]
    dirs += [os.path.join(os.path.expanduser("~"), f".{resource}")]

    return [Path(dir) for dir in dirs if os.path.isdir(dir)]


def list_all_themes():
    return sorted(
        {
            x.name
            for theme_dir in get_resource_dirs("themes")
            for x in theme_dir.iterdir()
            if x.is_dir()
        }
    )


def select_gtk_theme(settings):
    gtk_settings = Gtk.Settings.get_default()
    if settings.general.get_boolean("gtk-use-system-default-theme"):
        logger.debug("%s:%s  Using system default theme", _file_(), _line_())
        gtk_settings.reset_property("gtk-theme-name")
        gtk_settings.set_property("gtk-application-prefer-dark-theme", False)
        return

    gtk_theme_name = settings.general.get_string("gtk-theme-name")
    logger.debug("%s:%s  Wanted GTK theme: %r", _file_(), _line_(), gtk_theme_name)
    gtk_settings.set_property("gtk-theme-name", gtk_theme_name)

    prefer_dark_theme = settings.general.get_boolean("gtk-prefer-dark-theme")
    logger.debug("%s:%s  Prefer dark theme: %r", _file_(), _line_(), prefer_dark_theme)
    gtk_settings.set_property("gtk-application-prefer-dark-theme", prefer_dark_theme)


def get_gtk_theme(settings):
    gtk_theme_name = settings.general.get_string("gtk-theme-name")
    prefer_dark_theme = settings.general.get_boolean("gtk-prefer-dark-theme")
    return (gtk_theme_name, "dark" if prefer_dark_theme else None)


def patch_gtk_theme(style_context, settings):
    theme_name, variant = get_gtk_theme(settings)

    def rgba_to_hex(color):
        return f"#{''.join(f'{int(i*255):02x}' for i in (color.red, color.green, color.blue))}"

    # for n in [
    #     "inverted_bg_color",
    #     "inverted_fg_color",
    #     "selected_bg_color",
    #     "selected_fg_color",
    #     "theme_inverted_bg_color",
    #     "theme_inverted_fg_color",
    #     "theme_selected_bg_color",
    #     "theme_selected_fg_color",
    #     ]:
    #     s = style_context.lookup_color(n)
    #     print(n, s, rgba_to_hex(s[1]))
    selected_fg_color = rgba_to_hex(style_context.lookup_color("theme_selected_fg_color")[1])
    selected_bg_color = rgba_to_hex(style_context.lookup_color("theme_selected_bg_color")[1])
    logger.debug(
        "%s:%s Patching theme '%s' (prefer dark = '%r'), overriding tab 'checked' state': "
        "foreground: %r, background: %r",
        _file_(),
        _line_(),
        theme_name,
        ("yes" if variant == "dark" else "no"),
        selected_fg_color,
        selected_bg_color,
    )
    css_data = dedent(
        f"""
        .custom_tab:checked {{
            color: {selected_fg_color};
            background: {selected_bg_color};
        }}
        """
    ).encode()
    style_provider = Gtk.CssProvider()
    style_provider.load_from_data(css_data)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        style_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )

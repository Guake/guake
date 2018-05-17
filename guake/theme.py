import itertools
import logging
import os

from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib
from gi.repository import Gtk

from guake.paths import GUAKE_THEME_DIR

log = logging.getLogger(__name__)

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
        os.path.join(dir, resource) for dir in
        itertools.chain(GLib.get_system_data_dirs(), GUAKE_THEME_DIR, GLib.get_user_data_dir())
    ]
    dirs += [os.path.join(os.path.expanduser("~"), ".{}".format(resource))]

    return [Path(dir) for dir in dirs if os.path.isdir(dir)]


def list_all_themes():
    return sorted(
        set(
            x.name for theme_dir in get_resource_dirs("themes") for x in theme_dir.iterdir()
            if x.is_dir()
        )
    )


def select_gtk_theme(settings):
    gtk_theme_name = settings.general.get_string('gtk-theme-name')
    log.debug("Wanted GTK theme: %r", gtk_theme_name)
    gtk_settings = Gtk.Settings.get_default()
    gtk_settings.set_property("gtk-theme-name", gtk_theme_name)

    prefer_dark_theme = settings.general.get_boolean('gtk-prefer-dark-theme')
    log.debug("Prefer dark theme: %r", prefer_dark_theme)
    gtk_settings.set_property("gtk-application-prefer-dark-theme", prefer_dark_theme)


def get_gtk_theme(settings):
    gtk_theme_name = settings.general.get_string('gtk-theme-name')
    prefer_dark_theme = settings.general.get_boolean('gtk-prefer-dark-theme')
    return (gtk_theme_name, "dark" if prefer_dark_theme else None)

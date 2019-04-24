# -*- coding: utf-8 -*-

import os

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gdk
from gi.repository import GdkX11
from gi.repository import Gtk

from guake import guake_version
from guake import gtk_version
from guake import vte_version
from guake import vte_runtime_version


def horizonal_line():
    print('-' * 50)


def populate_display(display):
    screen = display.get_default_screen()
    print('Display: {}'.format(display.get_name()))
    print()
    # pylint: disable=R1719
    print('RGBA visual: {}'.format(True if screen.get_rgba_visual() else False))
    print()
    print('Composited: {}'.format(screen.is_composited()))
    print()

    n_monitors = display.get_n_monitors()
    for i in range(n_monitors):
        monitor = display.get_monitor(i)
        manufacturer = monitor.get_manufacturer()
        model = monitor.get_model()
        v = '%s%s%s' % (manufacturer if manufacturer else '',
                        ' ' if manufacturer or model else '',
                        model if model else '')
        print('* Monitor: {} - {}'.format(i, v))

        # Geometry
        rect = monitor.get_geometry()
        scale = monitor.get_scale_factor()
        v = '%d x %d%s at %d, %d' % (rect.width, rect.height,
                                     ' % 2' if scale == 2 else '',
                                     rect.x, rect.y)
        print('    * Geometry:\t\t{}'.format(v))

        # Size
        v = '%d x %d mm²' % (monitor.get_width_mm(), monitor.get_height_mm())
        print('    * Size:\t\t{}'.format(v))

        # Primary
        print('    * Primary:\t\t{}'.format(monitor.is_primary()))

        # Refresh rate
        if monitor.get_refresh_rate():
            v = '%.2f Hz' % (0.001 * monitor.get_refresh_rate())
        else:
            v = 'unknown'
        print('    * Refresh rate:\t{}'.format(v))

        # Subpixel layout
        print('    * Subpixel layout:\t{}'.format(monitor.get_subpixel_layout().value_nick))


def get_version():
    display = Gdk.Display.get_default()

    print('Guake Version:\t\t{}'.format(guake_version()))
    print()
    print('Vte Version:\t\t{}'.format(vte_version()))
    print()
    print('Vte Runtime Version:\t{}'.format(vte_runtime_version()))
    print()
    horizonal_line()
    print('GTK+ Version:\t\t{}'.format(gtk_version()))
    print()
    print('GDK Backend:\t\t{}'.format(str(display).split(' ')[0][1:]))
    print()
    horizonal_line()


def get_desktop_session():
    print('Desktop Session: {}'.format(os.environ.get('DESKTOP_SESSION')))
    print()
    horizonal_line()


def get_display():
    display = Gdk.Display.get_default()
    populate_display(display)


def print_support():
    print("<details><summary>$ guake --support</summary>")
    print()
    get_version()
    get_desktop_session()
    get_display()

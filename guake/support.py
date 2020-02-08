import os

import gi
from gi.repository import Gdk, GdkX11, Gtk

from guake import gtk_version, guake_version, vte_runtime_version, vte_version

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')




def horizonal_line():
    print('-' * 50)


def populate_display(display):
    screen = display.get_default_screen()
    print(f'Display: {display.get_name()}')
    print()
    # pylint: disable=R1719
    print(f'RGBA visual: {True if screen.get_rgba_visual() else False}')
    print()
    print(f'Composited: {screen.is_composited()}')
    print()

    n_monitors = display.get_n_monitors()
    for i in range(n_monitors):
        monitor = display.get_monitor(i)
        manufacturer = monitor.get_manufacturer()
        model = monitor.get_model()
        v = '{}{}{}'.format(
            manufacturer if manufacturer else '', ' ' if manufacturer or model else '',
            model if model else ''
        )
        print(f'* Monitor: {i} - {v}')

        # Geometry
        rect = monitor.get_geometry()
        scale = monitor.get_scale_factor()
        v = '%d x %d%s at %d, %d' % (
            rect.width, rect.height, ' % 2' if scale == 2 else '', rect.x, rect.y
        )
        print(f'    * Geometry:\t\t{v}')

        # Size
        v = f'{monitor.get_width_mm():d} x {monitor.get_height_mm():d} mm²'
        print(f'    * Size:\t\t{v}')

        # Primary
        print(f'    * Primary:\t\t{monitor.is_primary()}')

        # Refresh rate
        if monitor.get_refresh_rate():
            v = '%.2f Hz' % (0.001 * monitor.get_refresh_rate())
        else:
            v = 'unknown'
        print(f'    * Refresh rate:\t{v}')

        # Subpixel layout
        print(f'    * Subpixel layout:\t{monitor.get_subpixel_layout().value_nick}')


def get_version():
    display = Gdk.Display.get_default()

    print(f'Guake Version:\t\t{guake_version()}')
    print()
    print(f'Vte Version:\t\t{vte_version()}')
    print()
    print(f'Vte Runtime Version:\t{vte_runtime_version()}')
    print()
    horizonal_line()
    print(f'GTK+ Version:\t\t{gtk_version()}')
    print()
    print(f"GDK Backend:\t\t{str(display).split(' ')[0][1:]}")
    print()
    horizonal_line()


def get_desktop_session():
    print(f"Desktop Session: {os.environ.get('DESKTOP_SESSION')}")
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

#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import gtk


def format_color_string(color):
    return "%s %s %s" % (color.red / 256, color.green / 256, color.blue / 256)


def print_hex_color(color):
    return "#" + hex(color.red / 256)[2:] + hex(color.green / 256)[2:] + hex(color.blue / 256)[2:]


def format_color_key(key, color):
    return "\"%s\"=\"%s\" (%s)\n" % (key, format_color_string(color), print_hex_color(color))

invisible1 = gtk.Invisible()
style1 = invisible1.style

button1 = gtk.Button()
buttonstyle = button1.style

scroll1 = gtk.VScrollbar()
scrollbarstyle = scroll1.style

menu1 = gtk.Menu()
menuitem1 = gtk.MenuItem()
menu1.add(menuitem1)
menustyle = menuitem1.style

format = ""
format += format_color_key('Scrollbar', scrollbarstyle.bg[gtk.STATE_NORMAL])
format += format_color_key('Background', style1.bg[gtk.STATE_NORMAL])
format += format_color_key('ActiveTitle', menustyle.bg[gtk.STATE_PRELIGHT])
format += format_color_key('InactiveTitle', menustyle.bg[gtk.STATE_PRELIGHT])
format += format_color_key('Menu', menustyle.bg[gtk.STATE_NORMAL])
format += format_color_key('Window', style1.bg[gtk.STATE_NORMAL])
format += format_color_key('WindowFrame', style1.fg[gtk.STATE_INSENSITIVE])
format += format_color_key('MenuText', style1.fg[gtk.STATE_NORMAL])
format += format_color_key('WindowText', style1.fg[gtk.STATE_NORMAL])
format += format_color_key('TitleText', style1.fg[gtk.STATE_NORMAL])
format += format_color_key('ActiveBorder', menustyle.bg[gtk.STATE_PRELIGHT])
format += format_color_key('InactiveBorder', menustyle.bg[gtk.STATE_NORMAL])
format += format_color_key('AppWorkSpace', style1.bg[gtk.STATE_NORMAL])
format += format_color_key('Hilight', menustyle.bg[gtk.STATE_PRELIGHT])
format += format_color_key('HilightText', style1.bg[gtk.STATE_PRELIGHT])
format += format_color_key('ButtonFace', style1.bg[gtk.STATE_NORMAL])
format += format_color_key('ButtonShadow', style1.bg[gtk.STATE_INSENSITIVE])
format += format_color_key('GrayText', style1.fg[gtk.STATE_INSENSITIVE])
format += format_color_key('ButtonText', style1.fg[gtk.STATE_NORMAL])
format += format_color_key('InactiveTitleText', style1.fg[gtk.STATE_INSENSITIVE])
format += format_color_key('ButtonHilight', style1.bg[gtk.STATE_NORMAL])
format += format_color_key('ButtonShadow', style1.fg[gtk.STATE_NORMAL])
format += format_color_key('ButtonLight', style1.fg[gtk.STATE_NORMAL])
format += format_color_key('InfoText', style1.fg[gtk.STATE_NORMAL])
format += format_color_key('InfoWindow', style1.fg[gtk.STATE_NORMAL])
format += format_color_key('ButtonAlternateFace', style1.bg[gtk.STATE_NORMAL])
format += format_color_key('ButtonHilight', style1.bg[gtk.STATE_NORMAL])
format += format_color_key('GradientActiveTitle', style1.bg[gtk.STATE_NORMAL])
format += format_color_key('GradientInactiveTitle', style1.bg[gtk.STATE_NORMAL])
format += format_color_key('MenuHilight', menustyle.bg[gtk.STATE_NORMAL])

print(format)

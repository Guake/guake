#!/usr/bin/env python
# gtk-theme-swatch: A PyGtk widget that displays the color swatches of all
# gtk.Styles, in all states. Useful for designing themes
# author: John Stowers <john.stowers@gmail.com>

import gtk
import pygtk

pygtk.require('2.0')


class ThemeSwatch(gtk.DrawingArea):

    SWATCH_SIZE = 50  # swatch size
    SWATCH_GAP = 5  # gap
    SWATCH_LABEL_SIZE = 10  # text size

    STYLES = (
        "fg",
        "bg",
        "light",
        "dark",
        "mid",
        "text",
        "base",
        "text_aa"
    )
    STYLE_STATES = {
        gtk.STATE_NORMAL: "normal",
        gtk.STATE_ACTIVE: "active",
        gtk.STATE_PRELIGHT: "prelight",
        gtk.STATE_SELECTED: "selected",
        gtk.STATE_INSENSITIVE: "insensitive"
    }

    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.connect("expose_event", self.expose)

    @classmethod
    def get_min_size(cls):
        w = (1 + len(cls.STYLE_STATES)) * (cls.SWATCH_SIZE + cls.SWATCH_GAP)
        h = (1 + len(cls.STYLES)) * (cls.SWATCH_SIZE + cls.SWATCH_GAP)
        return w, h

    def color_to_cairo_rgba(self, c, a=1):
        return c.red / 65535.0, c.green / 65535.0, c.blue / 65535.0, a

    def draw_rect(self, x, y, w, h, color):
        cr = self.context
        cr.rectangle(x, y, w, h)
        cr.set_source_rgba(
            *self.color_to_cairo_rgba(color)
        )
        cr.fill()

    def draw_round_rect(self, x, y, w, h, color, r=15):
        cr = self.context
        cr.set_source_rgba(
            *self.color_to_cairo_rgba(color)
        )

        cr.move_to(x + r, y)
        cr.line_to(x + w - r, y)
        cr.curve_to(x + w, y, x + w, y, x + w, y + r)
        cr.line_to(x + w, y + h - r)
        cr.curve_to(x + w, y + h, x + w, y + h, x + w - r, y + h)
        cr.line_to(x + r, y + h)
        cr.curve_to(x, y + h, x, y + h, x, y + h - r)
        cr.line_to(x, y + r)
        cr.curve_to(x, y, x, y, x + r, y)
        cr.close_path()

        cr.fill()

    def expose(self, widget, event):
        self.context = widget.window.cairo_create()

        # set a clip region for the expose event
        self.context.rectangle(event.area.x, event.area.y,
                               event.area.width, event.area.height)
        self.context.clip()

        self.draw()

        return False

    def draw(self):
        cr = self.context
        rect = self.get_allocation()

        s = self.SWATCH_SIZE  # swatch size
        g = self.SWATCH_GAP  # gap
        t = self.SWATCH_LABEL_SIZE  # text size

        x = rect.x + g
        y = rect.y

        # draw style state labels, x axis
        # cr.rotate(-30)
        cr.set_font_size(t)
        for state, name in self.STYLE_STATES.items():
            cr.set_source_rgb(0, 0, 0)
            cr.move_to(x + 0.5, y + s / 2 + t / 2)
            cr.show_text(name)
            x += g + s
        # cr.rotate(30)

        y += s
        x = rect.x + g
        for name in self.STYLES:
            colors = getattr(self.style, name, None)
            if colors:
                for state in self.STYLE_STATES:
                    color = colors[state]

                    # self.draw_rect(x, y, s, s, color)
                    self.draw_round_rect(x, y, s, s, color)
                    print "[%7s,%11s]" % (name, self.STYLE_STATES[state])

                    x += g + s

            # draw style labels, y axis
            cr.set_source_rgb(0, 0, 0)
            cr.move_to(x + g, y + s / 2 + t / 2)
            cr.show_text(name)

            x = rect.x + g
            y += g + s
            print ""


def main():
    window = gtk.Window()
    theme = ThemeSwatch()

    window.set_size_request(
        *theme.get_min_size()
    )
    window.add(theme)

    window.connect("destroy", gtk.main_quit)
    window.show_all()

    gtk.main()

if __name__ == "__main__":
    main()

"""
Copyright (C) 2009-2011  Lincoln de Sousa <lincoln@guake.org>

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
Free Software Foundation, Inc., 59 Temple Place - Suite 330,
Boston, MA 02111-1307, USA.
"""

from gi.repository import Gtk
from gi.repository import Vte
from gi.repository import GConf
from guake.globals import KEY

__all__ = 'Terminal', 'TerminalBox'

# regular expressions to highlight links in terminal. This code was
# lovely stolen from the great gnome-terminal project, thank you =)
USERCHARS = "-[:alnum:]"
PASSCHARS = "-[:alnum:],?;.:/!%$^*&~\"#'"
HOSTCHARS = "-[:alnum:]"
HOST      = "[" + HOSTCHARS + "]+(\\.[" + HOSTCHARS + "]+)*"
PORT      = "(:[:digit:]{1,5})?"
PATHCHARS =  "-[:alnum:]_$.+!*(),;:@&=?/~#%"
SCHEME    = "(news:|telnet:|nntp:|file:/|https?:|ftps?:|webcal:)"
USER      = "[" + USERCHARS + "]+(:[" + PASSCHARS + "]+)?"
URLPATH   = "/[" + PATHCHARS + "]*[^]'.}>) \t\r\n,\\\"]"
TERMINAL_MATCH_TAGS = 'schema', 'http', 'email'
TERMINAL_MATCH_EXPRS = [
  "\<" + SCHEME + "//(" + USER + "@)?" + HOST + PORT + "(" + URLPATH + ")?\>/?",
  "\<(www|ftp)[" + HOSTCHARS + "]*\." + HOST + PORT + "(" +URLPATH + ")?\>/?",
  "\<(mailto:)?[" + USERCHARS + "][" + USERCHARS + ".]*@[" + HOSTCHARS +
  "]+\." + HOST + "\>"
  ]


class Terminal(Vte.Terminal):
    """Just a Vte.Terminal with some properties already set.
    """
    def __init__(self):
        super(Terminal, self).__init__()
        self.configure_terminal()
        self.add_matches()
        self.connect('button-press-event', self.button_press)
        self.matched_value = ''

    def configure_terminal(self):
        """Sets all customized properties on the terminal
        """
        client = GConf.Client.get_default()
        word_chars = client.get_string(KEY('/general/word_chars'))
        self.set_word_chars(word_chars)
        self.set_audible_bell(False)
        self.set_visible_bell(False)
        self.set_sensitive(True)
        self.set_can_default(True)
        self.set_can_focus(True)

    def add_matches(self):
        """Adds all regular expressions declared in TERMINAL_MATCH_EXPRS
        to the terminal to make vte highlight text that matches them.
        """
        # FIXME: match_add is deprecated we should use match_add_regex
        # witch takes GRegex as parameter but first we need to find
        # a way to construct GRegex objects (GLib.Regex)
        #
        # This is the error happening when trying to create a new
        # GRegex: https://bugzilla.gnome.org/show_bug.cgi?id=647249
        pass

        # for expr in TERMINAL_MATCH_EXPRS:
        #     tag = self.match_add_gregex(GLib.Regex(expr, 0))
        #     self.match_set_cursor_type(tag, Gdk.HAND2)

    def button_press(self, terminal, event):
        """Handles the button press event in the terminal widget. If
        any match string is caught, another aplication is open to
        handle the matched resource uri.
        """
        self.matched_value = ''
        matched_string = self.match_check(
            int(event.x / self.get_char_width()),
            int(event.y / self.get_char_height()))

        if event.button == 1 \
                and event.get_state()[1] & Gdk.ModifierType.CONTROL_MASK \
                and matched_string:
            value, tag = matched_string

            if TERMINAL_MATCH_TAGS[tag] == 'schema':
                # value here should not be changed, it is right and
                # ready to be used.
                pass
            elif TERMINAL_MATCH_TAGS[tag] == 'http':
                value = 'http://%s' % value
            elif TERMINAL_MATCH_TAGS[tag] == 'email':
                value = 'mailto:%s' % value

            Gtk.show_uri(self.window.get_screen(), value,
                         GdkX11.get_server_time(self.window))
        elif event.button == 3 and matched_string:
            self.matched_value = matched_string[0]

class TerminalBox(Gtk.HBox):
    """A box to group the terminal and a scrollbar.
    """
    def __init__(self):
        super(TerminalBox, self).__init__()
        self.terminal = Terminal()
        self.add_terminal()
        self.add_scrollbar()

    def add_terminal(self):
        """Packs the terminal widget.
        """
        self.pack_start(self.terminal, True, True, 0)
        self.terminal.show()

    def add_scrollbar(self):
        """Packs the scrollbar.
        """
        adj = self.terminal.get_vadjustment()
        scroll = Gtk.VScrollbar.new(adj)
        scroll.set_no_show_all(True)
        self.pack_start(scroll, False, False, 0)


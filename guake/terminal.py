# -*- coding: utf-8; -*-
"""
Copyright (C) 2007-2013 Guake authors

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
import code
import logging
import os
import re
import signal
import subprocess
import threading
import uuid

from pathlib import Path
from typing import Optional
from typing import Tuple

from time import sleep

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')  # vte-0.38

from gi.repository import GLib
from gi.repository import Gdk
from gi.repository import GdkX11
from gi.repository import Gtk
from gi.repository import Pango
from gi.repository import Vte

from guake.common import clamp

log = logging.getLogger(__name__)


def halt(loc):
    code.interact(local=loc)


# TODO PORT
# __all__ = ['Terminal', 'TerminalBox']

# TODO this is not as fancy as as it could be
# pylint: disable=anomalous-backslash-in-string
TERMINAL_MATCH_TAGS = ('schema', 'http', 'https', 'email', 'ftp')
TERMINAL_MATCH_EXPRS = [
    "(news:|telnet:|nntp:|file:\/|https?:|ftps?:|webcal:)\/\/"
    "([-[:alnum:]]+(:[-[:alnum:],?;.:\/!%$^*&~\"#']+)?\@)?[-[:alnum:]]+"
    "(\.[-[:alnum:]]+)*(:[0-9]{1,5})?(\/[-[:alnum:]_$.+!*(),;:@&=?\/~#%]*[^]'.>) \t\r\n,\\\"])?",
    "(www|ftp)[-[:alnum:]]*\.[-[:alnum:]]+(\.[-[:alnum:]]+)*(:[0-9]{1,5})?"
    "(\/[-[:alnum:]_$.+!*(),;:@&=?\/~#%]*[^]'.>) \t\r\n,\\\"])?",
    "(mailto:)?[-[:alnum:]][-[:alnum:].]*@[-[:alnum:]]+\.[-[:alnum:]]+(\\.[-[:alnum:]]+)*"
]
# tuple (title/quick matcher/filename and line number extractor)
QUICK_OPEN_MATCHERS = [
    (
        "Python traceback", r"^\s*File\s\".*\",\sline\s[0-9]+",
        r"^\s*File\s\"(.*)\",\sline\s([0-9]+)"
    ),
    (
        "line starts by 'Filename:line' pattern (GCC/make). File path should exists.",
        r"^\s*[a-zA-Z0-9\/\_\-\.\ ]+\.?[a-zA-Z0-9]+\:[0-9]+", r"^\s*.(.*)\:([0-9]+)"
    )
]

# pylint: enable=anomalous-backslash-in-string


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


class GuakeTerminal(Vte.Terminal):

    """Just a vte.Terminal with some properties already set.
    """

    def __init__(self, settings):
        super(GuakeTerminal, self).__init__()
        self.settings = settings
        self.configure_terminal()
        self.add_matches()
        self.connect('button-press-event', self.button_press)
        self.matched_value = ''
        self.font_scale_index = 0
        self._pid = None
        self.custom_bgcolor = None
        self.custom_fgcolor = None
        self.found_link = None
        self.uuid = uuid.uuid4()

    def get_uuid(self):
        return self.uuid

    @property
    def pid(self):
        return self._pid

    @pid.setter
    def pid(self, pid):
        self._pid = pid

    def copy_clipboard(self):
        if self.get_has_selection():
            super(GuakeTerminal, self).copy_clipboard()
        elif self.matched_value:
            guake_clipboard = Gtk.Clipboard.get_default(self.window.get_display())
            guake_clipboard.set_text(self.matched_value)

    def configure_terminal(self):
        """Sets all customized properties on the terminal
        """
        client = self.settings.general
        word_chars = client.get_string('word-chars')
        if word_chars:
            # TODO PORT this does not work this way any more see:
            #   https://lazka.github.io/
            #          pgi-docs/Vte-2.91/classes/Terminal.html#Vte.Terminal.set_word_char_exceptions
            # self.set_word_chars(word_chars)
            pass
        self.set_audible_bell(client.get_boolean('use-audible-bell'))
        self.set_sensitive(True)

        cursor_blink_mode = self.settings.style.get_int('cursor-blink-mode')
        self.set_property('cursor-blink-mode', cursor_blink_mode)

        # TODO PORT there is no method set_flags anymore
        # self.set_flags(gtk.CAN_DEFAULT)
        # self.set_flags(gtk.CAN_FOCUS)
        # TODO PORT getting it and then setting it???
        # cursor_shape = client.get_int(KEY('/style/cursor_shape'))
        # client.set_int(KEY('/style/cursor_shape'), cursor_shape)

    def add_matches(self):
        """Adds all regular expressions declared in
        guake.globals.TERMINAL_MATCH_EXPRS to the terminal to make vte
        highlight text that matches them.
        """
        # log.debug("Skipped 'match' feature")
        for expr in TERMINAL_MATCH_EXPRS:
            # TODO PORT next line throws a Vte-WARNIN but works: runtime check failed
            tag = self.match_add_gregex(GLib.Regex.new(expr, 0, 0), 0)
            self.match_set_cursor_type(tag, Gdk.CursorType.HAND2)

        for _useless, match, _otheruseless in QUICK_OPEN_MATCHERS:
            # TODO PORT next line throws a Vte-WARNIN but works: runtime check failed
            tag = self.match_add_gregex(GLib.Regex.new(match, 0, 0), 0)
            self.match_set_cursor_type(tag, Gdk.CursorType.HAND2)

    def get_current_directory(self):
        directory = os.path.expanduser('~')
        if self.pid is not None:
            cwd = os.readlink("/proc/{}/cwd".format(self.pid))
            if os.path.exists(cwd):
                directory = cwd
        return directory

    def _is_file_on_local_server(self, text) -> Tuple[Optional[Path], Optional[int], Optional[int]]:
        """Test if the provided text matches a file on local server

        Supports:
         - absolute path
         - relative path (using current working directory)
         - file:line syntax
         - file:line:colum syntax

        Args:
            text (str): candidate for file search

        Returns
            - Tuple(None, None, None) is the provided text does not match anything
            - Tuple(file path, None, None) if only a file path is found
            - Tuple(file path, linenumber, None) if line number is found
            - Tuple(file path, linenumber, columnnumber) if line and column numbers are found
        """
        lineno = None
        colno = None
        m = re.compile(r"(.*)\:(\d+)\:(\d+)$").match(text)
        if m:
            text = m.group(1)
            lineno = m.group(2)
            colno = m.group(3)
        else:
            m = re.compile(r"(.*)\:(\d+)$").match(text)
            if m:
                text = m.group(1)
                lineno = m.group(2)
        pt = Path(text)
        log.debug("checking file existance: %r", pt)
        if pt.exists():
            log.debug("File exists: %r", pt.absolute().as_posix())
            return (pt, lineno, colno)
        log.debug("No file found matching: %r", text)
        cwd = self.get_current_directory()
        pt = Path(cwd) / pt
        log.debug("checking file existance: %r", pt)
        if pt.exists():
            log.debug("File exists: %r", pt.absolute().as_posix())
            return (pt, lineno, colno)
        return (None, None, None)

    def button_press(self, terminal, event):
        """Handles the button press event in the terminal widget. If
        any match string is caught, another application is open to
        handle the matched resource uri.
        """
        self.matched_value = ''
        matched_string = self.match_check(
            int(event.x / self.get_char_width()), int(event.y / self.get_char_height())
        )

        self.found_link = None

        if event.button == 1 and (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
            if self.get_has_selection():
                self.copy_clipboard()
                clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
                text = clipboard.wait_for_text()
                (fp, lo, co) = self._is_file_on_local_server(text)
                self._execute_quick_open(fp, lo)
            elif matched_string and matched_string[0]:
                self.__on_ctrl_click_matcher(matched_string)
        elif event.button == 3 and matched_string:
            self.found_link = self.handleTerminalMatch(matched_string)
            self.matched_value = matched_string[0]

    def __on_ctrl_click_matcher(self, matched_string):
        value, tag = matched_string
        log.debug("matched string: %s", matched_string)
        # First searching in additional matchers
        found_additional_matcher = False
        # TODO PORT
        use_quick_open = self.settings.general.get_boolean("quick-open-enable")
        quick_open_in_current_terminal = self.settings.general.get_boolean(
            "quick-open-in-current-terminal"
        )
        if use_quick_open:
            for _useless, _otheruseless, extractor in QUICK_OPEN_MATCHERS:
                print("value", value)
                g = re.compile(extractor).match(value)
                if g and g.groups():
                    filename = g.group(1).strip()
                    filepath = filename
                    line_number = g.group(2)
                    if line_number is None:
                        line_number = "1"
                    if not quick_open_in_current_terminal:
                        (filepath, _lo, _co) = self._is_file_on_local_server(filename)
                    # for quick_open_in_current_terminal, we run the command line directly in
                    # the tab so relative path is enough.
                    #
                    # We do not test for file existence, because it doesn't work in ssh
                    # sessions.
                    self._execute_quick_open(filepath, line_number)
                    found_additional_matcher = True
                    break
        if not found_additional_matcher:
            self.found_link = self.handleTerminalMatch(matched_string)
            if self.found_link:
                self.browse_link_under_cursor()

    def _execute_quick_open(self, filepath, line_number):
        cmdline = self.settings.general.get_string("quick-open-command-line")
        if not line_number:
            line_number = ""
        logging.debug("Opening file %s at line %s", filepath, line_number)
        resolved_cmdline = cmdline % {"file_path": filepath, "line_number": line_number}
        logging.debug("Command line: %s", resolved_cmdline)
        quick_open_in_current_terminal = self.settings.general.get_boolean(
            "quick-open-in-current-terminal"
        )
        if quick_open_in_current_terminal:
            logging.debug("Executing it in current tab")
            if resolved_cmdline[-1] != '\n':
                resolved_cmdline += '\n'
            self.feed_child(resolved_cmdline, len(resolved_cmdline))
        else:
            logging.debug("Executing it independently")
            subprocess.call(resolved_cmdline, shell=True)

    def handleTerminalMatch(self, matched_string):
        value, tag = matched_string
        log.debug("found tag: %r, item: %r", tag, value)
        if tag in TERMINAL_MATCH_TAGS:
            if TERMINAL_MATCH_TAGS[tag] == 'schema':
                # value here should not be changed, it is right and
                # ready to be used.
                pass
            elif TERMINAL_MATCH_TAGS[tag] == 'http':
                value = 'http://%s' % value
            elif TERMINAL_MATCH_TAGS[tag] == 'https':
                value = 'https://%s' % value
            elif TERMINAL_MATCH_TAGS[tag] == 'ftp':
                value = 'ftp://%s' % value
            elif TERMINAL_MATCH_TAGS[tag] == 'email':
                value = 'mailto:%s' % value

        if value:
            return value

    def browse_link_under_cursor(self):
        if not self.found_link:
            return
        log.debug("Opening link: %s", self.found_link)
        cmd = ["xdg-open", self.found_link]
        subprocess.Popen(cmd, shell=False)

    def set_font(self, font):
        self.font = font
        self.set_font_scale_index(0)

    def set_font_scale_index(self, scale_index):
        self.font_scale_index = clamp(scale_index, -6, 12)

        font = Pango.FontDescription(self.font.to_string())
        scale_factor = 2 ** (self.font_scale_index / 6)
        new_size = int(scale_factor * font.get_size())

        if font.get_size_is_absolute():
            font.set_absolute_size(new_size)
        else:
            font.set_size(new_size)

        super(GuakeTerminal, self).set_font(font)

    font_scale = property(fset=set_font_scale_index, fget=lambda self: self.font_scale_index)

    def increase_font_size(self):
        self.font_scale += 1

    def decrease_font_size(self):
        self.font_scale -= 1

    def kill(self):
        pid = self.pid
        threading.Thread(target=self.delete_shell, args=(pid, )).start()
        # start_new_thread(self.delete_shell, (pid,))

    def delete_shell(self, pid):
        """This function will kill the shell on a tab, trying to send
        a sigterm and if it doesn't work, a sigkill. Between these two
        signals, we have a timeout of 3 seconds, so is recommended to
        call this in another thread. This doesn't change any thing in
        UI, so you can use python's start_new_thread.
        """
        try:
            os.kill(pid.child_pid, signal.SIGHUP)
        except OSError:
            pass
        num_tries = 30

        while num_tries > 0:
            try:
                # Try to wait for the pid to be closed. If it does not
                # exist anymore, an OSError is raised and we can
                # safely ignore it.
                if os.waitpid(pid.child_pid, os.WNOHANG)[0] != 0:
                    break
            except OSError:
                break
            sleep(0.1)
            num_tries -= 1

        if num_tries == 0:
            try:
                os.kill(pid.child_pid, signal.SIGKILL)
                os.waitpid(pid.child_pid, 0)
            except OSError:
                # if this part of code was reached, means that SIGTERM
                # did the work and SIGKILL wasnt needed.
                pass


# TODO PORT port this from HBOX to Box with orientation horitzontal


class GuakeTerminalBox(Gtk.HBox):

    """A box to group the terminal and a scrollbar.
    """

    def __init__(self, settings):
        super(GuakeTerminalBox, self).__init__()
        self.terminal = GuakeTerminal(settings)
        self.add_terminal()
        self.add_scroll_bar()

    def add_terminal(self):
        """Packs the terminal widget.
        """
        self.pack_start(self.terminal, True, True, 0)
        self.terminal.show()

    def add_scroll_bar(self):
        """Packs the scrollbar.
        """
        adj = self.terminal.get_vadjustment()
        scroll = Gtk.VScrollbar(adj)
        scroll.show()
        self.pack_start(scroll, False, False, 0)

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
import shlex
import signal
import subprocess
import sys
import threading
import uuid

from enum import IntEnum
from pathlib import Path
from typing import Optional
from typing import Tuple
from urllib.parse import unquote
from urllib.parse import urlparse

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Vte", "2.91")  # vte-0.38

from gi.repository import GLib
from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import Pango
from gi.repository import Vte

from guake.common import clamp
from guake.globals import QUICK_OPEN_MATCHERS
from guake.globals import TERMINAL_MATCH_EXPRS
from guake.globals import TERMINAL_MATCH_TAGS

log = logging.getLogger(__name__)

libutempter = None
try:
    # this allow to run some commands that requires libuterm to
    # be injected in current process, as: wall
    from atexit import register as at_exit_call
    from ctypes import cdll

    libutempter = cdll.LoadLibrary("libutempter.so.0")
    if libutempter is not None:
        # We absolutely need to remove the old tty from the utmp !!!
        at_exit_call(libutempter.utempter_remove_added_record)
except Exception as e:
    libutempter = None
    sys.stderr.write("[WARN] ===================================================================\n")
    sys.stderr.write("[WARN] Unable to load the library libutempter !\n")
    sys.stderr.write(
        "[WARN] Some feature might not work:\n"
        "[WARN]  - 'exit' command might freeze the terminal instead of closing the tab\n"
        "[WARN]  - the 'wall' command is known to work badly\n"
    )
    sys.stderr.write("[WARN] Error: " + str(e) + "\n")
    sys.stderr.write(
        "[WARN] ===================================================================²\n"
    )


def halt(loc):
    code.interact(local=loc)


__all__ = ["GuakeTerminal"]

# pylint: enable=anomalous-backslash-in-string


class DropTargets(IntEnum):
    URIS = 0
    TEXT = 1


class GuakeTerminal(Vte.Terminal):

    """Just a vte.Terminal with some properties already set."""

    def __init__(self, guake):
        super().__init__()
        self.guake = guake
        self.configure_terminal()
        self.add_matches()
        self.handler_ids = []
        self.handler_ids.append(self.connect("button-press-event", self.button_press))
        self.connect("child-exited", self.on_child_exited)  # Call on_child_exited, don't remove it
        self.connect("selection-changed", self.copy_on_select)
        self.matched_value = ""
        self.font_scale_index = 0
        self._pid = None
        # self.custom_bgcolor = None
        # self.custom_fgcolor = None
        self.found_link = None
        self.uuid = uuid.uuid4()

        # Custom colors
        self.custom_bgcolor = None
        self.custom_fgcolor = None
        self.custom_palette = None

        self.setup_drag_and_drop()

        self.ENVV_EXCLUDE_LIST = ["GDK_BACKEND"]
        self.envv = [f"{i}={os.environ[i]}" for i in os.environ if i not in self.ENVV_EXCLUDE_LIST]
        self.envv.append(f"GUAKE_TAB_UUID={self.uuid}")

    def setup_drag_and_drop(self):
        self.targets = Gtk.TargetList()
        self.targets.add_uri_targets(DropTargets.URIS)
        self.targets.add_text_targets(DropTargets.TEXT)
        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.drag_dest_set_target_list(self.targets)
        self.connect("drag-data-received", self.on_drag_data_received)

    def get_uuid(self):
        return self.uuid

    @property
    def pid(self):
        return self._pid

    @pid.setter
    def pid(self, pid):
        self._pid = pid

    def feed_child(self, resolved_cmdline):
        if (Vte.MAJOR_VERSION, Vte.MINOR_VERSION) >= (0, 42):
            encoded = resolved_cmdline.encode("utf-8")
            try:
                super().feed_child_binary(encoded)
            except TypeError:
                # The doc doest not say clearly at which version the feed_child* function has lost
                # the "len" parameter :(
                super().feed_child(resolved_cmdline, len(resolved_cmdline))
        else:
            super().feed_child(resolved_cmdline, len(resolved_cmdline))

    def execute_command(self, command):
        if command[-1] != "\n":
            command += "\n"
        self.feed_child(command)

    def copy_clipboard(self):
        if self.get_has_selection():
            super().copy_clipboard()
        elif self.matched_value:
            guake_clipboard = Gtk.Clipboard.get_default(self.guake.window.get_display())
            guake_clipboard.set_text(self.matched_value, len(self.matched_value))

    def copy_on_select(self, event):
        if self.guake.settings.general.get_boolean("copy-on-select") and self.get_has_selection():
            self.copy_clipboard()

    def configure_terminal(self):
        """Sets all customized properties on the terminal"""
        client = self.guake.settings.general
        word_chars = client.get_string("word-chars")
        if word_chars:
            self.set_word_char_exceptions(word_chars)
        self.set_audible_bell(client.get_boolean("use-audible-bell"))
        self.set_sensitive(True)

        cursor_blink_mode = self.guake.settings.style.get_int("cursor-blink-mode")
        self.set_property("cursor-blink-mode", cursor_blink_mode)

        if (Vte.MAJOR_VERSION, Vte.MINOR_VERSION) >= (0, 50):
            self.set_allow_hyperlink(True)

        if (Vte.MAJOR_VERSION, Vte.MINOR_VERSION) >= (0, 52):
            try:
                self.set_cell_height_scale(
                    self.guake.settings.styleFont.get_double("cell-height-scale")
                )
            except:  # pylint: disable=bare-except
                log.error("set_cell_height_scale not supported by your version of VTE")
            try:
                self.set_cell_width_scale(
                    self.guake.settings.styleFont.get_double("cell-width-scale")
                )
            except:  # pylint: disable=bare-except
                log.error("set_cell_width_scale not supported by your version of VTE")

        if (Vte.MAJOR_VERSION, Vte.MINOR_VERSION) >= (0, 56):
            try:
                self.set_bold_is_bright(self.guake.settings.styleFont.get_boolean("bold-is-bright"))
            except:  # pylint: disable=bare-except
                log.error("set_bold_is_bright not supported by your version of VTE")

        # TODO PORT is this still the case with the newer vte version?
        # -- Ubuntu has a patch to libvte which disables mouse scrolling in apps
        # -- like vim and less by default. If this is the case, enable it back.
        if hasattr(self, "set_alternate_screen_scroll"):
            self.set_alternate_screen_scroll(True)

        self.set_can_default(True)
        self.set_can_focus(True)

    def add_matches(self):
        """Adds all regular expressions declared in
        guake.globals.TERMINAL_MATCH_EXPRS to the terminal to make vte
        highlight text that matches them.
        """
        try:
            # NOTE: PCRE2_UTF | PCRE2_NO_UTF_CHECK | PCRE2_MULTILINE
            # reference from vte/bindings/vala/app.vala, flags = 0x40080400u
            # also ref: https://mail.gnome.org/archives/commits-list/2016-September/msg06218.html
            VTE_REGEX_FLAGS = 0x40080400
            for expr in TERMINAL_MATCH_EXPRS:
                tag = self.match_add_regex(
                    Vte.Regex.new_for_match(expr, len(expr), VTE_REGEX_FLAGS), 0
                )
                self.match_set_cursor_type(tag, Gdk.CursorType.HAND2)

            for _useless, match, _otheruseless in QUICK_OPEN_MATCHERS:
                tag = self.match_add_regex(
                    Vte.Regex.new_for_match(match, len(match), VTE_REGEX_FLAGS), 0
                )
                self.match_set_cursor_type(tag, Gdk.CursorType.HAND2)
        except (
            GLib.Error,
            AttributeError,
        ):  # pylint: disable=catching-non-exception
            try:
                compile_flag = 0
                if (Vte.MAJOR_VERSION, Vte.MINOR_VERSION) >= (0, 44):
                    compile_flag = GLib.RegexCompileFlags.MULTILINE
                for expr in TERMINAL_MATCH_EXPRS:
                    tag = self.match_add_gregex(GLib.Regex.new(expr, compile_flag, 0), 0)
                    self.match_set_cursor_type(tag, Gdk.CursorType.HAND2)

                for _useless, match, _otheruseless in QUICK_OPEN_MATCHERS:
                    tag = self.match_add_gregex(GLib.Regex.new(match, compile_flag, 0), 0)
                    self.match_set_cursor_type(tag, Gdk.CursorType.HAND2)
            except GLib.Error as err:  # pylint: disable=catching-non-exception
                log.error(
                    "ERROR: PCRE2 does not seems to be enabled on your system. "
                    "Quick Edit and other Ctrl+click features are disabled. "
                    "Please update your VTE package or contact your distribution to ask "
                    "to enable regular expression support in VTE. Exception: '%s'",
                    str(err),
                )

    def get_current_directory(self):
        directory = os.path.expanduser("~")
        if self.pid is not None:
            try:
                cwd = os.readlink(f"/proc/{self.pid}/cwd")
            except Exception:
                return directory
            if os.path.exists(cwd):
                directory = cwd
        return directory

    def is_file_on_local_server(self, text) -> Tuple[Optional[Path], Optional[int], Optional[int]]:
        """Test if the provided text matches a file on local server

        Supports:
         - absolute path
         - relative path (using current working directory)
         - file:line syntax
         - file:line:colum syntax

        Args:
            text (str): candidate for file search

        Returns
            - Tuple(None, None, None) if the provided text does not match anything
            - Tuple(file path, None, None) if only a file path is found
            - Tuple(file path, linenumber, None) if line number is found
            - Tuple(file path, linenumber, columnnumber) if line and column numbers are found
        """
        lineno = None
        colno = None
        py_func = None
        # "<File>:<line>:<col>"
        m = re.compile(r"(.*)\:(\d+)\:(\d+)$").match(text)
        if m:
            text = m.group(1)
            lineno = m.group(2)
            colno = m.group(3)
        else:
            # "<File>:<line>"
            m = re.compile(r"(.*)\:(\d+)$").match(text)
            if m:
                text = m.group(1)
                lineno = m.group(2)
            else:
                # "<File>::<python_function>"
                m = re.compile(r"^(.*)\:\:([a-zA-Z0-9\_]+)$").match(text)
                if m:
                    text = m.group(1)
                    py_func = m.group(2).strip()

        def find_lineno(text, pt, lineno, py_func):
            # print("text={!r}, pt={!r}, lineno={!r}, py_func={!r}".format(text,
            #                                                              pt, lineno, py_func))
            if lineno:
                return lineno
            if not py_func:
                return
            with pt.open() as f:
                for i, line in enumerate(f.readlines()):
                    if line.startswith(f"def {py_func}"):
                        return i + 1
                        break

        pt = Path(text)
        log.debug("checking file existance: %r", pt)
        try:
            if pt.exists():
                lineno = find_lineno(text, pt, lineno, py_func)
                log.info("File exists: %r, line=%r", pt.absolute().as_posix(), lineno)
                return (pt, lineno, colno)
            log.debug("No file found matching: %r", text)
            cwd = self.get_current_directory()
            pt = Path(cwd) / pt
            log.debug("checking file existance: %r", pt)
            if pt.exists():
                lineno = find_lineno(text, pt, lineno, py_func)
                log.info("File exists: %r, line=%r", pt.absolute().as_posix(), lineno)
                return (pt, lineno, colno)
            log.debug("file does not exist: %s", str(pt))
        except OSError:
            log.debug("not a file name: %r", text)
        return (None, None, None)

    def button_press(self, terminal, event):
        """Handles the button press event in the terminal widget. If
        any match string is caught, another application is open to
        handle the matched resource uri.
        """
        self.matched_value = ""
        if (Vte.MAJOR_VERSION, Vte.MINOR_VERSION) >= (0, 46):
            matched_string = self.match_check_event(event)
        else:
            matched_string = self.match_check(
                int(event.x / self.get_char_width()),
                int(event.y / self.get_char_height()),
            )

        self.found_link = None

        if event.button == 1 and (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
            if (Vte.MAJOR_VERSION, Vte.MINOR_VERSION) > (0, 50):
                s = self.hyperlink_check_event(event)
            else:
                s = None
            if s is not None:
                self._on_ctrl_click_matcher((s, None))
            elif self.get_has_selection():
                self.quick_open()
            elif matched_string and matched_string[0]:
                self._on_ctrl_click_matcher(matched_string)
        elif event.button == 3 and matched_string:
            self.found_link = self.handleTerminalMatch(matched_string)
            self.matched_value = matched_string[0]

    def on_child_exited(self, target, status, *user_data):
        if None not in (libutempter, self.get_pty()):
            libutempter.utempter_remove_record(self.get_pty().get_fd())

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        if info == DropTargets.URIS:
            uris = data.get_uris()
            for uri in uris:
                path = Path(unquote(urlparse(uri).path))
                self.feed_child(shlex.quote(str(path.absolute())) + " ")
        elif info == DropTargets.TEXT:
            text = data.get_text()
            if text:
                self.feed_child(text)

    def quick_open(self):
        self.copy_clipboard()
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        text = clipboard.wait_for_text()
        if not text:
            return
        (fp, lo, co) = self.is_file_on_local_server(text)
        self._execute_quick_open(fp, lo)

    def _on_ctrl_click_matcher(self, matched_string):
        value, tag = matched_string
        found_matcher = False
        log.debug("matched string: %s", matched_string)
        # First searching in additional matchers
        use_quick_open = self.guake.settings.general.get_boolean("quick-open-enable")
        if use_quick_open:
            found_matcher = self._find_quick_matcher(value)
        if not found_matcher:
            self.found_link = self.handleTerminalMatch(matched_string)
            if self.found_link:
                self.browse_link_under_cursor()

    def _find_quick_matcher(self, value):
        for _useless, _otheruseless, extractor in QUICK_OPEN_MATCHERS:
            g = re.compile(extractor).match(value)
            if g and g.groups():
                filename = g.group(1).strip()
                if len(g.groups()) >= 2:
                    line_number = g.group(2)
                else:
                    line_number = None
                log.info("Quick action executed filename=%s, line=%s", filename, line_number)
                (filepath, ln, _) = self.is_file_on_local_server(filename)
                if ln:
                    line_number = ln
                if not filepath:
                    continue
                if line_number is None:
                    line_number = "1"
                self._execute_quick_open(filepath, line_number)
                return True
        return False

    def _execute_quick_open(self, filepath, line_number):
        if not filepath:
            return
        cmdline = self.guake.settings.general.get_string("quick-open-command-line")
        if not line_number:
            line_number = ""
        else:
            line_number = str(line_number)
        logging.debug("Opening file %s at line %s", filepath, line_number)
        resolved_cmdline = cmdline % {"file_path": filepath, "line_number": line_number}
        logging.debug("Command line: %s", resolved_cmdline)
        quick_open_in_current_terminal = self.guake.settings.general.get_boolean(
            "quick-open-in-current-terminal"
        )
        if quick_open_in_current_terminal:
            logging.debug("Executing it in current tab")
            if resolved_cmdline[-1] != "\n":
                resolved_cmdline += "\n"
            self.feed_child(resolved_cmdline)
        else:
            resolved_cmdline += " &"
            logging.debug("Executing it independently")
            subprocess.call(resolved_cmdline, shell=True)

    def handleTerminalMatch(self, matched_string):
        value, tag = matched_string
        log.debug("found tag: %r, item: %r", tag, value)
        if tag in TERMINAL_MATCH_TAGS:
            if TERMINAL_MATCH_TAGS[tag] == "schema":
                # value here should not be changed, it is right and
                # ready to be used.
                pass
            elif TERMINAL_MATCH_TAGS[tag] == "http":
                value = f"http://{value}"
            elif TERMINAL_MATCH_TAGS[tag] == "https":
                value = f"https://{value}"
            elif TERMINAL_MATCH_TAGS[tag] == "ftp":
                value = f"ftp://{value}"
            elif TERMINAL_MATCH_TAGS[tag] == "email":
                value = f"mailto:{value}"

        if value:
            return value

    def get_link_under_cursor(self):
        return self.found_link

    def browse_link_under_cursor(self):
        # TODO move the call to xdg-open to guake.utils
        if not self.found_link:
            return
        log.debug("Opening link: %s", self.found_link)
        cmd = ["xdg-open", self.found_link]
        with subprocess.Popen(cmd, shell=False):
            pass

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

        super().set_font(font)

    font_scale = property(fset=set_font_scale_index, fget=lambda self: self.font_scale_index)

    def increase_font_size(self):
        self.font_scale += 1

    def decrease_font_size(self):
        self.font_scale -= 1

    def kill(self):
        pid = self.pid
        threading.Thread(target=self.delete_shell, args=(pid,)).start()
        # start_new_thread(self.delete_shell, (pid,))

    def delete_shell(self, pid):
        """Kill the shell with SIGHUP

        NOTE: Leave it alone, DO NOT USE os.waitpid

        > sys:1: Warning: GChildWatchSource: Exit status of a child process was requested but
                 ECHILD was received by waitpid(). See the documentation of
                 g_child_watch_source_new() for possible causes.

        g_child_watch_source_new() documentation:
            https://developer.gnome.org/glib/stable/glib-The-Main-Event-Loop.html#g-child-watch-source-new

        On POSIX platforms, the following restrictions apply to this API due to limitations
        in POSIX process interfaces:
            ...
            * the application must not wait for pid to exit by any other mechanism,
              including waitpid(pid, ...) or a second child-watch source for the same pid
            ...
        For this reason, we should not call os.waitpid(pid, ...), leave it to OS
        """
        try:
            os.kill(pid, signal.SIGHUP)
        except OSError:
            pass

    def spawn_sync_pid(self, directory):

        argv = []
        user_shell = self.guake.settings.general.get_string("default-shell")
        if user_shell and os.path.exists(user_shell):
            argv.append(user_shell)
        else:
            try:
                argv.append(os.environ["SHELL"])
            except KeyError:
                argv.append("/usr/bin/bash")

        login_shell = self.guake.settings.general.get_boolean("use-login-shell")
        if login_shell:
            argv.append("--login")

        log.debug('Spawn command: "%s"', " ".join(argv))

        pid = self.spawn_sync(
            Vte.PtyFlags.DEFAULT,
            directory,
            argv,
            self.envv,
            GLib.SpawnFlags(Vte.SPAWN_NO_PARENT_ENVV),
            None,
            None,
            None,
        )

        try:
            tuple_type = gi._gi.ResultTuple  # pylint: disable=c-extension-no-member
        except:  # pylint: disable=bare-except
            tuple_type = tuple
        if isinstance(pid, (tuple, tuple_type)):
            # Return a tuple in 2.91
            # https://lazka.github.io/pgi-docs/Vte-2.91/classes/Terminal.html#Vte.Terminal.spawn_sync
            pid = pid[1]
        if not isinstance(pid, int):
            raise TypeError("pid must be an int")

        if libutempter is not None:
            libutempter.utempter_add_record(self.get_pty().get_fd(), os.uname()[1])
        self.pid = pid
        return pid

    def set_color_foreground(self, font_color, *args, **kwargs):
        real_fgcolor = self.custom_fgcolor if self.custom_fgcolor else font_color
        super().set_color_foreground(real_fgcolor, *args, **kwargs)

    def set_color_background(self, bgcolor, *args, **kwargs):
        real_bgcolor = self.custom_bgcolor if self.custom_bgcolor else bgcolor
        super().set_color_background(real_bgcolor, *args, **kwargs)

    def set_color_bold(self, font_color, *args, **kwargs):
        real_fgcolor = self.custom_fgcolor if self.custom_fgcolor else font_color
        super().set_color_bold(real_fgcolor, *args, **kwargs)

    def set_colors(self, font_color, bg_color, palette_list, *args, **kwargs):
        real_bgcolor = self.custom_bgcolor if self.custom_bgcolor else bg_color
        real_fgcolor = self.custom_fgcolor if self.custom_fgcolor else font_color
        real_palette = self.custom_palette if self.custom_palette else palette_list
        super().set_colors(real_fgcolor, real_bgcolor, real_palette, *args, **kwargs)

    def set_color_foreground_custom(self, fgcolor, *args, **kwargs):
        """Sets custom foreground color for this terminal"""
        print(f"set_color_foreground_custom: {self.uuid}")
        self.custom_fgcolor = fgcolor
        super().set_color_foreground(self.custom_fgcolor, *args, **kwargs)

    def set_color_background_custom(self, bgcolor, *args, **kwargs):
        """Sets custom background color for this terminal"""
        self.custom_bgcolor = bgcolor
        super().set_color_background(self.custom_bgcolor, *args, **kwargs)

    def reset_custom_colors(self):
        self.custom_fgcolor = None
        self.custom_bgcolor = None
        self.custom_palette = None

    @staticmethod
    def _color_to_list(color):
        """This method is used for serialization."""
        if color is None:
            return None
        return [color.red, color.green, color.blue, color.alpha]

    @staticmethod
    def _color_from_list(color_list):
        """This method is used for deserialization."""
        return Gdk.RGBA(
            red=color_list[0],
            green=color_list[1],
            blue=color_list[2],
            alpha=color_list[3],
        )

    def get_custom_colors_dict(self):
        """Returns dictionary of custom colors."""
        return {
            "fg_color": self._color_to_list(self.custom_fgcolor),
            "bg_color": self._color_to_list(self.custom_bgcolor),
            "palette": [self._color_to_list(col) for col in self.custom_palette]
            if self.custom_palette
            else None,
        }

    def set_custom_colors_from_dict(self, colors_dict):
        if not isinstance(colors_dict, dict):
            return

        bg_color = colors_dict.get("bg_color", None)
        if isinstance(bg_color, list):
            self.custom_bgcolor = self._color_from_list(bg_color)
        else:
            self.custom_bgcolor = None

        fg_color = colors_dict.get("fg_color", None)
        if isinstance(fg_color, list):
            self.custom_fgcolor = self._color_from_list(fg_color)
        else:
            self.custom_fgcolor = None

        palette = colors_dict.get("palette", None)
        if isinstance(palette, list):
            self.custom_palette = [self._color_from_list(col) for col in palette]
        else:
            self.custom_palette = None

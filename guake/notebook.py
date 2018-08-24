# -*- coding: utf-8; -*-
"""
Copyright (C) 2007-2018 Guake authors

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

from guake.boxes import DualTerminalBox
from guake.boxes import RootTerminalBox
from guake.boxes import TerminalBox

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from guake.terminal import GuakeTerminal

import logging
import posix

log = logging.getLogger(__name__)


class TerminalNotebook(Gtk.Notebook):

    def __init__(self, guake, *args, **kwargs):
        Gtk.Notebook.__init__(self, *args, **kwargs)
        self.guake = guake

    def get_focused_terminal(self):
        for terminal in self.iter_terminals():
            if terminal.has_focus():
                return terminal

    def get_current_terminal(self):
        return self.get_focused_terminal()

    def get_terminals_for_page(self, index):
        page = self.get_nth_page(index)
        return page.get_terminals()

    def get_terminals(self, index):
        terminals = []
        for page in self.iter_pages():
            terminals += page.get_terminals()
        return terminals

    def get_running_fg_processes_count(self):
        fg_proc_count = 0
        for page in self.iter_pages():
            fg_proc_count += self.get_running_fg_processes_count_page(self.page_num(page))
        return fg_proc_count

    def get_running_fg_processes_count_page(self, index):
        total_procs = 0
        for terminal in self.get_terminals_for_page(index):
            fdpty = terminal.get_pty().get_fd()
            term_pid = terminal.pid
            try:
                fgpid = posix.tcgetpgrp(fdpty)
                log.debug("found running pid: %s", fgpid)
                if fgpid not in (-1, term_pid):
                    total_procs += 1
            except OSError:
                log.debug(
                    "Cannot retrieve any pid from terminal %s, looks like it is already dead", index
                )
                return 0
        return total_procs

    def has_page(self):
        return self.get_n_pages() > 0

    def iter_terminals(self):
        for page in self.iter_pages():
            if page is not None:
                for t in page.iter_terminals():
                    yield t

    def iter_tabs(self):
        for page_num in range(self.get_n_pages()):
            yield self.get_tab_label(self.get_nth_page(page_num))

    def iter_pages(self):
        for page_num in range(self.get_n_pages()):
            yield self.get_nth_page(page_num)

    def delete_page(self, page_num, kill=True):
        if page_num >= self.get_n_pages():
            log.debug("Can not delete page %s no such index", page_num)
            return
        for terminal in self.get_terminals_for_page(page_num):
            if kill:
                terminal.kill()
            terminal.destroy()
        self.remove_page(page_num)

    def delete_page_by_label(self, label, kill=True):
        self.delete_page(self.find_tab_index_label(label), True)

    def new_page(self):
        terminal_box = TerminalBox()
        terminal_box.set_terminal(self.guake.setup_new_terminal())
        root_terminal_box = RootTerminalBox(self.guake)
        root_terminal_box.set_child(terminal_box)
        page_num = self.append_page(root_terminal_box, None)
        self.set_tab_reorderable(root_terminal_box, True)
        self.show_all()  # needed to show newly added tabs and pages
        return root_terminal_box, page_num

    def find_tab_index_eventbox(self, eventbox):
        for index, tab_eventbox in enumerate(self.iter_tabs()):
            if eventbox is tab_eventbox:
                return index
        return -1

    def find_tab_index_label(self, label):
        return self.find_tab_index_eventbox(label.get_parent())

    def find_page_index_for_terminal(self, terminal):
        for index, page in enumerate(self.iter_pages()):
            for t in page.iter_terminals():
                if t is terminal:
                    return index
        return -1

    def get_tab_text_index(self, index):
        return self.get_tab_label(self.get_nth_page(index)).get_children()[0].get_text()

    def get_tab_text_page(self, page):
        return self.get_tab_label(page).get_children()[0].get_text()

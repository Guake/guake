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

import logging
import posix

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

log = logging.getLogger(__name__)


class GuakeNotebook(Gtk.Notebook):

    def __init__(self, *args, **kwargs):
        Gtk.Notebook.__init__(self, *args, **kwargs)

        # List of vte.Terminal widgets, it will be useful when needed
        # to get a widget by the current page in self.notebook
        self.term_list = []

        # This is the pid of shells forked by each terminal. Will be
        # used to kill the process when closing a tab
        self.pid_list = []

    def reorder_child(self, child, position):
        """ We should also reorder elements in term_list
        """
        old_pos = self.get_children().index(child)
        self.term_list.insert(position, self.term_list.pop(old_pos))
        super(GuakeNotebook, self).reorder_child(child, position)

    def has_term(self):
        return self.term_list

    def get_tab_count(self):
        return len(self.term_list)

    def get_terminals_for_tab(self, index):
        return [self.term_list[index]]

    def get_current_terminal(self):
        if self.get_current_page() == -1:
            return None
        return self.term_list[self.get_current_page()]

    def get_running_fg_processes(self):
        total_procs = 0
        for page_index in range(self.get_tab_count()):
            total_procs += self.get_running_fg_processes_tab(page_index)
        return total_procs

    def get_running_fg_processes_tab(self, index):
        total_procs = 0
        for terminal in self.get_terminals_for_tab(index):

            fdpty = terminal.get_pty().get_fd()
            term_pid = terminal.pid
            try:
                fgpid = posix.tcgetpgrp(fdpty)
                log.debug("found running pid: %s", fgpid)
                if not (fgpid == -1 or fgpid == term_pid):
                    total_procs += 1
            except OSError:
                log.debug(
                    "Cannot retrieve any pid from terminal %s, looks like it is already dead", index
                )
                return 0
        return total_procs

    def iter_terminals(self):
        for t in self.term_list:
            yield t

    def delete_tab(self, pagepos, kill=True):
        for terminal in self.get_terminals_for_tab(pagepos):
            if kill:
                terminal.kill()

            terminal.destroy()

        self.remove_page(pagepos)
        self.term_list.pop(pagepos)

    def append_tab(self, terminal):
        self.term_list.append(terminal)

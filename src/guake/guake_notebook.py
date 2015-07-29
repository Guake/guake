from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import os
import posix
import signal

from gtk import Notebook
from thread import start_new_thread
from time import sleep

log = logging.getLogger(__name__)


class GuakeNotebook(Notebook):

    def __init__(self, *args, **kwargs):
        Notebook.__init__(self, *args, **kwargs)

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
            fdpty = terminal.get_pty()
            term_pid = terminal.get_pid()
            try:
                fgpid = posix.tcgetpgrp(fdpty)
                if not (fgpid == -1 or fgpid == term_pid):
                    total_procs += 1
            except OSError:
                log.debug("Cannot retrieve any pid from terminal %s, looks like it is already dead",
                          index)
                return 0
        return total_procs

    def iter_terminals(self):
        for t in self.term_list:
            yield t

    def delete_tab(self, pagepos, kill=True):
        for terminal in self.get_terminals_for_tab(pagepos):
            pid = terminal.get_pid()
            if kill:
                start_new_thread(self.delete_shell, (pid,))

            terminal.destroy()

        self.remove_page(pagepos)
        self.term_list.pop(pagepos)

    def delete_shell(self, pid):
        """This function will kill the shell on a tab, trying to send
        a sigterm and if it doesn't work, a sigkill. Between these two
        signals, we have a timeout of 3 seconds, so is recommended to
        call this in another thread. This doesn't change any thing in
        UI, so you can use python's start_new_thread.
        """
        try:
            os.kill(pid, signal.SIGHUP)
        except OSError:
            pass
        num_tries = 30

        while num_tries > 0:
            try:
                # Try to wait for the pid to be closed. If it does not
                # exist anymore, an OSError is raised and we can
                # safely ignore it.
                if os.waitpid(pid, os.WNOHANG)[0] != 0:
                    break
            except OSError:
                break
            sleep(0.1)
            num_tries -= 1

        if num_tries == 0:
            try:
                os.kill(pid, signal.SIGKILL)
                os.waitpid(pid, 0)
            except OSError:
                # if this part of code was reached, means that SIGTERM
                # did the work and SIGKILL wasnt needed.
                pass

    def append_tab(self, terminal):
        self.term_list.append(terminal)

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

from guake.about import AboutDialog
from guake.boxes import DualTerminalBox
from guake.boxes import RootTerminalBox
from guake.boxes import TabLabelEventBox
from guake.boxes import TerminalBox
from guake.callbacks import MenuHideCallback
from guake.callbacks import NotebookScrollCallback
from guake.dialogs import PromptQuitDialog
from guake.menus import mk_notebook_context_menu
from guake.prefs import PrefsDialog

import gi
import os
gi.require_version('Gtk', '3.0')
gi.require_version('Wnck', '3.0')
from gi.repository import GObject
from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import Wnck
from guake.terminal import GuakeTerminal
from locale import gettext as _

import logging
import posix

log = logging.getLogger(__name__)


class TerminalNotebook(Gtk.Notebook):

    def __init__(self, *args, **kwargs):
        Gtk.Notebook.__init__(self, *args, **kwargs)
        self.last_terminal_focused = None

        self.set_name("notebook-teminals")
        self.set_tab_pos(Gtk.PositionType.BOTTOM)
        self.set_property("show-tabs", True)
        self.set_property("enable-popup", False)
        self.set_property("scrollable", True)
        self.set_property("show-border", False)
        self.set_property("visible", True)
        self.set_property("has-focus", True)
        self.set_property("can-focus", True)
        self.set_property("is-focus", True)
        self.set_property("expand", True)

        if GObject.signal_lookup('terminal-spawned', TerminalNotebook) == 0:
            GObject.signal_new(
                'terminal-spawned', TerminalNotebook, GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
                (GObject.TYPE_PYOBJECT, GObject.TYPE_INT)
            )
            GObject.signal_new(
                'page-deleted', TerminalNotebook, GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, ()
            )

        self.scroll_callback = NotebookScrollCallback(self)
        self.add_events(Gdk.EventMask.SCROLL_MASK)
        self.connect('scroll-event', self.scroll_callback.on_scroll)
        self.connect("button-press-event", self.on_button_press, None)

        self.new_page_button = Gtk.Button(
            image=Gtk.Image.new_from_icon_name("tab-new", Gtk.IconSize.MENU), visible=True
        )
        self.new_page_button.connect("clicked", self.on_new_tab)
        self.set_action_widget(self.new_page_button, Gtk.PackType.END)

    def attach_guake(self, guake):
        self.guake = guake

    def on_button_press(self, target, event, user_data):
        if event.button == 3:
            menu = mk_notebook_context_menu(self)
            menu.connect("hide", MenuHideCallback(self.guake.window).on_hide)

            try:
                menu.popup_at_pointer(event)
            except AttributeError:
                # Gtk 3.18 fallback ("'Menu' object has no attribute 'popup_at_pointer'")
                menu.popup(None, None, None, None, event.button, event.time)

        elif event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS and event.button == 1:
            self.new_page_with_focus()

        return False

    def set_last_terminal_focused(self, terminal):
        self.last_terminal_focused = terminal

    def get_focused_terminal(self):
        for terminal in self.iter_terminals():
            if terminal.has_focus():
                return terminal

    def get_current_terminal(self):
        # TODO NOTEBOOK the name of this method should
        # be changed, for now it returns the last focused terminal
        return self.last_terminal_focused

    def get_terminals_for_page(self, index):
        page = self.get_nth_page(index)
        return page.get_terminals()

    def get_terminals(self):
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

    def delete_page(self, page_num, kill=True, prompt=0):
        if page_num >= self.get_n_pages() or page_num < 0:
            log.debug("Can not delete page %s no such index", page_num)
            return
        # TODO NOTEBOOK it would be nice if none of the "ui" stuff
        # (PromptQuitDialog) would be in here
        procs = self.get_running_fg_processes_count_page(page_num)
        if prompt == 2 or (prompt == 1 and procs > 0):
            # TODO NOTEBOOK remove call to guake
            if not PromptQuitDialog(self.guake.window, procs, -1).close_tab():
                return

        for terminal in self.get_terminals_for_page(page_num):
            if kill:
                terminal.kill()
            terminal.destroy()
        self.remove_page(page_num)

    def remove_page(self, page_num):
        super().remove_page(page_num)
        # focusing the first terminal on the previous page
        if self.get_current_page() > -1:
            page = self.get_nth_page(self.get_current_page())
            if page.get_terminals():
                page.get_terminals()[0].grab_focus()
        self.emit('page-deleted')

    def delete_page_by_label(self, label, kill=True, prompt=0):
        self.delete_page(self.find_tab_index_by_label(label), kill, prompt)

    def delete_page_current(self, kill=True, prompt=0):
        self.delete_page(self.get_current_page(), kill, prompt)

    def new_page(self, directory=None):
        terminal = self.terminal_spawn(directory)
        terminal_box = TerminalBox()
        terminal_box.set_terminal(terminal)
        root_terminal_box = RootTerminalBox(self.guake, self)
        root_terminal_box.set_child(terminal_box)
        page_num = self.append_page(root_terminal_box, None)
        self.set_tab_reorderable(root_terminal_box, True)
        self.show_all()  # needed to show newly added tabs and pages
        # this is needed to initially set the last_terminal_focused,
        # one could also call terminal.get_parent().on_terminal_focus()
        self.terminal_attached(terminal)
        return root_terminal_box, page_num, terminal

    def terminal_spawn(self, directory=None):
        terminal = GuakeTerminal(self.guake)
        terminal.grab_focus()
        if not isinstance(directory, str):
            directory = os.environ['HOME']
            try:
                if self.guake.settings.general.get_boolean('open-tab-cwd'):
                    active_terminal = self.get_focused_terminal()
                    directory = os.path.expanduser('~')
                    if active_terminal:
                        directory = active_terminal.get_current_directory()
            except Exception as e:
                pass
        log.info("Spawning new terminal at %s", directory)
        terminal.spawn_sync_pid(directory)
        return terminal

    def terminal_attached(self, terminal):
        terminal.emit("focus", Gtk.DirectionType.TAB_FORWARD)
        self.emit('terminal-spawned', terminal, terminal.pid)

    def new_page_with_focus(self, directory=None):
        box, page_num, terminal = self.new_page(directory)
        self.set_current_page(page_num)
        self.rename_page(page_num, _("Terminal"), False)
        terminal.grab_focus()

    def rename_page(self, page_index, new_text, user_set=False):
        """Rename an already added page by its index. Use user_set to define
        if the rename was triggered by the user (eg. rename dialog) or by
        an update from the vte (eg. vte:window-title-changed)
        """
        page = self.get_nth_page(page_index)
        if not getattr(page, "custom_label_set", False) or user_set:
            old_label = self.get_tab_label(page)
            if isinstance(old_label, TabLabelEventBox):
                old_label.set_text(new_text)
            else:
                label = TabLabelEventBox(self, new_text, self.guake.settings)
                label.add_events(Gdk.EventMask.SCROLL_MASK)
                label.connect('scroll-event', self.scroll_callback.on_scroll)

                self.set_tab_label(page, label)
            if user_set:
                setattr(page, "custom_label_set", new_text != "-")

    def find_tab_index_by_label(self, eventbox):
        for index, tab_eventbox in enumerate(self.iter_tabs()):
            if eventbox is tab_eventbox:
                return index
        return -1

    def find_page_index_by_terminal(self, terminal):
        for index, page in enumerate(self.iter_pages()):
            for t in page.iter_terminals():
                if t is terminal:
                    return index
        return -1

    def get_tab_text_index(self, index):
        return self.get_tab_label(self.get_nth_page(index)).get_text()

    def get_tab_text_page(self, page):
        return self.get_tab_label(page).get_text()

    def on_new_tab(self, user_data):
        self.new_page_with_focus()

    def on_show_preferences(self, user_data):
        self.guake.hide()
        PrefsDialog(self.guake.settings).show()

    def on_show_about(self, user_data):
        self.guake.hide()
        AboutDialog()

    def on_quit(self, user_data):
        self.guake.accel_quit()


class NotebookManager(GObject.Object):

    def __init__(
        self, window, notebook_parent, workspaces_enabled, terminal_spawned_cb, page_deleted_cb
    ):
        GObject.Object.__init__(self)
        GObject.signal_new(
            'notebook-created', self, GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
            (GObject.TYPE_PYOBJECT, GObject.TYPE_INT)
        )
        self.current_notebook = 0
        self.notebooks = {}
        self.window = window
        self.notebook_parent = notebook_parent
        self.terminal_spawned_cb = terminal_spawned_cb
        self.page_deleted_cb = page_deleted_cb
        self.screen = Wnck.Screen.get_default()
        if workspaces_enabled:
            self.screen.connect("active-workspace-changed", self.workspace_changed)

    def workspace_changed(self, screen, previous_workspace):
        self.set_workspace(self.screen.get_active_workspace().get_number())

    def get_notebook(self, workspace_index):
        if not self.has_notebook_for_workspace(workspace_index):
            self.notebooks[workspace_index] = TerminalNotebook()
            self.emit('notebook-created', self.notebooks[workspace_index], workspace_index)
            self.notebooks[workspace_index].connect('terminal-spawned', self.terminal_spawned_cb)
            self.notebooks[workspace_index].connect('page-deleted', self.page_deleted_cb)
            log.info("created fresh notebook for workspace %d", self.current_notebook)

            # add a tab if there is none
            if not self.notebooks[workspace_index].has_page():
                self.notebooks[workspace_index].new_page_with_focus(None)

        return self.notebooks[workspace_index]

    def get_current_notebook(self):
        return self.get_notebook(self.current_notebook)

    def has_notebook_for_workspace(self, workspace_index):
        return workspace_index in self.notebooks.keys()

    def set_workspace(self, index):
        self.notebook_parent.remove(self.get_current_notebook())
        self.current_notebook = index
        log.info("current workspace is %d", self.current_notebook)
        notebook = self.get_current_notebook()
        self.notebook_parent.add(notebook)
        if self.window.get_property('visible') and \
                notebook.last_terminal_focused is not None:
            notebook.last_terminal_focused.grab_focus()

    def get_notebooks(self):
        return self.notebooks

    def get_terminals(self):
        terminals = []
        for k in self.notebooks:
            terminals += self.notebooks[k].get_terminals()
        return terminals

    def iter_terminals(self):
        for k in self.notebooks:
            for t in self.notebooks[k].iter_terminals():
                yield t

    def iter_pages(self):
        for k in self.notebooks:
            for t in self.notebooks[k].iter_pages():
                yield t

    def iter_notebooks(self):
        for k in self.notebooks:
            yield self.notebooks[k]

    def get_n_pages(self):
        n = 0
        for k in self.notebooks:
            n += self.notebooks[k].get_n_pages()
        return n

    def get_n_notebooks(self):
        return len(self.notebooks.keys())

    def get_running_fg_processes_count(self):
        r_fg_c = 0
        for k in self.notebooks:
            r_fg_c += self.notebooks[k].get_running_fg_processes_count()
        return r_fg_c

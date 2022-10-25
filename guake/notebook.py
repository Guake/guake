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
from guake.boxes import RootTerminalBox
from guake.boxes import TabLabelEventBox
from guake.boxes import TerminalBox
from guake.callbacks import MenuHideCallback
from guake.callbacks import NotebookScrollCallback
from guake.dialogs import PromptQuitDialog
from guake.globals import PROMPT_ALWAYS
from guake.globals import PROMPT_PROCESSES
from guake.menus import mk_notebook_context_menu
from guake.prefs import PrefsDialog
from guake.utils import HidePrevention
from guake.utils import gdk_is_x11_display
from guake.utils import get_process_name
from guake.utils import save_tabs_when_changed

import gi
import os

gi.require_version("Gtk", "3.0")
gi.require_version("Wnck", "3.0")
from gi.repository import GObject
from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import Wnck
from guake.terminal import GuakeTerminal

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

        if GObject.signal_lookup("terminal-spawned", TerminalNotebook) == 0:
            GObject.signal_new(
                "terminal-spawned",
                TerminalNotebook,
                GObject.SignalFlags.RUN_LAST,
                GObject.TYPE_NONE,
                (GObject.TYPE_PYOBJECT, GObject.TYPE_INT),
            )
            GObject.signal_new(
                "page-deleted",
                TerminalNotebook,
                GObject.SignalFlags.RUN_LAST,
                GObject.TYPE_NONE,
                (),
            )

        self.scroll_callback = NotebookScrollCallback(self)
        self.add_events(Gdk.EventMask.SCROLL_MASK)
        self.connect("scroll-event", self.scroll_callback.on_scroll)
        self.notebook_on_button_press_id = self.connect(
            "button-press-event", self.on_button_press, None
        )

        # Action box
        self.pin_button = Gtk.ToggleButton(
            image=Gtk.Image.new_from_icon_name("view-pin-symbolic", Gtk.IconSize.MENU),
            visible=False,
        )
        self.pin_button.connect("clicked", self.on_pin_clicked)
        self.new_page_button = Gtk.Button(
            image=Gtk.Image.new_from_icon_name("tab-new-symbolic", Gtk.IconSize.MENU),
            visible=True,
        )
        self.new_page_button.connect("clicked", self.on_new_tab)

        self.tab_selection_button = Gtk.Button(
            image=Gtk.Image.new_from_icon_name("pan-down-symbolic", Gtk.IconSize.MENU),
            visible=True,
        )
        self.popover = Gtk.Popover()
        self.popover_window = None
        self.tab_selection_button.connect("clicked", self.on_tab_selection)

        self.action_box = Gtk.Box(visible=True)
        self.action_box.pack_start(self.pin_button, 0, 0, 0)
        self.action_box.pack_start(self.new_page_button, 0, 0, 0)
        self.action_box.pack_start(self.tab_selection_button, 0, 0, 0)
        self.set_action_widget(self.action_box, Gtk.PackType.END)

    def attach_guake(self, guake):
        self.guake = guake

        self.guake.settings.general.onChangedValue("window-losefocus", self.on_lose_focus_toggled)
        self.pin_button.set_visible(self.guake.settings.general.get_boolean("window-losefocus"))

    def on_button_press(self, target, event, user_data):
        if event.button == 3:
            menu = mk_notebook_context_menu(self)
            menu.connect("hide", MenuHideCallback(self.guake.window).on_hide)

            try:
                menu.popup_at_pointer(event)
            except AttributeError:
                # Gtk 3.18 fallback ("'Menu' object has no attribute 'popup_at_pointer'")
                menu.popup(None, None, None, None, event.button, event.time)
        elif (
            event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS
            and event.button == 1
            and event.window.get_height() < 60
        ):
            # event.window.get_height() reports the height of the clicked frame
            self.new_page_with_focus()

        return False

    def on_pin_clicked(self, user_data=None):
        hide_prevention = HidePrevention(self.guake.window)
        if self.pin_button.get_active():
            hide_prevention.prevent()
        else:
            hide_prevention.allow()

    def on_lose_focus_toggled(self, settings, key, user_data=None):
        self.pin_button.set_visible(settings.get_boolean(key))

    @save_tabs_when_changed
    def on_new_tab(self, user_data):
        self.new_page_with_focus()

    def on_tab_selection(self, user_data):
        """Construct the tab selection popover

        Since we did not use Gtk.ListStore to store tab information, we will construct the
        tab selection popover content each time when user click them.
        """

        # Remove previous window
        if self.popover_window:
            self.popover.remove(self.popover_window)

        # This makes the list's background transparent
        # ref: epiphany
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(
            b"#popover-window list { border-style: none; background-color: transparent; }"
        )
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        # Construct popover properties
        BOX_HEIGHT = 30
        LISTBOX_MARGIN = 12
        self.popover_window = Gtk.ScrolledWindow(name="popover-window")
        self.popover_listbox = Gtk.ListBox()
        self.popover_listbox.set_property("margin", LISTBOX_MARGIN)
        self.popover_window.add_with_viewport(self.popover_listbox)

        max_height = (
            self.guake.window.get_allocation().height - BOX_HEIGHT
            if self.guake
            else BOX_HEIGHT * 10
        )
        height = BOX_HEIGHT * self.get_n_pages() + LISTBOX_MARGIN * 4
        self.popover_window.set_min_content_height(min(max_height, height))
        self.popover_window.set_min_content_width(325)
        self.popover.add(self.popover_window)

        # Construct content
        current_term = self.get_current_terminal()
        selected_row = 0
        for i in range(self.get_n_pages()):
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            box.set_size_request(200, BOX_HEIGHT)
            label = Gtk.Label(self.get_tab_text_index(i))
            label.set_xalign(0.0)
            box.pack_start(label, 0, 0, 5)
            row.add(box)
            setattr(row, "page_index", i)
            self.popover_listbox.add(row)
            if current_term in self.get_terminals_for_page(i):
                self.popover_listbox.select_row(row)
                selected_row = i

        # Signal
        self.popover_listbox.connect("row-activated", self.on_popover_tab_select)

        # Show popup
        self.popover.set_position(Gtk.PositionType.TOP)
        self.popover.set_relative_to(user_data)
        self.popover.show_all()
        try:
            # For GTK >= 3.22
            self.popover.popup()
        except AttributeError:
            pass

        # Adjust scrollor
        while Gtk.events_pending():
            Gtk.main_iteration()

        if selected_row:
            adj = self.popover_window.get_vadjustment()
            v = adj.get_upper() - adj.get_page_size()
            part = v / self.get_n_pages()
            adj.set_value(part * (selected_row + 1))

    def on_popover_tab_select(self, list_box, row):
        page_index = getattr(row, "page_index", -1)
        if page_index != -1:
            self.set_current_page(page_index)
            self.get_terminals_for_page(page_index)[0].grab_focus()

    def set_tabbar_visible(self, v):
        self.set_property("show-tabs", v)

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

    def get_running_fg_processes(self):
        processes = []
        for page in self.iter_pages():
            processes += self.get_running_fg_processes_page(page)
        return processes

    def get_running_fg_processes_page(self, page):
        processes = []
        for terminal in page.get_terminals():
            pty = terminal.get_pty()
            if not pty:
                continue
            fdpty = pty.get_fd()
            term_pid = terminal.pid
            try:
                fgpid = posix.tcgetpgrp(fdpty)
                log.debug("found running pid: %s", fgpid)
                if fgpid not in (-1, term_pid):
                    processes.append((fgpid, get_process_name(fgpid)))
            except OSError:
                log.debug(
                    "Cannot retrieve any pid from terminal %s, looks like it is already dead",
                    terminal,
                )
        return processes

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
        log.debug("Deleting page index %s", page_num)
        if page_num >= self.get_n_pages() or page_num < 0:
            log.error("Can not delete page %s no such index", page_num)
            return

        page = self.get_nth_page(page_num)
        # TODO NOTEBOOK it would be nice if none of the "ui" stuff
        # (PromptQuitDialog) would be in here
        procs = self.get_running_fg_processes_page(page)
        if prompt == PROMPT_ALWAYS or (prompt == PROMPT_PROCESSES and procs):
            # TODO NOTEBOOK remove call to guake
            if not PromptQuitDialog(self.guake.window, procs, -1, None).close_tab():
                return

        for terminal in page.get_terminals():
            if kill:
                terminal.kill()
            terminal.destroy()

        if self.get_nth_page(page_num) is page:
            # NOTE: GitHub issue #1438
            # Previous line `terminal.destroy()` will finally called `on_terminal_exited`,
            # and called `RootTerminalBox.remove_dead_child`, then called `remove_page`.
            #
            # But in some cases (e.g. #1438), it will not remove the page by
            # `terminal.destory() chain`.
            #
            # Check this by compare same page_num page with previous saved page instance,
            # and remove the page if it really didn't remove it.
            self.remove_page(page_num)

    @save_tabs_when_changed
    def remove_page(self, page_num):
        super().remove_page(page_num)
        # focusing the first terminal on the previous page
        if self.get_current_page() > -1:
            page = self.get_nth_page(self.get_current_page())
            if page.get_terminals():
                page.get_terminals()[0].grab_focus()

        self.hide_tabbar_if_one_tab()
        self.emit("page-deleted")

    def delete_page_by_label(self, label, kill=True, prompt=0):
        self.delete_page(self.find_tab_index_by_label(label), kill, prompt)

    def delete_page_current(self, kill=True, prompt=0):
        self.delete_page(self.get_current_page(), kill, prompt)

    def new_page(self, directory=None, position=None, empty=False, open_tab_cwd=False):
        terminal_box = TerminalBox()
        if empty:
            terminal = None
        else:
            terminal = self.terminal_spawn(directory, open_tab_cwd)
            terminal_box.set_terminal(terminal)
        root_terminal_box = RootTerminalBox(self.guake, self)
        root_terminal_box.set_child(terminal_box)
        page_num = self.insert_page(
            root_terminal_box, None, position if position is not None else -1
        )
        self.set_tab_reorderable(root_terminal_box, True)
        self.show_all()  # needed to show newly added tabs and pages
        # this is needed because self.window.show_all() results in showing every
        # thing which includes the scrollbar too
        self.guake.settings.general.triggerOnChangedValue(
            self.guake.settings.general, "use-scrollbar"
        )
        # this is needed to initially set the last_terminal_focused,
        # one could also call terminal.get_parent().on_terminal_focus()
        if not empty:
            self.terminal_attached(terminal)
        self.hide_tabbar_if_one_tab()

        if self.guake:
            # Attack background image draw callback to root terminal box
            root_terminal_box.connect_after("draw", self.guake.background_image_manager.draw)
        return root_terminal_box, page_num, terminal

    def hide_tabbar_if_one_tab(self):
        """Hide the tab bar if hide-tabs-if-one-tab is true and there is only one
        notebook page"""
        if self.guake.settings.general.get_boolean("window-tabbar"):
            if self.guake.settings.general.get_boolean("hide-tabs-if-one-tab"):
                self.set_property("show-tabs", self.get_n_pages() != 1)
            else:
                self.set_property("show-tabs", True)

    def terminal_spawn(self, directory=None, open_tab_cwd=False):
        terminal = GuakeTerminal(self.guake)
        terminal.grab_focus()
        terminal.connect(
            "key-press-event",
            lambda x, y: self.guake.accel_group.activate(x, y) if self.guake.accel_group else False,
        )
        if not isinstance(directory, str):
            directory = os.environ["HOME"]
            try:
                if self.guake.settings.general.get_boolean("open-tab-cwd") or open_tab_cwd:
                    # Do last focused terminal still alive?
                    active_terminal = self.get_current_terminal()
                    if not active_terminal:
                        # If not alive, can we get any focused terminal?
                        active_terminal = self.get_focused_terminal()
                    directory = os.path.expanduser("~")
                    if active_terminal:
                        # If found, we will use its directory as new terminal's directory
                        directory = active_terminal.get_current_directory()
            except BaseException:
                pass
        log.info("Spawning new terminal at %s", directory)
        terminal.spawn_sync_pid(directory)
        return terminal

    def terminal_attached(self, terminal):
        terminal.emit("focus", Gtk.DirectionType.TAB_FORWARD)
        self.emit("terminal-spawned", terminal, terminal.pid)

    def new_page_with_focus(
        self,
        directory=None,
        label=None,
        user_set=False,
        position=None,
        empty=False,
        open_tab_cwd=False,
    ):
        box, page_num, terminal = self.new_page(
            directory, position=position, empty=empty, open_tab_cwd=open_tab_cwd
        )
        self.set_current_page(page_num)
        if not label:
            self.rename_page(page_num, self.guake.compute_tab_title(terminal), False)
        else:
            self.rename_page(page_num, label, user_set)
        if terminal is not None:
            terminal.grab_focus()
        return box, page_num, terminal

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
                label.connect("scroll-event", self.scroll_callback.on_scroll)

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

    def on_show_preferences(self, user_data):
        self.guake.hide()
        PrefsDialog(self.guake.settings).show()

    def on_show_about(self, user_data):
        self.guake.hide()
        AboutDialog()

    def on_quit(self, user_data):
        self.guake.accel_quit()

    def on_save_tabs(self, user_data):
        self.guake.save_tabs()

    def on_restore_tabs(self, user_data):
        self.guake.restore_tabs()

    def on_restore_tabs_with_dialog(self, user_data):
        dialog = Gtk.MessageDialog(
            parent=self.guake.window,
            flags=Gtk.DialogFlags.MODAL,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            message_format=_(
                "You are going to restore *all* the tabs!\n"
                "which means all your terminals & pages "
                "will be replaced.\n\nDo you want to continue?"
            ),
        )
        dialog.connect("response", self.restore_tabs_dialog_response)
        dialog.show()

    def restore_tabs_dialog_response(self, widget, response_id):
        widget.destroy()
        if response_id == Gtk.ResponseType.OK:
            self.guake.restore_tabs()


class NotebookManager(GObject.Object):
    def __init__(
        self,
        window,
        notebook_parent,
        workspaces_enabled,
        terminal_spawned_cb,
        page_deleted_cb,
    ):
        GObject.Object.__init__(self)
        if not GObject.signal_lookup("notebook-created", self):
            GObject.signal_new(
                "notebook-created",
                self,
                GObject.SignalFlags.RUN_LAST,
                GObject.TYPE_NONE,
                (GObject.TYPE_PYOBJECT, GObject.TYPE_INT),
            )
        self.current_notebook = 0
        self.notebooks = {}
        self.window = window
        self.notebook_parent = notebook_parent
        self.terminal_spawned_cb = terminal_spawned_cb
        self.page_deleted_cb = page_deleted_cb
        if workspaces_enabled and gdk_is_x11_display(Gdk.Display.get_default()):
            # NOTE: Wnck didn't support non-X11 display backend, so we need to check if the display
            #       is X11 or not, if not, it will not able to enable workspace-specific-tab-sets
            #
            # TODO: Is there anyway to support this in non-X11 display backend?
            self.screen = Wnck.Screen.get_default()
            self.screen.connect("active-workspace-changed", self.__workspace_changed_cb)

    def __workspace_changed_cb(self, screen, previous_workspace):
        self.set_workspace(self.screen.get_active_workspace().get_number())

    def get_notebook(self, workspace_index: int):
        if not self.has_notebook_for_workspace(workspace_index):
            self.notebooks[workspace_index] = TerminalNotebook()
            self.emit("notebook-created", self.notebooks[workspace_index], workspace_index)
            self.notebooks[workspace_index].connect("terminal-spawned", self.terminal_spawned_cb)
            self.notebooks[workspace_index].connect("page-deleted", self.page_deleted_cb)
            log.info("created fresh notebook for workspace %d", self.current_notebook)

            # add a tab if there is none
            if not self.notebooks[workspace_index].has_page():
                self.notebooks[workspace_index].new_page_with_focus(None)

        return self.notebooks[workspace_index]

    def get_current_notebook(self):
        return self.get_notebook(self.current_notebook)

    def has_notebook_for_workspace(self, workspace_index):
        return workspace_index in self.notebooks

    def set_workspace(self, index: int):
        self.notebook_parent.remove(self.get_current_notebook())
        self.current_notebook = index
        log.info("current workspace is %d", self.current_notebook)
        notebook = self.get_current_notebook()
        self.notebook_parent.add(notebook)
        if self.window.get_property("visible") and notebook.last_terminal_focused is not None:
            notebook.last_terminal_focused.grab_focus()

        # Restore pending page terminal split
        notebook.guake.restore_pending_terminal_split()

        # Restore config to workspace
        notebook.guake.load_config()

    def set_notebooks_tabbar_visible(self, v):
        for nb in self.iter_notebooks():
            nb.set_tabbar_visible(v)

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

    def get_terminal_by_uuid(self, terminal_uuid):
        for t in self.iter_terminals():
            if t.uuid == terminal_uuid:
                return t
        return None

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

    def get_running_fg_processes(self):
        processes = []
        for k in self.notebooks:
            processes += self.notebooks[k].get_running_fg_processes()
        return processes

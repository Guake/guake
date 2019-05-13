import logging
import time

from locale import gettext as _

import gi
gi.require_version('Vte', '2.91')  # vte-0.42
gi.require_version('Gtk', '3.0')
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import Vte

from guake.callbacks import MenuHideCallback
from guake.callbacks import TerminalContextMenuCallbacks
from guake.dialogs import RenameDialog
from guake.menus import mk_tab_context_menu
from guake.menus import mk_terminal_context_menu
from guake.utils import HidePrevention
from guake.utils import TabNameUtils
from guake.utils import get_server_time
from guake.utils import save_tabs_when_changed

log = logging.getLogger(__name__)

# TODO remove calls to guake


class TerminalHolder():
    UP = 0
    DOWN = 1
    RIGHT = 2
    LEFT = 3

    def get_terminals(self):
        pass

    def iter_terminals(self):
        pass

    def replace_child(self, old, new):
        pass

    def get_guake(self):
        pass

    def get_window(self):
        pass

    def get_settings(self):
        pass

    def get_root_box(self):
        pass

    def get_notebook(self):
        pass

    def remove_dead_child(self, child):
        pass


class RootTerminalBox(Gtk.Overlay, TerminalHolder):

    def __init__(self, guake, parent_notebook):
        super().__init__()
        self.guake = guake
        self.notebook = parent_notebook
        self.child = None
        self.last_terminal_focused = None

        self.searchstring = None
        self.searchre = None
        self._add_search_box()

    def _add_search_box(self):
        """ --------------------------------------|
            | Revealer                            |
            | |-----------------------------------|
            | | Frame                             |
            | | |---------------------------------|
            | | | HBox                            |
            | | | |---| |-------| |----| |------| |
            | | | | x | | Entry | |Prev| | Next | |
            | | | |---| |-------| |----| |------| |
            --------------------------------------|
        """
        self.search_revealer = Gtk.Revealer()
        self.search_frame = Gtk.Frame(name='search-frame')
        self.search_box = Gtk.HBox()

        # Search
        self.search_close_btn = Gtk.Button()
        self.search_close_btn.set_can_focus(False)
        close_icon = Gio.ThemedIcon(name='window-close-symbolic')
        close_image = Gtk.Image.new_from_gicon(close_icon, Gtk.IconSize.BUTTON)
        self.search_close_btn.set_image(close_image)
        self.search_entry = Gtk.SearchEntry()
        self.search_prev_btn = Gtk.Button()
        self.search_prev_btn.set_can_focus(False)
        prev_icon = Gio.ThemedIcon(name='go-up-symbolic')
        prev_image = Gtk.Image.new_from_gicon(prev_icon, Gtk.IconSize.BUTTON)
        self.search_prev_btn.set_image(prev_image)
        self.search_next_btn = Gtk.Button()
        self.search_next_btn.set_can_focus(False)
        next_icon = Gio.ThemedIcon(name='go-down-symbolic')
        next_image = Gtk.Image.new_from_gicon(next_icon, Gtk.IconSize.BUTTON)
        self.search_next_btn.set_image(next_image)

        # Pack into box
        self.search_box.pack_start(self.search_close_btn, False, False, 0)
        self.search_box.pack_start(self.search_entry, False, False, 0)
        self.search_box.pack_start(self.search_prev_btn, False, False, 0)
        self.search_box.pack_start(self.search_next_btn, False, False, 0)

        # Add into frame
        self.search_frame.add(self.search_box)

        # Frame
        self.search_frame.set_margin_end(12)
        self.search_frame.get_style_context().add_class('background')
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(
            b'#search-frame border {'
            b'    padding: 5px 5px 5px 5px;'
            b'    border: none;'
            b'}'
        )
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Add to revealer
        self.search_revealer.add(self.search_frame)
        self.search_revealer.set_transition_duration(500)
        self.search_revealer.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)
        self.search_revealer.set_valign(Gtk.Align.END)
        self.search_revealer.set_halign(Gtk.Align.END)

        # Welcome to the overlay
        self.add_overlay(self.search_revealer)

        # Events
        self.search_entry.connect('key-press-event', self.on_search_entry_keypress)
        self.search_entry.connect('changed', self.set_search)
        self.search_entry.connect('activate', self.do_search)
        self.search_entry.connect('focus-in-event', self.on_search_entry_focus_in)
        self.search_entry.connect('focus-out-event', self.on_search_entry_focus_out)
        self.search_next_btn.connect('clicked', self.on_search_next_clicked)
        self.search_prev_btn.connect('clicked', self.on_search_prev_clicked)
        self.search_close_btn.connect('clicked', self.close_search_box)
        self.search_prev = True

    def get_terminals(self):
        return self.get_child().get_terminals()

    def iter_terminals(self):
        if self.get_child() is not None:
            for t in self.get_child().iter_terminals():
                yield t

    def replace_child(self, old, new):
        self.remove(old)
        self.set_child(new)

    def set_child(self, terminal_holder):
        if isinstance(terminal_holder, TerminalHolder) or True:
            self.child = terminal_holder
            self.add(self.child)
        else:
            print(
                "wtf, what have you added to me???"
                "(RootTerminalBox.add(%s))" % type(terminal_holder)
            )

    def focus():
        if self.get_terminals():
            self.get_terminals()[0].grab_focus()

    def get_child(self):
        return self.child

    def get_guake(self):
        return self.guake

    def get_window(self):
        return self.guake.window

    def get_settings(self):
        return self.guake.settings

    def get_root_box(self):
        return self

    def save_box_layout(self, box, panes: list):
        """Save box layout with pre-order traversal, it should result `panes` with
           a full binary tree in list.
        """
        if not box:
            panes.append({'type': None, 'directory': None})
            return
        if isinstance(box, DualTerminalBox):
            btype = 'dual' + ('_h' if box.orient is DualTerminalBox.ORIENT_V else '_v')
            panes.append({'type': btype, 'directory': None})
            self.save_box_layout(box.get_child1(), panes)
            self.save_box_layout(box.get_child2(), panes)
        elif isinstance(box, TerminalBox):
            btype = 'term'
            directory = box.terminal.get_current_directory()
            panes.append({'type': btype, 'directory': directory})

    def restore_box_layout(self, box, panes: list):
        """Restore box layout by `panes`
        """
        if not panes or not isinstance(panes, list):
            return
        if not box or not isinstance(box, TerminalBox):
            # Should only called on TerminalBox
            return

        cur = panes.pop(0)
        if cur['type'].startswith('dual'):
            while True:
                if self.guake:
                    # If Guake are not visible, we should pending the restore, then do the
                    # restore when Guake is visible again.
                    #
                    # Otherwise we will stuck in the infinite loop, since new DualTerminalBox
                    # cannot get any allocation when Guake is invisible
                    if (
                        not self.guake.window.get_property('visible') or self.get_notebook() is
                        not self.guake.notebook_manager.get_current_notebook()
                    ):
                        panes.insert(0, cur)
                        self.guake._failed_restore_page_split.append((self, box, panes))
                        return

                # UI didn't update, wait for it
                alloc = box.get_allocation()
                if alloc.width == 1 and alloc.height == 1:
                    time.sleep(.01)
                else:
                    break

                # Waiting for UI update..
                while Gtk.events_pending():
                    Gtk.main_iteration()

            if cur['type'].endswith('v'):
                box = box.split_v()
            else:
                box = box.split_h()
            self.restore_box_layout(box.get_child1(), panes)
            self.restore_box_layout(box.get_child2(), panes)
        else:
            if box.terminal:
                term = box.terminal
                # Remove signal handler from terminal
                for i in term.handler_ids:
                    term.disconnect(i)
                term.handler_ids = []
                box.remove(box.scroll)
                box.remove(term)
                box.unset_terminal()

            # Replace term in the TerminalBox
            term = self.get_notebook().terminal_spawn(cur['directory'])
            box.set_terminal(term)
            self.get_notebook().terminal_attached(term)

    def set_last_terminal_focused(self, terminal):
        self.last_terminal_focused = terminal
        self.get_notebook().set_last_terminal_focused(terminal)

    def get_last_terminal_focused(self, terminal):
        return self.last_terminal_focused

    def get_notebook(self):
        return self.notebook

    def remove_dead_child(self, child):
        page_num = self.get_notebook().page_num(self)
        self.get_notebook().remove_page(page_num)

    def move_focus(self, direction, fromChild):
        pass

    def block_notebook_on_button_press_id(self):
        GObject.signal_handler_block(
            self.get_notebook(),
            self.get_notebook().notebook_on_button_press_id
        )

    def unblock_notebook_on_button_press_id(self):
        GObject.signal_handler_unblock(
            self.get_notebook(),
            self.get_notebook().notebook_on_button_press_id
        )

    def show_search_box(self):
        if not self.search_revealer.get_reveal_child():
            self.search_revealer.set_reveal_child(True)
            # XXX: Mestery line to avoid Gtk-CRITICAL stuff
            # (guake:22694): Gtk-CRITICAL **: 18:04:57.345:
            # gtk_widget_event: assertion 'WIDGET_REALIZED_FOR_EVENT (widget, event)' failed
            self.search_entry.realize()
            self.search_entry.grab_focus()

    def hide_search_box(self):
        if self.search_revealer.get_reveal_child():
            self.search_revealer.set_reveal_child(False)
            self.last_terminal_focused.grab_focus()
            self.last_terminal_focused.unselect_all()

    def close_search_box(self, event):
        self.hide_search_box()

    def on_search_entry_focus_in(self, event, user_data):
        self.block_notebook_on_button_press_id()

    def on_search_entry_focus_out(self, event, user_data):
        self.unblock_notebook_on_button_press_id()

    def on_search_prev_clicked(self, widget):
        term = self.last_terminal_focused
        result = term.search_find_previous()
        if not result:
            term.search_find_previous()

    def on_search_next_clicked(self, widget):
        term = self.last_terminal_focused
        result = term.search_find_next()
        if not result:
            term.search_find_next()

    def on_search_entry_keypress(self, widget, event):
        key = Gdk.keyval_name(event.keyval)
        if key == 'Escape':
            self.hide_search_box()
        elif key == 'Return':
            # Combine with Shift?
            if event.state & Gdk.ModifierType.SHIFT_MASK:
                self.search_prev = False
                self.do_search(None)
            else:
                self.search_prev = True

    def reset_term_search(self, term):
        term.search_set_gregex(GLib.Regex('', 0, 0), 0)
        term.search_find_next()

    def set_search(self, widget):
        term = self.last_terminal_focused
        text = self.search_entry.get_text()
        if not text:
            self.reset_term_search(term)
            return

        if text != self.searchstring:
            self.reset_term_search(term)

            # Set search regex on term
            self.searchstring = text
            self.searchre = GLib.Regex(text, 0, 0)
            term.search_set_gregex(self.searchre, 0)

        self.do_search(None)

    def do_search(self, widget):
        if self.search_prev:
            self.on_search_prev_clicked(None)
        else:
            self.on_search_next_clicked(None)


class TerminalBox(Gtk.Box, TerminalHolder):

    """A box to group the terminal and a scrollbar.
    """

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.terminal = None

    def set_terminal(self, terminal):
        """Packs the terminal widget.
        """
        if self.terminal is not None:
            raise RuntimeError("TerminalBox: terminal already set")
        self.terminal = terminal
        self.terminal.handler_ids.append(
            self.terminal.connect("grab-focus", self.on_terminal_focus)
        )
        self.terminal.handler_ids.append(
            self.terminal.connect("button-press-event", self.on_button_press, None)
        )
        self.terminal.handler_ids.append(
            self.terminal.connect('child-exited', self.on_terminal_exited)
        )
        self.pack_start(self.terminal, True, True, 0)
        self.terminal.show()
        self.add_scroll_bar()

    def add_scroll_bar(self):
        """Packs the scrollbar.
        """
        adj = self.terminal.get_vadjustment()
        self.scroll = Gtk.VScrollbar(adj)
        self.scroll.show()
        self.pack_start(self.scroll, False, False, 0)

        self.terminal.handler_ids.append(
            self.terminal.connect('scroll-event', self.__scroll_event_cb)
        )

    def __scroll_event_cb(self, widget, event):
        # Adjust scrolling speed when adding "shift" or "shift + ctrl"
        adj = self.scroll.get_adjustment()
        page_size = adj.get_page_size()
        if (
            event.get_state() & Gdk.ModifierType.SHIFT_MASK and
            event.get_state() & Gdk.ModifierType.CONTROL_MASK
        ):
            # Ctrl + Shift + Mouse Scroll (4 pages)
            adj.set_page_increment(page_size * 40)
        elif event.get_state() & Gdk.ModifierType.SHIFT_MASK:
            # Shift + Mouse Scroll (1 page)
            adj.set_page_increment(page_size * 10)
        else:
            # Mouse Scroll
            adj.set_page_increment(page_size)

    def get_terminal(self):
        return self.terminal

    def get_terminals(self):
        if self.terminal is not None:
            return [self.terminal]
        return []

    def iter_terminals(self):
        if self.terminal is not None:
            yield self.terminal

    def replace_child(self, old, new):
        print("why would you call this on me?")
        pass

    def unset_terminal(self, *args):
        self.terminal = None

    def split_h(self):
        return self.split(DualTerminalBox.ORIENT_V)

    def split_v(self):
        return self.split(DualTerminalBox.ORIENT_H)

    def split(self, orientation):
        notebook = self.get_notebook()
        parent = self.get_parent()  # RootTerminalBox

        if orientation == DualTerminalBox.ORIENT_H:
            position = self.get_allocation().width / 2
        else:
            position = self.get_allocation().height / 2

        terminal_box = TerminalBox()
        terminal = notebook.terminal_spawn()
        terminal_box.set_terminal(terminal)
        dual_terminal_box = DualTerminalBox(orientation)
        dual_terminal_box.set_position(position)
        parent.replace_child(self, dual_terminal_box)
        dual_terminal_box.set_child_first(self)
        dual_terminal_box.set_child_second(terminal_box)
        dual_terminal_box.show()
        dual_terminal_box.show_all()
        notebook.terminal_attached(terminal)

        return dual_terminal_box

    def get_guake(self):
        return self.get_parent().get_guake()

    def get_window(self):
        return self.get_parent().get_window()

    def get_settings(self):
        return self.get_parent().get_settings()

    def get_root_box(self):
        return self.get_parent().get_root_box()

    def get_notebook(self):
        return self.get_parent().get_notebook()

    def remove_dead_child(self, child):
        print("Can't do, have no \"child\"")

    def on_terminal_focus(self, *args):
        self.get_root_box().set_last_terminal_focused(self.terminal)

    def on_terminal_exited(self, terminal, status):
        if not self.get_parent():
            return
        self.get_parent().remove_dead_child(self)

    def on_button_press(self, target, event, user_data):
        if event.button == 3:
            # First send to background process if handled, do nothing else
            if not event.get_state() & Gdk.ModifierType.SHIFT_MASK:
                if Vte.Terminal.do_button_press_event(self.terminal, event):
                    return True

            menu = mk_terminal_context_menu(
                self.terminal, self.get_window(), self.get_settings(),
                TerminalContextMenuCallbacks(
                    self.terminal, self.get_window(), self.get_settings(),
                    self.get_root_box().get_notebook()
                )
            )
            menu.connect("hide", MenuHideCallback(self.get_window()).on_hide)
            HidePrevention(self.get_window()).prevent()
            try:
                menu.popup_at_pointer(event)
            except AttributeError:
                # Gtk 3.18 fallback ("'Menu' object has no attribute 'popup_at_pointer'")
                menu.popup(None, None, None, None, event.button, event.time)
            self.terminal.grab_focus()
            return True
        self.terminal.grab_focus()
        return False


class DualTerminalBox(Gtk.Paned, TerminalHolder):

    ORIENT_H = 0
    ORIENT_V = 1

    def __init__(self, orientation):
        super().__init__()

        self.orient = orientation
        if orientation is DualTerminalBox.ORIENT_H:
            self.set_orientation(orientation=Gtk.Orientation.HORIZONTAL)
        else:
            self.set_orientation(orientation=Gtk.Orientation.VERTICAL)

    def set_child_first(self, terminal_holder):
        if isinstance(terminal_holder, TerminalHolder):
            self.add1(terminal_holder)
        else:
            print("wtf, what have you added to me???")

    def set_child_second(self, terminal_holder):
        if isinstance(terminal_holder, TerminalHolder):
            self.add2(terminal_holder)
        else:
            print("wtf, what have you added to me???")

    def get_terminals(self):
        return self.get_child1().get_terminals() + self.get_child2().get_terminals()

    def iter_terminals(self):
        for t in self.get_child1().iter_terminals():
            yield t
        for t in self.get_child2().iter_terminals():
            yield t

    def replace_child(self, old, new):
        if self.get_child1() is old:
            self.remove(old)
            self.set_child_first(new)
        elif self.get_child2() is old:
            self.remove(old)
            self.set_child_second(new)
        else:
            print("I have never seen this widget!")

    def get_guake(self):
        return self.get_parent().get_guake()

    def get_window(self):
        return self.get_parent().get_window()

    def get_settings(self):
        return self.get_parent().get_settings()

    def get_root_box(self):
        return self.get_parent().get_root_box()

    def get_notebook(self):
        return self.get_parent().get_notebook()

    def grab_box_terminal_focus(self, box):
        if isinstance(box, DualTerminalBox):
            next(box.iter_terminals()).grab_focus()
        else:
            box.get_terminal().grab_focus()

    def remove_dead_child(self, child):
        if self.get_child1() is child:
            living_child = self.get_child2()
            self.remove(living_child)
            self.get_parent().replace_child(self, living_child)
            self.grab_box_terminal_focus(living_child)
        elif self.get_child2() is child:
            living_child = self.get_child1()
            self.remove(living_child)
            self.get_parent().replace_child(self, living_child)
            self.grab_box_terminal_focus(living_child)
        else:
            print("I have never seen this widget!")


class TabLabelEventBox(Gtk.EventBox):

    def __init__(self, notebook, text, settings):
        super().__init__()
        self.notebook = notebook
        self.box = Gtk.Box(Gtk.Orientation.HORIZONTAL, 0, visible=True)
        self.label = Gtk.Label(text, visible=True)
        self.close_button = Gtk.Button(
            image=Gtk.Image.new_from_icon_name("window-close", Gtk.IconSize.MENU),
            relief=Gtk.ReliefStyle.NONE
        )
        self.close_button.connect('clicked', self.on_close)
        settings.general.bind(
            'tab-close-buttons', self.close_button, 'visible', Gio.SettingsBindFlags.GET
        )
        self.box.pack_start(self.label, True, True, 0)
        self.box.pack_end(self.close_button, False, False, 0)
        self.add(self.box)
        self.connect("button-press-event", self.on_button_press, self.label)

    def set_text(self, text):
        self.label.set_text(text)

    def get_text(self):
        return self.label.get_text()

    def grab_focus_on_last_focused_terminal(self):
        server_time = get_server_time(self.notebook.guake.window)
        self.notebook.guake.window.get_window().focus(server_time)
        self.notebook.get_current_terminal().grab_focus()

    def on_button_press(self, target, event, user_data):
        if event.button == 3:
            menu = mk_tab_context_menu(self)
            menu.connect("hide", MenuHideCallback(self.get_toplevel()).on_hide)
            HidePrevention(self.get_toplevel()).prevent()
            try:
                menu.popup_at_pointer(event)
            except AttributeError:
                # Gtk 3.18 fallback ("'Menu' object has no attribute 'popup_at_pointer'")
                menu.popup(None, None, None, None, event.button, event.get_time())
            return True
        if event.button == 2:
            prompt_cfg = self.notebook.guake.settings.general.get_int('prompt-on-close-tab')
            self.notebook.delete_page_by_label(self, prompt=prompt_cfg)
            return True
        if event.button == 1 and event.type == Gdk.EventType._2BUTTON_PRESS:
            self.on_rename(None)

        return False

    @save_tabs_when_changed
    def on_new_tab(self, user_data):
        self.notebook.new_page_with_focus()

    @save_tabs_when_changed
    def on_rename(self, user_data):
        HidePrevention(self.get_toplevel()).prevent()
        dialog = RenameDialog(self.notebook.guake.window, self.label.get_text())
        r = dialog.run()
        if r == Gtk.ResponseType.ACCEPT:
            new_text = TabNameUtils.shorten(dialog.get_text(), self.notebook.guake.settings)
            page_num = self.notebook.find_tab_index_by_label(self)
            self.notebook.rename_page(page_num, new_text, True)
        dialog.destroy()
        HidePrevention(self.get_toplevel()).allow()

        self.grab_focus_on_last_focused_terminal()

    def on_close(self, user_data):
        prompt_cfg = self.notebook.guake.settings.general.get_int('prompt-on-close-tab')
        self.notebook.delete_page_by_label(self, prompt=prompt_cfg)

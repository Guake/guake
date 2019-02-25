import logging

from locale import gettext as _

import gi
gi.require_version('Vte', '2.91')  # vte-0.42
gi.require_version('Gtk', '3.0')
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


class RootTerminalBox(Gtk.Box, TerminalHolder):

    def __init__(self, guake, parent_notebook):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.guake = guake
        self.notebook = parent_notebook
        self.child = None
        self.last_terminal_focused = None

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
            self.pack_start(terminal_holder, True, True, 0)
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
        self.terminal.connect("grab-focus", self.on_terminal_focus)
        self.terminal.connect("button-press-event", self.on_button_press, None)
        self.terminal.connect('child-exited', self.on_terminal_exited)

        self.pack_start(self.terminal, True, True, 0)
        self.terminal.show()
        self.add_scroll_bar()

    def add_scroll_bar(self):
        """Packs the scrollbar.
        """
        adj = self.terminal.get_vadjustment()
        scroll = Gtk.VScrollbar(adj)
        scroll.show()
        self.pack_start(scroll, False, False, 0)

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
        self.split(DualTerminalBox.ORIENT_V)

    def split_v(self):
        self.split(DualTerminalBox.ORIENT_H)

    def split(self, orientation):
        notebook = self.get_notebook()
        parent = self.get_parent()
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

    def on_terminal_exited(self, *args):
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

    def remove_dead_child(self, child):
        if self.get_child1() is child:
            livingChild = self.get_child2()
            self.remove(livingChild)
            self.get_parent().replace_child(self, livingChild)
            livingChild.get_terminal().grab_focus()
        elif self.get_child2() is child:
            livingChild = self.get_child1()
            self.remove(livingChild)
            self.get_parent().replace_child(self, livingChild)
            livingChild.get_terminal().grab_focus()
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
            self.notebook.get_current_terminal().grab_focus()
            return True
        if event.button == 2:
            prompt_cfg = self.notebook.guake.settings.general.get_int('prompt-on-close-tab')
            self.notebook.delete_page_by_label(self, prompt=prompt_cfg)
            return True
        if event.button == 1 and event.type == Gdk.EventType._2BUTTON_PRESS:
            self.on_rename(None)

        self.notebook.get_current_terminal().grab_focus()
        return False

    def on_new_tab(self, user_data):
        self.notebook.new_page_with_focus()

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
        # TODO
        #        self.set_terminal_focus()

    def on_close(self, user_data):
        prompt_cfg = self.notebook.guake.settings.general.get_int('prompt-on-close-tab')
        self.notebook.delete_page_by_label(self, prompt=prompt_cfg)

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class TerminalHolder():

    def get_terminals(self):
        pass

    def iter_terminals(self):
        pass

    def replace_child(self, old, new):
        pass

    def get_guake(self):
        pass

    def get_root_box(self):
        pass


class RootTerminalBox(Gtk.Box, TerminalHolder):

    def __init__(self, guake):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.guake = guake
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
        self.set_child(new_child)

    def set_child(self, terminal_holder):
        if isinstance(terminal_holder, TerminalHolder) or True:
            self.child = terminal_holder
            self.pack_start(terminal_holder, True, True, 0)
        else:
            print(
                "wtf, what have you added to me???"
                "(RootTerminalBox.add(%s))" % type(terminal_holder)
            )

    def get_child(self):
        return self.child

    def get_guake(self):
        return self.guake

    def get_root_box(self):
        return self

    def set_last_terminal_focused(self, terminal):
        self.last_terminal_focused = terminal
        self.guake.notebook.set_last_terminal_focused(terminal)


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
        self.terminal.connect("focus", self.on_terminal_focus)
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
        return [self.terminal]

    def iter_terminals(self):
        yield self.terminal

    def replace_child(self, old, new):
        print("why would you call this on me?")
        pass

    def split_h(self):
        self.split(DualTerminalBox.ORIENT_H)

    def split_v(self):
        self.split(DualTerminalBox.ORIENT_V)

    def split(self, orientation):
        parent = self.get_parent()
        dual_terminal_box = DualTerminalBox(orientation)
        parent.replace_child(self, dual_terminal_box)
        dual_terminal_box.set_child_first(self)
        dual_terminal_box.set_child_second(GuakeTerminal())

    def get_guake(self):
        return self.get_parent().get_guake()

    def get_root_box(self):
        return self.get_parent()

    def on_terminal_focus(self, direction, user_data):
        self.get_root_box().set_last_terminal_focused(self.terminal)


class DualTerminalBox(Gtk.Paned, TerminalHolder):

    ORIENT_H = 0
    ORIENT_V = 1

    def __init__(self, orientation):
        super().__init__()

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
        self.get_child1().iter_terminals(self)
        self.get_child2().iter_terminals(self)

    def replace_child(self, old, new):
        if self.get_child1() is old:
            self.set_child_first(new)
        elif self.get_child2() is old:
            self.set_child_second(new)
        else:
            print("I have never seen this widget!")

    def get_guake(self):
        return self.get_parent().get_guake()

    def get_root_box(self):
        return self.get_parent()

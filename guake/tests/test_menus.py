# -*- coding: utf-8 -*-

from types import SimpleNamespace

from guake.callbacks import TerminalContextMenuCallbacks
from guake.menus import mk_terminal_context_menu


class FakeMenu:
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)

    def show_all(self):
        return None


class FakeMenuItem:
    def __init__(self, label=""):
        self.label = label
        self.connections = []
        self.sensitive = True

    def connect(self, signal, callback):
        self.connections.append((signal, callback))

    def set_label(self, label):
        self.label = label

    def set_sensitive(self, sensitive):
        self.sensitive = sensitive

    def set_submenu(self, submenu):
        self.submenu = submenu

    def set_use_stock(self, use_stock):
        self.use_stock = use_stock


class FakeSeparatorMenuItem:
    pass


class FakeClipboard:
    @classmethod
    def get_default(cls, display):
        return cls()

    def wait_is_text_available(self):
        return False


class FakeCallbacks:
    def __getattr__(self, name):
        def callback(*args):
            return None

        callback.__name__ = name
        setattr(self, name, callback)
        return callback


class FakeTerminal:
    found_link = None

    def get_has_selection(self):
        return False


class FakeCustomCommands:
    def __init__(self, settings, callback):
        return None

    def should_load(self):
        return False


def test_terminal_context_menu_contains_pane_move_items(monkeypatch):
    import guake.menus as menus

    fake_gtk = SimpleNamespace(
        Menu=FakeMenu,
        MenuItem=FakeMenuItem,
        ImageMenuItem=FakeMenuItem,
        SeparatorMenuItem=FakeSeparatorMenuItem,
        Clipboard=FakeClipboard,
    )
    monkeypatch.setattr(menus, "Gtk", fake_gtk)
    monkeypatch.setattr(menus, "CustomCommands", FakeCustomCommands)

    callbacks = FakeCallbacks()
    menu = mk_terminal_context_menu(
        FakeTerminal(),
        SimpleNamespace(get_display=lambda: object()),
        SimpleNamespace(general=SimpleNamespace(get_string=lambda key: None)),
        callbacks,
    )
    items_by_label = {
        item.label: item
        for item in menu.items
        if isinstance(item, FakeMenuItem)
    }

    assert items_by_label["Move pane up"].connections == [
        ("activate", callbacks.on_move_pane_up)
    ]
    assert items_by_label["Move pane down"].connections == [
        ("activate", callbacks.on_move_pane_down)
    ]
    assert items_by_label["Move pane left"].connections == [
        ("activate", callbacks.on_move_pane_left)
    ]
    assert items_by_label["Move pane right"].connections == [
        ("activate", callbacks.on_move_pane_right)
    ]


def test_terminal_context_callbacks_move_pane(monkeypatch):
    from guake import split_utils

    calls = []
    terminal = object()
    window = object()

    class FakePaneMover:
        def __init__(self, mover_window):
            calls.append(("init", mover_window))

        def move_up(self, mover_terminal):
            calls.append(("up", mover_terminal))

        def move_down(self, mover_terminal):
            calls.append(("down", mover_terminal))

        def move_left(self, mover_terminal):
            calls.append(("left", mover_terminal))

        def move_right(self, mover_terminal):
            calls.append(("right", mover_terminal))

    monkeypatch.setattr(split_utils, "PaneMover", FakePaneMover)

    callbacks = TerminalContextMenuCallbacks(terminal, window, object(), object())
    callbacks.on_move_pane_up()
    callbacks.on_move_pane_down()
    callbacks.on_move_pane_left()
    callbacks.on_move_pane_right()

    assert calls == [
        ("init", window),
        ("up", terminal),
        ("init", window),
        ("down", terminal),
        ("init", window),
        ("left", terminal),
        ("init", window),
        ("right", terminal),
    ]

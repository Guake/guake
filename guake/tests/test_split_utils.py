# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET

from types import SimpleNamespace

from guake.prefs import HOTKEYS
from guake.split_utils import PaneMover


PANE_MOVE_KEYS = {
    "move-terminal-pane-up",
    "move-terminal-pane-down",
    "move-terminal-pane-left",
    "move-terminal-pane-right",
}


class FakeWindow:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def get_size(self):
        return self.width, self.height


class FakeRoot:
    def __init__(self):
        self.terminals = []

    def iter_terminals(self):
        yield from self.terminals


class FakeTerminalBox:
    def __init__(self, root, x, y, width, height):
        self.root = root
        self.x = x
        self.y = y
        self.allocation = SimpleNamespace(width=width, height=height)
        self.parent = None

    def get_parent(self):
        return self.parent

    def set_parent(self, parent):
        self.parent = parent

    def get_root_box(self):
        return self.root

    def get_allocation(self):
        return self.allocation

    def translate_coordinates(self, window, x, y):
        return self.x, self.y

    def reparent(self, parent):
        if self.parent is not None:
            self.parent.remove_child(self)
        parent.add_child(self)

    def ref(self):
        raise RuntimeError("ref should not be used through PyGObject")


class FakeTerminal:
    def __init__(self, box):
        self.box = box
        self.focus_count = 0

    def get_parent(self):
        return self.box

    def grab_focus(self):
        self.focus_count += 1


class FakeHolder:
    def __init__(self, root, first=None, second=None, position=50):
        self.root = root
        self.children = {1: None, 2: None}
        self.position = position
        if first is not None:
            self.children[1] = first
            first.set_parent(self)
        if second is not None:
            self.children[2] = second
            second.set_parent(self)

    def child_at(self, position):
        return self.children[position]

    def add_child(self, child):
        if self.children[1] is None:
            self.children[1] = child
        elif self.children[2] is None:
            self.children[2] = child
        else:
            raise RuntimeError("holder is full")
        child.set_parent(self)

    def remove_child(self, child):
        position = self.get_child_position(child)
        self.children[position] = None
        child.set_parent(None)

    def get_root_box(self):
        return self.root

    def get_child_position(self, child):
        for position, candidate in self.children.items():
            if candidate is child:
                return position
        raise RuntimeError("unknown child")

    def detach_child(self, child, temporary_parent):
        position = self.get_child_position(child)
        child.reparent(temporary_parent)
        return position

    def attach_detached_child(self, position, child):
        child.reparent(self)


class FakeTemporaryHolder:
    def __init__(self):
        self.children = []

    def add_child(self, child):
        self.children.append(child)
        child.set_parent(self)

    def remove_child(self, child):
        self.children.remove(child)
        child.set_parent(None)


class FakeSettingsGroup:
    def __init__(self):
        self.changed_keys = []

    def onChangedValue(self, key, callback):
        self.changed_keys.append(key)

    def triggerOnChangedValue(self, *args):
        return None

    def get_string(self, key):
        return ""


class FakeSettings:
    def __init__(self):
        self.keybindingsGlobal = FakeSettingsGroup()
        self.keybindingsLocal = FakeSettingsGroup()
        self.general = SimpleNamespace(get_int=lambda key: 0)


class FakeGuake:
    def __init__(self):
        self.settings = FakeSettings()
        self.window = object()

    def gen_accel_switch_tabN(self, index):
        return self.noop

    def noop(self, *args):
        return None

    def __getattr__(self, name):
        if name.startswith("accel_") or name in (
            "search_on_web",
            "open_link_under_terminal_cursor",
        ):
            return self.noop
        raise AttributeError(name)


def make_terminal(root, x, y, width, height):
    box = FakeTerminalBox(root, x, y, width, height)
    terminal = FakeTerminal(box)
    root.terminals.append(terminal)
    return box, terminal


def patch_temporary_parent(monkeypatch):
    import guake.boxes as boxes

    monkeypatch.setattr(boxes.Gtk, "Box", FakeTemporaryHolder)


def test_move_pane_swaps_terminal_boxes_in_same_parent(monkeypatch):
    patch_temporary_parent(monkeypatch)
    root = FakeRoot()
    left_box, left_terminal = make_terminal(root, 0, 0, 100, 100)
    right_box, _ = make_terminal(root, 100, 0, 100, 100)
    parent = FakeHolder(root, left_box, right_box, position=42)

    PaneMover(FakeWindow(200, 100)).move_right(left_terminal)

    assert parent.child_at(1) is right_box
    assert parent.child_at(2) is left_box
    assert parent.position == 42
    assert left_terminal.focus_count == 1


def test_move_pane_swaps_terminal_boxes_in_same_parent_from_second_slot(monkeypatch):
    patch_temporary_parent(monkeypatch)
    root = FakeRoot()
    left_box, _ = make_terminal(root, 0, 0, 100, 100)
    right_box, right_terminal = make_terminal(root, 100, 0, 100, 100)
    parent = FakeHolder(root, left_box, right_box, position=42)

    PaneMover(FakeWindow(200, 100)).move_left(right_terminal)

    assert parent.child_at(1) is right_box
    assert parent.child_at(2) is left_box
    assert parent.position == 42
    assert right_terminal.focus_count == 1


def test_move_pane_swaps_terminal_boxes_in_different_parents(monkeypatch):
    patch_temporary_parent(monkeypatch)
    root = FakeRoot()
    source_box, source_terminal = make_terminal(root, 0, 0, 100, 100)
    left_sibling, _ = make_terminal(root, 0, 100, 100, 100)
    right_sibling, _ = make_terminal(root, 100, 100, 100, 100)
    target_box, _ = make_terminal(root, 100, 0, 100, 100)
    source_parent = FakeHolder(root, source_box, left_sibling, position=25)
    target_parent = FakeHolder(root, right_sibling, target_box, position=75)

    PaneMover(FakeWindow(200, 200)).move_right(source_terminal)

    assert source_parent.child_at(1) is target_box
    assert target_parent.child_at(2) is source_box
    assert source_parent.position == 25
    assert target_parent.position == 75
    assert source_terminal.focus_count == 1


def test_move_pane_noops_at_outer_edge(monkeypatch):
    patch_temporary_parent(monkeypatch)
    root = FakeRoot()
    left_box, left_terminal = make_terminal(root, 0, 0, 100, 100)
    right_box, _ = make_terminal(root, 100, 0, 100, 100)
    parent = FakeHolder(root, left_box, right_box)

    PaneMover(FakeWindow(200, 100)).move_left(left_terminal)

    assert parent.child_at(1) is left_box
    assert parent.child_at(2) is right_box
    assert left_terminal.focus_count == 0


def test_pane_move_hotkeys_are_registered(monkeypatch):
    import guake.keybindings as keybindings

    monkeypatch.setattr(keybindings.Gdk.Display, "get_default", lambda: None)
    monkeypatch.setattr(keybindings.Gdk.Keymap, "get_for_display", lambda display: object())

    bindings = keybindings.Keybindings(FakeGuake())
    actions = dict(bindings.keys)

    for key in PANE_MOVE_KEYS:
        assert key in actions
        assert callable(actions[key])
        assert key in bindings.guake.settings.keybindingsLocal.changed_keys


def test_pane_move_hotkeys_are_in_schema_and_preferences():
    schema = ET.parse("guake/data/org.guake.gschema.xml")
    local_schema = schema.find(".//schema[@id='guake.keybindings.local']")
    schema_keys = {key.get("name"): key.findtext("default") for key in local_schema}
    prefs_keys = {
        item["key"]
        for group in HOTKEYS
        for item in group["keys"]
    }

    for key in PANE_MOVE_KEYS:
        assert schema_keys[key] == "''"
        assert key in prefs_keys

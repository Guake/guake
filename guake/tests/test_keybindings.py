# -*- coding: utf-8 -*-

from types import SimpleNamespace

import gi

gi.require_version("Gdk", "3.0")
from gi.repository import Gdk

from guake.keybindings import Keybindings


class FakeKeymap:
    """Stands in for Gdk.Keymap: one hardware keycode, the keyvals it carries."""

    def __init__(self, keyvals_by_keycode):
        self.keyvals_by_keycode = keyvals_by_keycode

    def get_entries_for_keycode(self, hardware_keycode):
        keyvals = self.keyvals_by_keycode[hardware_keycode]
        return True, [hardware_keycode] * len(keyvals), keyvals


def make_keybindings(lookup, keyvals_by_keycode):
    # skip __init__: it needs a running Guake to read its settings from
    keybindings = Keybindings.__new__(Keybindings)
    keybindings.keymap = FakeKeymap(keyvals_by_keycode)
    keybindings._lookup = lookup
    keybindings._masks = 0
    for mask in lookup:
        keybindings._masks |= mask
    return keybindings


def control_event(keyval, hardware_keycode):
    return SimpleNamespace(
        keyval=keyval, hardware_keycode=hardware_keycode, state=Gdk.ModifierType.CONTROL_MASK
    )


def test_keypad_binding_fires():
    calls = []
    keybindings = make_keybindings(
        {Gdk.ModifierType.CONTROL_MASK: {Gdk.KEY_KP_Divide: lambda: calls.append("split-v")}},
        {106: [Gdk.KEY_KP_Divide, Gdk.KEY_slash, 247]},
    )

    assert keybindings.activate(None, control_event(Gdk.KEY_KP_Divide, 106))
    assert calls == ["split-v"]


def test_keypad_binding_is_not_shadowed_by_the_ascii_keysym_on_its_keycode():
    calls = []
    keybindings = make_keybindings(
        {
            Gdk.ModifierType.CONTROL_MASK: {
                Gdk.KEY_KP_Subtract: lambda: calls.append("split-h"),
                Gdk.KEY_minus: lambda: calls.append("zoom-out"),
            }
        },
        {82: [Gdk.KEY_KP_Subtract, Gdk.KEY_minus, Gdk.KEY_minus]},
    )

    assert keybindings.activate(None, control_event(Gdk.KEY_KP_Subtract, 82))
    assert calls == ["split-h"]


def test_ascii_keysym_still_fires_when_the_keypad_key_has_no_binding():
    calls = []
    keybindings = make_keybindings(
        {Gdk.ModifierType.CONTROL_MASK: {Gdk.KEY_slash: lambda: calls.append("split-v")}},
        {106: [Gdk.KEY_KP_Divide, Gdk.KEY_slash]},
    )

    assert keybindings.activate(None, control_event(Gdk.KEY_KP_Divide, 106))
    assert calls == ["split-v"]


def test_non_latin_keyval_falls_back_to_the_english_keysym():
    calls = []
    keybindings = make_keybindings(
        {Gdk.ModifierType.CONTROL_MASK: {Gdk.KEY_t: lambda: calls.append("new-tab")}},
        {28: [1077, Gdk.KEY_t]},
    )

    assert keybindings.activate(None, control_event(1077, 28))
    assert calls == ["new-tab"]

# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name,protected-access
from types import SimpleNamespace

import pytest

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from guake.globals import ALWAYS_ON_PRIMARY
from guake.prefs import PrefsCallbacks
from guake.prefs import PrefsDialog
from guake.utils import RectCalculator
from guake.utils import get_display_index
from guake.utils import get_monitor_name


@pytest.fixture
def settings(mocker):
    values = {"display-n": 1, "display-name": "", "mouse-display": False}
    general = mocker.Mock()
    general.get_int.side_effect = values.__getitem__
    general.get_string.side_effect = values.__getitem__
    general.get_boolean.side_effect = values.__getitem__
    general.set_int.side_effect = values.__setitem__
    general.set_string.side_effect = values.__setitem__
    general.set_boolean.side_effect = values.__setitem__
    return SimpleNamespace(general=general)


@pytest.fixture
def display(mocker):
    display = mocker.Mock()
    primary = mocker.Mock()
    primary.get_model.return_value = "eDP-1"
    primary.is_primary.return_value = True
    external = mocker.Mock()
    external.get_model.return_value = "DP-1"
    external.is_primary.return_value = False
    display.monitors = [primary, external]
    display.get_n_monitors.side_effect = lambda: len(display.monitors)
    display.get_monitor.side_effect = lambda i: display.monitors[i]
    display.get_primary_monitor.return_value = primary
    return display


def test_numeric_selection_is_migrated_and_survives_reordering(settings, display, mocker):
    window = mocker.Mock()
    window.get_display.return_value = display
    selected = display.monitors[1]
    assert RectCalculator.get_final_window_monitor(settings, window) is selected
    assert settings.general.get_string("display-name") == "DP-1"

    display.monitors.reverse()
    assert settings.general.get_int("display-n") == 1
    assert RectCalculator.get_final_window_monitor(settings, window) is selected


def test_saved_name_survives_restart(settings, display, mocker):
    settings.general.set_string("display-name", "DP-1")
    # New GDK monitor objects, in a different order from the previous process.
    selected = mocker.Mock()
    selected.get_model.return_value = "DP-1"
    display.monitors = [selected, display.monitors[0]]
    assert get_display_index(settings, display) == 0


def test_disconnected_display_is_retained_until_reconnected(settings, display, mocker):
    window = mocker.Mock()
    window.get_display.return_value = display
    selected = display.monitors[1]
    get_display_index(settings, display)
    display.monitors = [display.monitors[0]]
    assert RectCalculator.get_final_window_monitor(settings, window) is display.monitors[0]
    assert settings.general.get_string("display-name") == "DP-1"
    assert settings.general.get_int("display-n") == 1

    display.monitors.insert(0, selected)
    assert RectCalculator.get_final_window_monitor(settings, window) is selected


def test_primary_selection_ignores_saved_name(settings, display, mocker):
    settings.general.set_int("display-n", ALWAYS_ON_PRIMARY)
    settings.general.set_string("display-name", "DP-1")
    window = mocker.Mock()
    window.get_display.return_value = display
    assert RectCalculator.get_final_window_monitor(settings, window) is display.monitors[0]


@pytest.mark.parametrize("pointer_available", [True, False])
def test_mouse_selection_still_takes_precedence(settings, display, mocker, pointer_available):
    settings.general.set_boolean("mouse-display", True)
    settings.general.set_string("display-name", "disconnected")
    window = mocker.Mock()
    window.get_display.return_value = display
    pointer = mocker.Mock() if pointer_available else None
    display.get_default_seat.return_value.get_pointer.return_value = pointer
    if pointer:
        pointer.get_position.return_value = (None, 2000, 100)
        display.get_monitor_at_point.return_value = display.monitors[1]
    expected = display.monitors[1 if pointer_available else 0]
    assert RectCalculator.get_final_window_monitor(settings, window) is expected


@pytest.mark.parametrize("name", [None, "", "eDP-1"])
def test_missing_or_ambiguous_name_keeps_numeric_fallback(settings, display, name):
    display.monitors[1].get_model.return_value = name
    assert get_monitor_name(display, 1) == ""
    assert get_display_index(settings, display) == 1
    assert settings.general.get_string("display-name") == ""


@pytest.mark.parametrize("index", [-2, 2, 100])
def test_invalid_legacy_index_falls_back_without_changing_settings(settings, display, index):
    settings.general.set_int("display-n", index)
    assert get_display_index(settings, display) == ALWAYS_ON_PRIMARY
    assert settings.general.get_int("display-n") == index


@pytest.fixture
def dialog(settings, display, mocker):
    dialog = PrefsDialog.__new__(PrefsDialog)
    dialog.settings = settings
    dialog.window = mocker.Mock()
    dialog.window.get_display.return_value = display
    dialog.loading_display_settings = False
    combo = Gtk.ComboBoxText()
    mocker.patch.object(dialog, "get_widget", return_value=combo)
    combo.connect("changed", PrefsCallbacks(dialog).on_display_n_changed)
    return dialog


def test_preferences_reordering_does_not_overwrite_selected_name(dialog, display):
    dialog._load_screen_settings()
    display.monitors.reverse()
    dialog._load_screen_settings()
    assert dialog.get_widget("display_n").get_active_id() == "0"
    assert dialog.settings.general.get_string("display-name") == "DP-1"
    assert dialog.settings.general.get_int("display-n") == 1


def test_preferences_keep_missing_display_and_mouse_mode(dialog, display):
    dialog._load_screen_settings()
    dialog.settings.general.set_boolean("mouse-display", True)
    selected = display.monitors.pop()
    dialog._load_screen_settings()
    assert dialog.get_widget("display_n").get_active_id() == "unavailable"
    assert dialog.settings.general.get_string("display-name") == "DP-1"
    assert dialog.settings.general.get_int("display-n") == 1
    assert dialog.settings.general.get_boolean("mouse-display")

    display.monitors.insert(0, selected)
    dialog._load_screen_settings()
    assert dialog.get_widget("display_n").get_active_id() == "0"


def test_preferences_can_choose_another_display_or_primary(dialog):
    dialog._load_screen_settings()
    combo = dialog.get_widget("display_n")
    combo.set_active_id("0")
    assert dialog.settings.general.get_string("display-name") == "eDP-1"
    assert dialog.settings.general.get_int("display-n") == 0
    combo.set_active_id(str(ALWAYS_ON_PRIMARY))
    assert dialog.settings.general.get_string("display-name") == ""
    assert dialog.settings.general.get_int("display-n") == ALWAYS_ON_PRIMARY

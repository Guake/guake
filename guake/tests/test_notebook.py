# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name

from types import SimpleNamespace

import pytest

from guake.notebook import NotebookManager
from guake.notebook import TerminalNotebook


@pytest.fixture
def nb(mocker):
    targets = [
        "guake.notebook.TerminalNotebook.terminal_spawn",
        "guake.notebook.TerminalNotebook.terminal_attached",
        "guake.notebook.TerminalNotebook.guake",
        "guake.notebook.TerminalBox.set_terminal",
    ]
    for target in targets:
        mocker.patch(target, create=True)
    return TerminalNotebook()


def test_zero_page_notebook(nb):
    assert nb.get_n_pages() == 0


def test_add_one_page_to_notebook(nb):
    nb.new_page()
    assert nb.get_n_pages() == 1


def test_add_two_pages_to_notebook(nb):
    nb.new_page()
    nb.new_page()
    assert nb.get_n_pages() == 2


def test_remove_page_in_notebook(nb):
    nb.new_page()
    nb.new_page()
    assert nb.get_n_pages() == 2
    nb.remove_page(0)
    assert nb.get_n_pages() == 1
    nb.remove_page(0)
    assert nb.get_n_pages() == 0


def test_rename_page(nb):
    t1 = "foo"
    t2 = "bar"
    nb.new_page()
    nb.rename_page(0, t1, True)
    assert nb.get_tab_text_index(0) == t1
    nb.rename_page(0, t2, False)
    assert nb.get_tab_text_index(0) == t1
    nb.rename_page(0, t2, True)
    assert nb.get_tab_text_index(0) == t2


def test_add_new_page_with_focus_with_label(nb):
    t = "test_this_label"
    nb.new_page_with_focus(label=t)
    assert nb.get_n_pages() == 1
    assert nb.get_tab_text_index(0) == t


def test_new_tab_button_adds_page_at_the_end(nb, mocker):
    new_page = mocker.patch.object(nb, "new_page_with_focus")

    nb.on_new_tab(None)

    new_page.assert_called_once_with(position=-1)


def test_new_tab_context_menu_adds_page_after_current(nb, mocker):
    mocker.patch.object(nb, "get_current_page", return_value=2)
    new_page = mocker.patch.object(nb, "new_page_with_focus")

    nb.on_new_tab_after_current(None)

    new_page.assert_called_once_with(position=3)


def test_notebook_manager_switches_current_workspace(mocker):
    parent = mocker.Mock()
    window = mocker.Mock()
    window.get_property.return_value = False
    manager = NotebookManager(window, parent, False, mocker.Mock(), mocker.Mock())
    workspace_zero = SimpleNamespace(
        last_terminal_focused=None,
        guake=SimpleNamespace(
            restore_pending_terminal_split=mocker.Mock(), load_config=mocker.Mock()
        ),
    )
    workspace_one = SimpleNamespace(
        last_terminal_focused=None,
        guake=SimpleNamespace(
            restore_pending_terminal_split=mocker.Mock(), load_config=mocker.Mock()
        ),
    )
    manager.notebooks = {0: workspace_zero, 1: workspace_one}

    manager.set_workspace(1)

    assert manager.current_notebook == 1
    parent.remove.assert_called_once_with(workspace_zero)
    parent.add.assert_called_once_with(workspace_one)
    workspace_one.guake.restore_pending_terminal_split.assert_called_once_with()
    workspace_one.guake.load_config.assert_called_once_with()

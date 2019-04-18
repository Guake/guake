# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name

import pytest

from guake.notebook import TerminalNotebook


@pytest.fixture
def nb(mocker):
    targets = [
        'guake.notebook.TerminalNotebook.terminal_spawn',
        'guake.notebook.TerminalNotebook.terminal_attached',
        'guake.notebook.TerminalNotebook.guake', 'guake.notebook.TerminalBox.set_terminal'
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
    t1 = 'foo'
    t2 = 'bar'
    nb.new_page()
    nb.rename_page(0, t1, True)
    assert nb.get_tab_text_index(0) == t1
    nb.rename_page(0, t2, False)
    assert nb.get_tab_text_index(0) == t1
    nb.rename_page(0, t2, True)
    assert nb.get_tab_text_index(0) == t2


def test_add_new_page_with_focus_with_label(nb):
    t = 'test_this_label'
    nb.new_page_with_focus(label=t)
    assert nb.get_n_pages() == 1
    assert nb.get_tab_text_index(0) == t

# -*- coding: utf-8 -*-

import pytest
import mock
from mock import Mock, MagicMock

import guake.notebook


guake.notebook.TerminalBox = Mock()
mockRootTerminalBox = guake.notebook.RootTerminalBox
mockRootTerminalBox.set_child = Mock()
mockRootTerminalBox.get_terminals = Mock()
guake.notebook.RootTerminalBox = mockRootTerminalBox
mockTerminalNotebook = guake.notebook.TerminalNotebook
mockTerminalNotebook.terminal_spawn = Mock()
mockTerminalNotebook.terminal_attached = Mock()
mockTerminalNotebook.guake = Mock()


class TestNotebook:

    def setup_method(self):
        self.nb = mockTerminalNotebook()

    def test_zero_page_notebook(self):
        assert self.nb.get_n_pages() == 0

    def test_add_one_page_to_notebook(self):
        self.nb.new_page_with_focus()
        assert self.nb.get_n_pages() == 1

    def test_add_two_page_to_notebook(self):
        self.nb.new_page_with_focus()
        self.nb.new_page_with_focus()
        assert self.nb.get_n_pages() == 2

    def test_remove_page(self):
        self.nb.new_page()
        self.nb.new_page()
        assert self.nb.get_n_pages() == 2

        with mock.patch.object(self.nb, 'get_current_page', new=lambda: -1):
            self.nb.remove_page(0)
            assert self.nb.get_n_pages() == 1
            self.nb.remove_page(0)
            assert self.nb.get_n_pages() == 0

    def test_add_new_page_with_focus_with_label(self):
        t = 'test_this_title'
        self.nb.new_page_with_focus(label=t)
        assert self.nb.get_tab_text_index(0) == t

    def test_rename_page(self):
        t1 = 'foo'
        t2 = 'bar'
        self.nb.new_page_with_focus(label=t1)
        assert self.nb.get_tab_text_index(0) == t1
        self.nb.rename_page(0, t2)
        assert self.nb.get_tab_text_index(0) == t1
        self.nb.rename_page(0, t2, True)
        assert self.nb.get_tab_text_index(0) == t2

# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name

import json
import os
import tempfile
import time

from pathlib import Path

import pytest

import guake.guake_app

from guake.common import pixmapfile
from guake.guake_app import Guake


@pytest.fixture
def g(mocker, fs):
    mocker.patch('guake.guake_app.Guake.get_xdg_config_directory', return_value=Path('/foobar'))
    mocker.patch('guake.guake_app.shutil.copy', create=True)
    mocker.patch('guake.guake_app.notifier.showMessage', create=True)
    mocker.patch('guake.guake_app.traceback.print_exc', create=True)
    fs.pause()
    g = Guake()
    fs.add_real_file(pixmapfile('guake-notification.png'))
    fs.resume()
    return g


# Accel Test


def test_accel_search_terminal(g):
    nb = g.get_notebook()
    page = nb.get_nth_page(0)
    assert not page.search_revealer.get_reveal_child()

    g.accel_search_terminal()
    assert page.search_revealer.get_reveal_child()


def test_accel_search_terminal_debounce(g):
    nb = g.get_notebook()
    page = nb.get_nth_page(0)
    assert not page.search_revealer.get_reveal_child()

    g.prev_accel_search_terminal_time = time.time()
    g.accel_search_terminal()
    assert not page.search_revealer.get_reveal_child()


def test_accel_quit_without_prompt(mocker, g):
    # Disable quit prompt
    mocker.patch.object(g.settings.general, 'get_boolean', return_value=False)
    mocker.patch('guake.guake_app.Gtk.main_quit')

    g.accel_quit()
    assert guake.guake_app.Gtk.main_quit.call_count == 1


def test_accel_quit_with_prompt(mocker, g):
    # Enable quit prompt
    mocker.patch.object(g.settings.general, 'get_boolean', return_value=True)
    mocker.patch('guake.guake_app.PromptQuitDialog')
    mocker.patch('guake.guake_app.Gtk.main_quit')

    g.accel_quit()
    assert guake.guake_app.Gtk.main_quit.call_count == 1


# Save/Restore Tabs


def test_guake_restore_tabs(g, fs):
    d1 = fs.create_dir('/foobar/foo')
    d2 = fs.create_dir('/foobar/bar')
    d3 = fs.create_dir('/foobar/foo/foo')
    d4 = fs.create_dir('/foobar/foo/bar')
    session = {
        "schema_version": 1,
        "timestamp": 1556092197,
        "workspace": {
            "0": [[{
                "directory": d1.path,
                "label": "1",
                "custom_label_set": True
            }, {
                "directory": d2.path,
                "label": "2",
                "custom_label_set": True
            }, {
                "directory": d3.path,
                "label": d3.path,
                "custom_label_set": False
            }]],
            "1": [[{
                "directory": d4.path,
                "label": "4",
                "custom_label_set": True
            }]]
        }
    }

    fn = fs.create_file('/foobar/session.json')
    with open(fn.path, 'w') as f:
        f.write(json.dumps(session))

    g.restore_tabs(fn.name)
    nb = g.notebook_manager.get_notebook(0)
    assert nb.get_n_pages() == 3
    assert nb.get_tab_text_index(0) == '1'
    assert nb.get_tab_text_index(1) == '2'

    nb = g.notebook_manager.get_notebook(1)
    assert nb.get_n_pages() == 1
    assert nb.get_tab_text_index(0) == '4'


def test_guake_restore_tabs_json_without_schema_version(g, fs):
    guake.guake_app.notifier.showMessage.reset_mock()

    fn = fs.create_file('/foobar/bar.json')
    with open(fn.path, 'w') as f:
        f.write('{}')

    g.restore_tabs(fn.name)
    assert guake.guake_app.notifier.showMessage.call_count == 1


def test_guake_restore_tabs_with_higher_schema_version(g, fs):
    guake.guake_app.notifier.showMessage.reset_mock()

    fn = fs.create_file('/foobar/bar.json')
    with open(fn.path, 'w') as f:
        f.write('{"schema_version": 2147483647}')

    g.restore_tabs(fn.name)
    assert guake.guake_app.notifier.showMessage.call_count == 1


def test_guake_restore_tabs_json_broken_session_file(g, fs):
    guake.guake_app.notifier.showMessage.reset_mock()
    fn = fs.create_file('/foobar/foobar.json')
    with open(fn.path, 'w') as f:
        f.write('{')

    g.restore_tabs(fn.name)
    assert guake.guake_app.shutil.copy.call_count == 1
    assert guake.guake_app.notifier.showMessage.call_count == 1


def test_guake_restore_tabs_schema_broken_session_file(g, fs):
    guake.guake_app.notifier.showMessage.reset_mock()

    fn = fs.create_file('/foobar/bar.json')
    d = fs.create_dir('/foobar/foo')
    with open(fn.path, 'w') as f:
        f.write('{"schema_version": 1, "workspace": {"0": [[{"directory": "%s"}]]}}' % (d.path))

    g.restore_tabs(fn.name)
    assert guake.guake_app.shutil.copy.call_count == 1
    assert guake.guake_app.traceback.print_exc.call_count == 1


def test_guake_save_tabs_and_restore(mocker, g, fs):
    # Disable auto save
    mocker.patch.object(g.settings.general, 'get_boolean', return_value=False)

    # Save
    assert not os.path.exists('/foobar/session.json')
    g.add_tab()
    g.rename_current_tab('foobar', True)
    g.add_tab()
    g.rename_current_tab('python', True)
    assert g.get_notebook().get_n_pages() == 3

    g.save_tabs()
    assert os.path.exists('/foobar')
    assert os.path.exists('/foobar/session.json')

    # Restore prepare
    g.close_tab()
    g.close_tab()
    assert g.get_notebook().get_n_pages() == 1

    # Restore
    g.restore_tabs()
    nb = g.get_notebook()
    assert nb.get_n_pages() == 3
    assert nb.get_tab_text_index(1) == 'foobar'
    assert nb.get_tab_text_index(2) == 'python'

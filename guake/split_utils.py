# -*- coding: utf-8; -*-
"""
Copyright (C) 2018 Mario Aichinger <aichingm@gmail.com>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public
License along with this program; if not, write to the
Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
Boston, MA 02110-1301 USA
"""
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from guake.boxes import DualTerminalBox
from guake.boxes import RootTerminalBox


class FocusMover():

    THRESHOLD = 10
    BORDER_THICKNESS = 2

    def __init__(self, window):
        self.window = window

    def move_right(self, terminal):
        window_width, window_height = self.window.get_size()
        tx, ty, tw, th = self.list_allocation(terminal)

        if tx + tw == window_width:
            return

        search_x = tx + tw + FocusMover.THRESHOLD
        search_y = ty + (th / 2) - FocusMover.BORDER_THICKNESS
        for term in terminal.get_parent().get_root_box().iter_terminals():
            sx, sy, sw, sh = self.list_allocation(term)
            if sx <= search_x <= sx + sw and sy <= search_y <= sy + sh:
                term.grab_focus()

    def move_left(self, terminal):
        window_width, window_height = self.window.get_size()
        tx, ty, tw, th = self.list_allocation(terminal)

        if tx == 0:
            return

        search_x = tx - FocusMover.THRESHOLD
        search_y = ty + (th / 2) - FocusMover.BORDER_THICKNESS
        for term in terminal.get_parent().get_root_box().iter_terminals():
            sx, sy, sw, sh = self.list_allocation(term)
            if sx <= search_x <= sx + sw and sy <= search_y <= sy + sh:
                term.grab_focus()

    def move_up(self, terminal):
        window_width, window_height = self.window.get_size()
        tx, ty, tw, th = self.list_allocation(terminal)
        if ty == 0:
            return

        search_x = tx + (tw / 2) - FocusMover.BORDER_THICKNESS
        search_y = ty - FocusMover.THRESHOLD
        for term in terminal.get_parent().get_root_box().iter_terminals():
            sx, sy, sw, sh = self.list_allocation(term)
            if sx <= search_x <= sx + sw and sy <= search_y <= sy + sh:
                term.grab_focus()

    def move_down(self, terminal):
        window_width, window_height = self.window.get_size()
        tx, ty, tw, th = self.list_allocation(terminal)

        if ty + th == window_height:
            return

        search_x = tx + (tw / 2) - FocusMover.BORDER_THICKNESS
        search_y = ty + th + FocusMover.THRESHOLD
        for term in terminal.get_parent().get_root_box().iter_terminals():
            sx, sy, sw, sh = self.list_allocation(term)
            if sx <= search_x <= sx + sw and sy <= search_y <= sy + sh:
                term.grab_focus()

    def list_allocation(self, terminal):
        terminal_rect = terminal.get_parent().get_allocation()
        x, y = terminal.get_parent().translate_coordinates(self.window, 0, 0)
        return x, y, terminal_rect.width, terminal_rect.height


class SplitMover():

    THRESHOLD = 35
    STEP = 10

    @classmethod
    def move_up(cls, terminal):
        box = terminal.get_parent()
        while not isinstance(box, RootTerminalBox):
            box = box.get_parent()
            if isinstance(box, DualTerminalBox):
                if box.get_orientation() == Gtk.Orientation.VERTICAL:
                    _, __, p = cls.list_allocation(box)
                    if p - SplitMover.STEP > SplitMover.THRESHOLD:
                        box.set_position(p - SplitMover.STEP)
                    else:
                        box.set_position(SplitMover.THRESHOLD)
                    break

    @classmethod
    def move_down(cls, terminal):
        box = terminal.get_parent()
        while not isinstance(box, RootTerminalBox):
            box = box.get_parent()
            if isinstance(box, DualTerminalBox):
                if box.get_orientation() == Gtk.Orientation.VERTICAL:
                    _, y, p = cls.list_allocation(box)
                    if p + SplitMover.STEP < y - SplitMover.THRESHOLD:
                        box.set_position(p + SplitMover.STEP)
                    else:
                        box.set_position(y - SplitMover.THRESHOLD)
                    break

    @classmethod
    def move_right(cls, terminal):
        box = terminal.get_parent()
        while not isinstance(box, RootTerminalBox):
            box = box.get_parent()
            if isinstance(box, DualTerminalBox):
                if box.get_orientation() == Gtk.Orientation.HORIZONTAL:
                    x, _, p = cls.list_allocation(box)
                    if p + SplitMover.STEP < x - SplitMover.THRESHOLD:
                        box.set_position(p + SplitMover.STEP)
                    else:
                        box.set_position(x - SplitMover.THRESHOLD)
                    break

    @classmethod
    def move_left(cls, terminal):
        box = terminal.get_parent()
        while not isinstance(box, RootTerminalBox):
            box = box.get_parent()
            if isinstance(box, DualTerminalBox):
                if box.get_orientation() == Gtk.Orientation.HORIZONTAL:
                    _, __, p = cls.list_allocation(box)
                    if p - SplitMover.STEP > SplitMover.THRESHOLD:
                        box.set_position(p - SplitMover.STEP)
                    else:
                        box.set_position(SplitMover.THRESHOLD)
                    break

    @classmethod
    def list_allocation(cls, box):
        box_rect = box.get_allocation()
        return box_rect.width, box_rect.height, box.get_position()

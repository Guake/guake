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

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from guake.boxes import DualTerminalBox
from guake.boxes import RootTerminalBox
from guake.boxes import swap_terminal_boxes


class FocusMover:

    THRESHOLD = 10
    BORDER_THICKNESS = 2

    def __init__(self, window):
        self.window = window

    def move_right(self, terminal):
        term = self.find_right(terminal)
        if term is not None:
            term.grab_focus()

    def move_left(self, terminal):
        term = self.find_left(terminal)
        if term is not None:
            term.grab_focus()

    def move_up(self, terminal):
        term = self.find_up(terminal)
        if term is not None:
            term.grab_focus()

    def move_down(self, terminal):
        term = self.find_down(terminal)
        if term is not None:
            term.grab_focus()

    def find_right(self, terminal):
        window_width, _ = self.window.get_size()
        tx, ty, tw, th = self.list_allocation(terminal)

        if tx + tw == window_width:
            return None

        search_x = tx + tw + FocusMover.THRESHOLD
        search_y = ty + (th / 2) - FocusMover.BORDER_THICKNESS
        return self.find_at(terminal, search_x, search_y)

    def find_left(self, terminal):
        tx, ty, tw, th = self.list_allocation(terminal)

        if tx == 0:
            return None

        search_x = tx - FocusMover.THRESHOLD
        search_y = ty + (th / 2) - FocusMover.BORDER_THICKNESS
        return self.find_at(terminal, search_x, search_y)

    def find_up(self, terminal):
        tx, ty, tw, th = self.list_allocation(terminal)
        if ty == 0:
            return None

        search_x = tx + (tw / 2) - FocusMover.BORDER_THICKNESS
        search_y = ty - FocusMover.THRESHOLD
        return self.find_at(terminal, search_x, search_y)

    def find_down(self, terminal):
        _, window_height = self.window.get_size()
        tx, ty, tw, th = self.list_allocation(terminal)

        if ty + th == window_height:
            return None

        search_x = tx + (tw / 2) - FocusMover.BORDER_THICKNESS
        search_y = ty + th + FocusMover.THRESHOLD
        return self.find_at(terminal, search_x, search_y)

    def find_at(self, terminal, search_x, search_y):
        for term in terminal.get_parent().get_root_box().iter_terminals():
            if term is terminal:
                continue
            sx, sy, sw, sh = self.list_allocation(term)
            if sx <= search_x <= sx + sw and sy <= search_y <= sy + sh:
                return term
        return None

    def list_allocation(self, terminal):
        terminal_rect = terminal.get_parent().get_allocation()
        x, y = terminal.get_parent().translate_coordinates(self.window, 0, 0)
        return x, y, terminal_rect.width, terminal_rect.height


class PaneMover(FocusMover):
    def move_right(self, terminal):
        self.move_to_neighbor(terminal, self.find_right(terminal))

    def move_left(self, terminal):
        self.move_to_neighbor(terminal, self.find_left(terminal))

    def move_up(self, terminal):
        self.move_to_neighbor(terminal, self.find_up(terminal))

    def move_down(self, terminal):
        self.move_to_neighbor(terminal, self.find_down(terminal))

    def move_to_neighbor(self, terminal, neighbor):
        if neighbor is None:
            return False

        swap_terminal_boxes(terminal.get_parent(), neighbor.get_parent())
        terminal.grab_focus()
        return True


class SplitMover:

    THRESHOLD = 35
    STEP = 10

    @classmethod
    def move_up(cls, terminal):
        box = terminal.get_parent()
        while not isinstance(box, RootTerminalBox):
            box = box.get_parent()
            if (
                isinstance(box, DualTerminalBox)
                and box.get_orientation() == Gtk.Orientation.VERTICAL
            ):
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
            if (
                isinstance(box, DualTerminalBox)
                and box.get_orientation() == Gtk.Orientation.VERTICAL
            ):
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
            if (
                isinstance(box, DualTerminalBox)
                and box.get_orientation() == Gtk.Orientation.HORIZONTAL
            ):
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
            if (
                isinstance(box, DualTerminalBox)
                and box.get_orientation() == Gtk.Orientation.HORIZONTAL
            ):
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

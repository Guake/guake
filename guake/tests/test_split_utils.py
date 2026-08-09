# -*- coding: utf-8; -*-

from types import SimpleNamespace

from guake.split_utils import SplitMover


def test_split_mover_list_allocation_returns_box_geometry():
    box = SimpleNamespace(
        get_allocation=lambda: SimpleNamespace(width=800, height=600),
        get_position=lambda: 300,
    )

    assert SplitMover.list_allocation(box) == (800, 600, 300)

"""引导层测试：领地/预览计算、脉动、描边绘制。"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame as pg  # noqa: E402
import pytest  # noqa: E402

from floodit import overlay  # noqa: E402
from floodit.fill import region_after, region_cells  # noqa: E402

POS = (0, 0)
SIDE = 10


@pytest.fixture(autouse=True)
def _init():
    pg.init()
    yield


class TestRegionCells:
    def test_single_cell_region(self):
        ary = [[1, 2], [2, 2]]
        assert region_cells(ary) == {(0, 0)}

    def test_uniform_board_is_one_region(self):
        ary = [[3] * 4 for _ in range(4)]
        assert len(region_cells(ary)) == 16

    def test_only_orthogonally_connected_cells_count(self):
        # 对角相连不算连通
        ary = [
            [1, 2],
            [2, 1],
        ]
        assert region_cells(ary) == {(0, 0)}

    def test_region_follows_a_winding_path(self):
        ary = [
            [1, 1, 1],
            [2, 2, 1],
            [1, 1, 1],
        ]
        assert len(region_cells(ary)) == 7

    def test_does_not_mutate_the_board(self):
        ary = [[1, 2], [2, 1]]
        before = [row[:] for row in ary]
        region_cells(ary)
        assert ary == before

    def test_can_start_anywhere(self):
        ary = [[1, 2], [2, 2]]
        assert region_cells(ary, 1, 1) == {(1, 0), (0, 1), (1, 1)}


class TestRegionAfter:
    def test_absorbs_the_adjacent_matching_region(self):
        ary = [
            [1, 2, 2],
            [3, 3, 2],
            [3, 3, 3],
        ]
        # 选 2：左上角变 2，与右上那片 2 连通
        assert region_after(ary, 2) == {(0, 0), (1, 0), (2, 0), (2, 1)}

    def test_choosing_the_current_colour_changes_nothing(self):
        ary = [[1, 2], [2, 2]]
        assert region_after(ary, 1) == region_cells(ary)

    def test_does_not_mutate_the_board(self):
        ary = [[1, 2], [2, 2]]
        before = [row[:] for row in ary]
        region_after(ary, 2)
        assert ary == before

    def test_gain_is_never_negative(self):
        ary = [
            [1, 2, 3],
            [2, 1, 3],
            [3, 3, 1],
        ]
        owned = region_cells(ary)
        for colour in (1, 2, 3):
            assert owned <= region_after(ary, colour), "领地只会变大，不会缩小"


class TestPulse:
    def test_starts_and_returns_to_zero(self):
        p = overlay.Pulse(period=1.0)
        assert p.value == pytest.approx(0.0, abs=1e-6)
        p.update(1.0)
        assert p.value == pytest.approx(0.0, abs=1e-6)

    def test_peaks_at_half_period(self):
        p = overlay.Pulse(period=1.0)
        p.update(0.5)
        assert p.value == pytest.approx(1.0, abs=1e-6)

    def test_value_stays_in_range(self):
        p = overlay.Pulse(period=0.7)
        for _ in range(200):
            assert 0.0 <= p.value <= 1.0
            p.update(1 / 60)

    def test_zero_period_is_inert(self):
        p = overlay.Pulse(period=0)
        p.update(1.0)
        assert p.value == 0.0


class TestDrawing:
    def blank(self, w=40, h=40):
        surf = pg.Surface((w, h))
        surf.fill((0, 0, 0))
        return surf

    def painted(self, surf):
        w, h = surf.get_size()
        return sum(
            surf.get_at((x, y))[:3] != (0, 0, 0) for y in range(h) for x in range(w)
        )

    def test_outline_draws_something(self):
        surf = self.blank()
        overlay.region_outline(surf, {(0, 0)}, POS, SIDE)
        assert self.painted(surf) > 0

    def test_empty_region_draws_nothing(self):
        surf = self.blank()
        overlay.region_outline(surf, set(), POS, SIDE)
        assert self.painted(surf) == 0

    def test_interior_edges_are_not_drawn(self):
        # 2x2 的块只描外缘，中间那条缝不该有线
        surf = self.blank()
        overlay.region_outline(
            surf, {(0, 0), (1, 0), (0, 1), (1, 1)}, POS, SIDE, width=1
        )
        assert surf.get_at((SIDE, SIDE))[:3] == (0, 0, 0), "内部边界被画出来了"

    def test_highlight_covers_only_given_cells(self):
        surf = self.blank()
        overlay.highlight_cells(surf, {(0, 0)}, POS, SIDE)
        assert surf.get_at((SIDE // 2, SIDE // 2))[:3] != (0, 0, 0)
        assert surf.get_at((SIDE + SIDE // 2, SIDE // 2))[:3] == (0, 0, 0)

    def test_empty_highlight_draws_nothing(self):
        surf = self.blank()
        overlay.highlight_cells(surf, set(), POS, SIDE)
        assert self.painted(surf) == 0

    def test_origin_marker_fades_as_it_expands(self):
        early, late = self.blank(80, 80), self.blank(80, 80)
        overlay.origin_marker(early, POS, SIDE, 0.1)
        overlay.origin_marker(late, POS, SIDE, 0.95)
        assert self.painted(early) > self.painted(late)

"""填充动画的时间推进逻辑测试，只测纯计算部分，不需要显示设备。"""

import pytest

from floodit.anim import (
    MAX_LAYER_DELAY,
    FloodAnimation,
    RevealAnimation,
    ease_out_back,
    ease_out_cubic,
    lerp,
    mix,
)

SRC = (10, 20, 30)
DST = (200, 210, 220)


def make_sequence(layers: int, per_layer: int = 1) -> list:
    return [[(x, i, 3) for x in range(per_layer)] for i in range(layers)]


def anim(layers: int = 5, **kwargs) -> FloodAnimation:
    return FloodAnimation(make_sequence(layers), SRC, DST, **kwargs)


class TestEasing:
    def test_lerp_endpoints(self):
        assert lerp(0, 10, 0) == 0
        assert lerp(0, 10, 1) == 10
        assert lerp(0, 10, 0.5) == 5

    def test_mix_endpoints(self):
        assert mix(SRC, DST, 0) == SRC
        assert mix(SRC, DST, 1) == DST

    @pytest.mark.parametrize("ease", [ease_out_cubic, ease_out_back])
    def test_easing_anchored_at_both_ends(self, ease):
        assert ease(0) == pytest.approx(0, abs=1e-9)
        assert ease(1) == pytest.approx(1, abs=1e-9)

    def test_out_cubic_decelerates(self):
        # 前半段走过的距离应超过一半
        assert ease_out_cubic(0.5) > 0.5

    def test_out_back_overshoots(self):
        assert max(ease_out_back(t / 100) for t in range(101)) > 1


class TestSchedule:
    def test_every_cell_is_queued(self):
        a = anim(layers=4)
        assert len(a.pending) == 4
        assert not a.done

    def test_layer_delay_shrinks_as_layers_grow(self):
        few = anim(layers=4, wave_time=0.4)
        many = anim(layers=40, wave_time=0.4)
        assert many.layer_delay < few.layer_delay

    def test_layer_delay_is_capped(self):
        # 层数很少时间隔不应被拉得过长
        assert anim(layers=1, wave_time=10.0).layer_delay <= MAX_LAYER_DELAY

    def test_total_duration_is_independent_of_layer_count(self):
        # 关键性质：整段时长由 wave_time 决定，不随棋盘/区域大小暴涨
        small = anim(layers=10, wave_time=0.4)
        big = anim(layers=200, wave_time=0.4)
        assert big.total == pytest.approx(small.total, abs=0.05)

    def test_empty_sequence_is_immediately_done(self):
        a = FloodAnimation([], SRC, DST)
        assert a.done and a.total == 0.0


class TestProgress:
    def test_progress_is_clamped(self):
        a = anim()
        assert a.progress_of(0.0) == 0.0
        a.update(999)
        assert a.progress_of(0.0) == 1.0

    def test_later_layers_lag_behind_earlier_ones(self):
        a = anim(layers=5)
        a.update(a.layer_delay * 2 + a.cell_duration / 2)
        first = a.progress_of(0.0)
        later = a.progress_of(a.layer_delay * 4)
        assert first > later

    def test_same_elapsed_time_regardless_of_step_size(self):
        # 同样的总时长，拆成多少帧推进都应得到相同进度
        coarse = anim()
        coarse.update(0.1)
        fine = anim()
        for _ in range(10):
            fine.update(0.01)
        assert fine.progress_of(0.0) == pytest.approx(coarse.progress_of(0.0))

    def test_zero_duration_completes_at_once(self):
        a = anim(cell_duration=0)
        assert a.progress_of(0.0) == 1.0


class FakeTable:
    """RevealAnimation 只用到 ary / size / pos / side。"""

    def __init__(self, cols, rows, side=10, pos=(0, 0)):
        self.ary = [[1 for _ in range(cols)] for _ in range(rows)]
        self.size = (cols, rows)
        self.pos_x, self.pos_y = pos
        self.side = side


def reveal(cols=4, rows=3, **kwargs):
    return RevealAnimation(
        FakeTable(cols, rows), {1: (0, 0, 0)}, (255, 255, 255), **kwargs
    )


class TestReveal:
    def test_every_cell_is_queued(self):
        assert len(reveal(4, 3).pending) == 12
        assert not reveal(4, 3).done

    def test_cells_appear_along_the_diagonal(self):
        r = reveal(4, 3)
        starts = {(x, y): s for x, y, s in r.pending}
        # 同一条对角线上的格子同时出现，越靠右下越晚
        assert starts[(1, 0)] == pytest.approx(starts[(0, 1)])
        assert starts[(0, 0)] < starts[(1, 0)] < starts[(2, 0)]

    def test_top_left_starts_immediately(self):
        starts = {(x, y): s for x, y, s in reveal().pending}
        assert starts[(0, 0)] == 0.0

    def test_total_duration_is_bounded_regardless_of_board_size(self):
        # 关键性质：棋盘越大只是每格间隔越短，总时长有上界，
        # 不像"每帧铺一条对角线"那样随边长线性增长。
        ceiling = 0.5 + 0.26  # reveal_time + cell_duration
        sizes = [(2, 2), (4, 4), (15, 15), (40, 40), (200, 200)]
        totals = [reveal(c, r, reveal_time=0.5).total for c, r in sizes]
        assert all(t <= ceiling for t in totals), "总时长突破了上界"
        # 越大的棋盘越贴近上界，但永远收敛而不是线性增长：
        # 边长从 15 涨到 200，总时长变化不到 0.05 秒
        realistic = [reveal(n, n, reveal_time=0.5).total for n in (15, 40, 100, 200)]
        assert max(realistic) - min(realistic) < 0.05

    def test_per_cell_delay_shrinks_as_board_grows(self):
        assert reveal(40, 40).wave_delay < reveal(4, 4).wave_delay

    def test_progress_is_clamped(self):
        r = reveal()
        assert r.progress_of(0.0) == 0.0
        r.update(999)
        assert r.progress_of(0.0) == 1.0

    def test_zero_duration_completes_at_once(self):
        assert reveal(cell_duration=0).progress_of(0.0) == 1.0

    def test_single_cell_board_is_handled(self):
        r = reveal(1, 1)
        assert len(r.pending) == 1
        assert r.total > 0

    def test_finishes_after_total_elapses(self):
        import pygame as pg

        pg.init()
        surface = pg.Surface((100, 100))
        r = reveal(4, 3)
        for _ in range(200):
            r.update(1 / 60)
            r.draw(surface)
            if r.done:
                break
        assert r.done, "铺开动画未在合理时间内结束"

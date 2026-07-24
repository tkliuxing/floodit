"""填充动画的时间推进逻辑测试，只测纯计算部分，不需要显示设备。"""

import pytest

from floodit.anim import (
    MAX_LAYER_DELAY,
    FloodAnimation,
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

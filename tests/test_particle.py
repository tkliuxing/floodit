"""粒子系统的时间推进逻辑测试，只测纯计算部分，不需要显示设备。"""

import random

import pytest

from floodit.particle import (
    Particle,
    ParticleSystem,
    Ripple,
    ScreenShake,
    burst,
    confetti,
)


def make(**kwargs) -> Particle:
    base = dict(x=0.0, y=0.0, vx=0.0, vy=0.0, life=1.0, color=(1, 2, 3), size=2.0)
    base.update(kwargs)
    return Particle(**base)


class TestParticle:
    def test_life_defines_fade(self):
        p = make(life=1.0)
        assert p.fade == 1.0
        p.update(0.5)
        assert p.fade == pytest.approx(0.5)

    def test_dies_after_life_runs_out(self):
        p = make(life=0.2)
        assert p.alive
        p.update(0.3)
        assert not p.alive

    def test_fade_never_goes_negative(self):
        p = make(life=0.1)
        p.update(10)
        assert p.fade == 0.0

    def test_gravity_pulls_down(self):
        p = make(gravity=900, drag=1.0)
        p.update(0.1)
        assert p.vy > 0 and p.y > 0

    def test_zero_gravity_keeps_vertical_speed(self):
        p = make(vy=50, gravity=0, drag=1.0)
        p.update(0.1)
        assert p.vy == pytest.approx(50)

    def test_drag_slows_horizontal_motion(self):
        p = make(vx=100, gravity=0, drag=0.5)
        p.update(0.1)
        assert p.vx < 100

    @pytest.mark.parametrize("vy0", [-80, 0, 60])
    def test_trajectory_is_framerate_independent(self, vy0):
        # 关键性质：同样的总时长，拆成多少帧推进落点应基本一致。
        # 用绝对像素容差——轨迹会穿过原点附近，相对容差在那里没有意义。
        coarse = make(vx=120, vy=vy0)
        coarse.update(0.2)
        fine = make(vx=120, vy=vy0)
        for _ in range(20):
            fine.update(0.01)
        assert fine.x == pytest.approx(coarse.x, abs=1.0)
        assert fine.y == pytest.approx(coarse.y, abs=1.0)

    def test_freefall_matches_closed_form(self):
        # 无阻力自由落体应逼近 y = v0*t + g*t²/2
        p = make(vy=0, gravity=900, drag=1.0)
        for _ in range(50):
            p.update(0.01)
        assert p.y == pytest.approx(0.5 * 900 * 0.5**2, rel=0.02)

    def test_spin_accumulates_angle(self):
        p = make(spin=4.0)
        p.update(0.5)
        assert p.angle == pytest.approx(2.0)


class TestParticleSystem:
    def test_starts_empty(self):
        assert not ParticleSystem().active

    def test_emit_then_expire(self):
        s = ParticleSystem()
        s.emit([make(life=0.1) for _ in range(5)])
        assert len(s) == 5 and s.active
        s.update(0.2)
        assert len(s) == 0 and not s.active

    def test_respects_max_particles(self):
        s = ParticleSystem(max_particles=10)
        s.emit([make() for _ in range(25)])
        assert len(s) == 10

    def test_clear_removes_everything(self):
        s = ParticleSystem()
        s.emit([make() for _ in range(3)])
        s.clear()
        assert not s.active

    def test_only_dead_particles_are_reclaimed(self):
        s = ParticleSystem()
        s.emit([make(life=0.1), make(life=5.0)])
        s.update(0.2)
        assert len(s) == 1


class TestEmitters:
    def test_burst_count_and_origin(self):
        ps = burst((40, 50), (10, 20, 30), count=8, rng=random.Random(0))
        assert len(ps) == 8
        assert all(p.x == 40 and p.y == 50 for p in ps)
        assert all(p.color == (10, 20, 30) for p in ps)

    def test_burst_spreads_in_varied_directions(self):
        ps = burst((0, 0), (0, 0, 0), count=30, rng=random.Random(1))
        assert any(p.vx > 0 for p in ps) and any(p.vx < 0 for p in ps)
        assert any(p.vy > 0 for p in ps) and any(p.vy < 0 for p in ps)

    def test_confetti_starts_at_or_above_top(self):
        import pygame as pg

        area = pg.Rect(10, 100, 200, 300)
        ps = confetti(area, [(1, 1, 1), (2, 2, 2)], count=40, rng=random.Random(2))
        assert len(ps) == 40
        assert all(p.y <= area.top for p in ps)
        assert all(area.left <= p.x <= area.right for p in ps)

    def test_confetti_falls_slower_than_debris(self):
        import pygame as pg

        c = confetti(pg.Rect(0, 0, 10, 10), [(0, 0, 0)], count=1, rng=random.Random(3))
        b = burst((0, 0), (0, 0, 0), count=1, rng=random.Random(3))
        assert c[0].gravity < b[0].gravity


class TestRipple:
    def test_expires_after_duration(self):
        r = Ripple((0, 0), (0, 0, 0), duration=0.3)
        assert r.alive
        r.update(0.4)
        assert not r.alive

    def test_progress_is_monotonic_and_clamped(self):
        r = Ripple((0, 0), (0, 0, 0), duration=0.4)
        seen = []
        for _ in range(8):
            seen.append(r.progress)
            r.update(0.1)
        assert seen == sorted(seen)
        assert r.progress == 1.0

    def test_zero_duration_is_immediately_complete(self):
        assert Ripple((0, 0), (0, 0, 0), duration=0).progress == 1.0


class TestScreenShake:
    def test_expires_after_duration(self):
        s = ScreenShake(duration=0.3)
        assert s.alive
        s.update(0.4)
        assert not s.alive

    def test_offset_decays_to_zero(self):
        s = ScreenShake(amplitude=10, duration=0.4)
        early = max(abs(v) for v in s.offset())
        s.update(0.35)
        late = max(abs(v) for v in s.offset())
        assert late <= early

    def test_dead_shake_has_no_offset(self):
        s = ScreenShake(duration=0.2)
        s.update(0.3)
        assert s.offset() == (0, 0)

    def test_offset_stays_within_amplitude(self):
        s = ScreenShake(amplitude=6, duration=1.0)
        for _ in range(50):
            assert all(abs(v) <= 6 for v in s.offset())
            s.update(0.02)

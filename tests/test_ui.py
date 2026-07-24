"""ui 模块里纯函数的测试：文字反色与步数压力取色。"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from floodit import ui


def test_text_on_dark_background_is_light():
    assert ui.text_on((20, 20, 20)) == ui.TEXT_ON_DARK


def test_text_on_light_background_is_dark():
    assert ui.text_on((240, 240, 240)) == ui.TEXT_ON_LIGHT


def test_pressure_endpoints_and_midpoint():
    assert ui.pressure_color(0.0) == ui.PRESSURE_CALM
    assert ui.pressure_color(0.5) == ui.PRESSURE_WARN
    assert ui.pressure_color(1.0) == ui.PRESSURE_DANGER


def test_pressure_clamps_out_of_range():
    assert ui.pressure_color(-1.0) == ui.PRESSURE_CALM
    assert ui.pressure_color(2.0) == ui.PRESSURE_DANGER


def _midpoint(a, b):
    return tuple((x + y) // 2 for x, y in zip(a, b))


def test_pressure_interpolates_between_stops():
    # 前半段在 从容→警戒 之间线性插值，后半段在 警戒→告急 之间
    assert ui.pressure_color(0.25) == _midpoint(ui.PRESSURE_CALM, ui.PRESSURE_WARN)
    assert ui.pressure_color(0.75) == _midpoint(ui.PRESSURE_WARN, ui.PRESSURE_DANGER)
    # 从容端与告急端必须是分得开的两种颜色
    assert ui.pressure_color(0.0) != ui.pressure_color(1.0)


def test_pressure_returns_int_rgb():
    for r in (0.13, 0.37, 0.62, 0.88):
        color = ui.pressure_color(r)
        assert len(color) == 3
        assert all(isinstance(c, int) and 0 <= c <= 255 for c in color)

"""颜色融合滤镜测试。"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame as pg  # noqa: E402
import pytest  # noqa: E402

from floodit import filters  # noqa: E402

RED = (255, 0, 0)
BLUE = (0, 0, 255)


@pytest.fixture(autouse=True)
def _init():
    pg.init()
    yield


def checkerboard(cols=4, rows=4, side=20):
    """相邻格颜色不同的棋盘，便于观察边界。"""
    surf = pg.Surface((cols * side, rows * side))
    for y in range(rows):
        for x in range(cols):
            color = RED if (x + y) % 2 == 0 else BLUE
            pg.draw.rect(surf, color, pg.Rect(x * side, y * side, side, side))
    return surf


def edge_pixel(surf, side=20):
    """两格交界处的像素。"""
    return surf.get_at((side, side // 2))[:3]


def close(a, b, tol=12):
    return sum((x - y) ** 2 for x, y in zip(a, b, strict=True)) ** 0.5 <= tol


def is_pure(color):
    """是否仍可辨认为某个原色。

    两次重采样会带来 ±2/255 的取整误差（纯红会变成 253,0,0），
    肉眼不可见，所以判定要留容差而不是精确相等。
    """
    return close(color, RED) or close(color, BLUE)


class TestStrength:
    def test_default_actually_blends(self):
        assert filters.CELL_PX and filters.CELL_PX > 0

    def test_default_keeps_the_transition_narrow(self):
        # 选的是最轻的一档：过渡带只有几个像素，格子仍然辨认得出
        width = filters.transition_width(20, filters.CELL_PX)
        assert 0 < width <= 4

    def test_default_leaves_cell_centres_intact(self):
        surf = checkerboard()
        filters.blend_rect(surf, surf.get_rect(), (4, 4), filters.CELL_PX)
        # 每格正中央仍应是本色，只有边界被柔化
        for cy in range(4):
            for cx in range(4):
                px = surf.get_at((cx * 20 + 10, cy * 20 + 10))[:3]
                assert is_pure(px), f"格子 ({cx},{cy}) 中心被融糊了: {px}"


class TestTransitionWidth:
    def test_zero_when_disabled(self):
        assert filters.transition_width(20, None) == 0.0

    def test_zero_when_sampling_at_full_resolution(self):
        assert filters.transition_width(20, 20) == 0.0

    def test_wider_as_cell_px_shrinks(self):
        wide = filters.transition_width(20, 2)
        narrow = filters.transition_width(20, 8)
        assert wide > narrow > 0


class TestBlendRect:
    def test_none_leaves_surface_untouched(self):
        surf = checkerboard()
        before = pg.image.tostring(surf, "RGB")
        filters.blend_rect(surf, surf.get_rect(), (4, 4), None)
        assert pg.image.tostring(surf, "RGB") == before

    def test_full_resolution_leaves_surface_untouched(self):
        # 采样密度等于原图时融合没有意义，应直接跳过
        surf = checkerboard(side=20)
        before = pg.image.tostring(surf, "RGB")
        filters.blend_rect(surf, surf.get_rect(), (4, 4), 20)
        assert pg.image.tostring(surf, "RGB") == before

    def test_blending_softens_the_boundary(self):
        surf = checkerboard()
        assert is_pure(edge_pixel(surf)), "原图交界处应是纯色"
        filters.blend_rect(surf, surf.get_rect(), (4, 4), 2)
        assert not is_pure(edge_pixel(surf)), "融合后交界处应出现中间色"

    def test_stronger_setting_blends_more(self):
        def spread(cell_px):
            surf = checkerboard()
            filters.blend_rect(surf, surf.get_rect(), (4, 4), cell_px)
            # 统计既不是纯红也不是纯蓝的像素
            w, h = surf.get_size()
            return sum(
                not is_pure(surf.get_at((x, y))[:3])
                for y in range(0, h, 2)
                for x in range(0, w, 2)
            )

        assert spread(2) > spread(8)

    def test_only_the_given_rect_is_affected(self):
        surf = pg.Surface((160, 80))
        surf.fill((10, 10, 10))
        board = checkerboard(4, 4, 20)
        surf.blit(board, (0, 0))
        filters.blend_rect(surf, pg.Rect(0, 0, 80, 80), (4, 4), 2)
        # 区域之外的背景不应被碰过
        assert surf.get_at((120, 40))[:3] == (10, 10, 10)

    def test_uniform_area_survives_blending(self):
        # 整块同色时融合前后应几乎一致，不该凭空产生杂色
        surf = pg.Surface((80, 80))
        surf.fill(RED)
        filters.blend_rect(surf, surf.get_rect(), (4, 4), 2)
        assert close(surf.get_at((40, 40))[:3], RED)

    def test_size_is_preserved(self):
        surf = checkerboard()
        size = surf.get_size()
        filters.blend_rect(surf, surf.get_rect(), (4, 4), 4)
        assert surf.get_size() == size

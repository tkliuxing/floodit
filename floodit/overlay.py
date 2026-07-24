"""棋盘上的引导性标记：领地描边、悬停预览、起点脉动。

这些都画在**窗口副本**上、且在融合滤镜之后，所以描边始终清晰，
不会被融合糊掉，也不会弄脏离屏画面。
"""

import math

import pygame as pg

# 描边采用"外亮内暗"的双层画法：任意底色上都能看清
OUTLINE_LIGHT = (255, 255, 255)
OUTLINE_DARK = (32, 36, 44)
OUTLINE_WIDTH = 3

# 悬停预览的覆盖强度
PREVIEW_ALPHA = 110
# 预览区域外缘的描边粗细
PREVIEW_OUTLINE_WIDTH = 2

# 起点脉动一个来回的时长（秒）
PULSE_PERIOD = 1.4
# 脉动圆环的最小/最大半径，相对格子边长的倍数
PULSE_MIN = 0.9
PULSE_MAX = 1.5


def _edges(cells: set):
    """逐格找出与区域外相邻的边，返回 (起点, 终点) 的序列。"""
    for x, y in cells:
        yield (x, y, "top") if (x, y - 1) not in cells else None
        yield (x, y, "bottom") if (x, y + 1) not in cells else None
        yield (x, y, "left") if (x - 1, y) not in cells else None
        yield (x, y, "right") if (x + 1, y) not in cells else None


def _edge_line(x: int, y: int, kind: str, pos: tuple, side: int):
    left = pos[0] + x * side
    top = pos[1] + y * side
    if kind == "top":
        return (left, top), (left + side, top)
    if kind == "bottom":
        return (left, top + side), (left + side, top + side)
    if kind == "left":
        return (left, top), (left, top + side)
    return (left + side, top), (left + side, top + side)


def region_outline(
    surface: pg.Surface,
    cells: set,
    pos: tuple,
    side: int,
    color: tuple = OUTLINE_LIGHT,
    width: int = OUTLINE_WIDTH,
    inner: tuple = OUTLINE_DARK,
):
    """沿区域外缘描边。

    cells: 区域内格子的 (x, y) 集合
    pos: 棋盘左上角坐标
    side: 格子边长
    inner: 叠在外描边内侧的深色细线；为 None 时只画一层
    """
    if not cells:
        return
    borders = [e for e in _edges(cells) if e]
    for x, y, kind in borders:
        start, end = _edge_line(x, y, kind, pos, side)
        pg.draw.line(surface, color, start, end, width)
    if inner is not None:
        for x, y, kind in borders:
            start, end = _edge_line(x, y, kind, pos, side)
            pg.draw.line(surface, inner, start, end, 1)


def highlight_cells(
    surface: pg.Surface,
    cells: set,
    pos: tuple,
    side: int,
    alpha: int = PREVIEW_ALPHA,
    color: tuple = (255, 255, 255),
):
    """给一组格子盖上半透明色，用于预览"这一步会吃掉哪些格"。"""
    if not cells:
        return
    veil = pg.Surface((side, side), pg.SRCALPHA)
    veil.fill((*color, alpha))
    for x, y in cells:
        surface.blit(veil, (pos[0] + x * side, pos[1] + y * side))


class Pulse:
    """dt 驱动的往复脉动，取值在 0..1 之间平滑摆动。"""

    def __init__(self, period: float = PULSE_PERIOD):
        self.period = period
        self.elapsed = 0.0

    def update(self, dt: float):
        self.elapsed = (self.elapsed + dt) % self.period if self.period else 0.0

    @property
    def value(self) -> float:
        if not self.period:
            return 0.0
        # 用余弦而不是锯齿，两端才会自然减速
        return (1 - math.cos(self.elapsed / self.period * math.tau)) / 2


def origin_marker(
    surface: pg.Surface,
    pos: tuple,
    side: int,
    phase: float,
    color: tuple = OUTLINE_LIGHT,
):
    """在起点格上画一个脉动圆环，把视线引到该看的地方。

    phase: 0..1 的脉动相位，通常来自 Pulse.value
    """
    center = (pos[0] + side // 2, pos[1] + side // 2)
    radius = round(side * (PULSE_MIN + (PULSE_MAX - PULSE_MIN) * phase))
    # 越张开越淡，像水波散开
    width = max(1, round(3 * (1 - phase)))
    ring = pg.Surface((radius * 2 + 4, radius * 2 + 4), pg.SRCALPHA)
    pg.draw.circle(
        ring,
        (*color, round(220 * (1 - phase))),
        (radius + 2, radius + 2),
        radius,
        width,
    )
    surface.blit(ring, ring.get_rect(center=center))

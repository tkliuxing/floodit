"""按时间推进的填充动画。

动画进度只由累积的真实时间决定，与帧率和棋盘尺寸都无关：
整段波纹的时长固定为 WAVE_TIME，层数越多每层间隔越短。
"""

import pygame as pg

# 整段波纹从起点扩散到最远一层的目标时长（秒）
WAVE_TIME = 0.45
# 单个格子从旧色变到新色的时长（秒）
CELL_DURATION = 0.18
# 每层之间的最大间隔，避免只有一两层时波纹慢得像卡住
MAX_LAYER_DELAY = 0.05
# 格子弹出时的起始缩放比例
MIN_SCALE = 0.55
# 刚变色时叠加的高光强度，随进度衰减到 0
FLASH = 0.35


def lerp(a: float, b: float, t: float) -> float:
    """线性插值。"""
    return a + (b - a) * t


def mix(c1: tuple, c2: tuple, t: float) -> tuple:
    """按 t 在两个颜色之间插值。"""
    return tuple(round(lerp(a, b, t)) for a, b in zip(c1, c2, strict=True))


def ease_out_cubic(t: float) -> float:
    """末端减速，用于颜色过渡。"""
    return 1 - (1 - t) ** 3


def ease_out_back(t: float, overshoot: float = 1.70158) -> float:
    """末端回弹（会略微超过 1），用于格子弹出。"""
    t -= 1
    return 1 + (overshoot + 1) * t**3 + overshoot * t**2


class FloodAnimation:
    """把 BFS 分层结果按时间铺开播放的填充动画。"""

    def __init__(
        self,
        sequence: list,
        src_color: tuple,
        dst_color: tuple,
        wave_time: float = WAVE_TIME,
        cell_duration: float = CELL_DURATION,
    ):
        """
        sequence: get_fill_sequence 的分层结果
        src_color: 区域填充前的颜色（同一连通区域必然同色）
        dst_color: 填充后的颜色
        """
        self.src_color = src_color
        self.dst_color = dst_color
        self.cell_duration = cell_duration

        layers = len(sequence)
        self.layer_delay = min(MAX_LAYER_DELAY, wave_time / layers) if layers else 0.0
        # 每格记录 (x, y, 该格的起始时间)
        self.pending = [
            (x, y, i * self.layer_delay)
            for i, layer in enumerate(sequence)
            for x, y, _ in layer
        ]
        self.elapsed = 0.0
        self.total = (layers - 1) * self.layer_delay + cell_duration if layers else 0.0

    @property
    def done(self) -> bool:
        """所有格子都已完成过渡。"""
        return not self.pending

    def progress_of(self, start: float) -> float:
        """某个格子当前的过渡进度，取值 0..1。"""
        if self.cell_duration <= 0:
            return 1.0
        return max(0.0, min(1.0, (self.elapsed - start) / self.cell_duration))

    def update(self, dt: float) -> list:
        """按经过的秒数推进动画，返回本帧刚开始过渡的格子坐标。

        返回值用于在波前撒碎屑——只有刚"点亮"的格子才该迸粒子。
        """
        before = self.elapsed
        self.elapsed += dt
        return [
            (x, y) for x, y, start in self.pending if before <= start < self.elapsed
        ]

    def draw(self, screen: pg.Surface, pos: tuple, side: int):
        """只重绘正在过渡的格子（脏矩形），完成的格子移出队列。"""
        still_pending = []
        for x, y, start in self.pending:
            progress = self.progress_of(start)
            if progress <= 0:
                # 尚未开始，屏幕上仍是旧色，无需重绘
                still_pending.append((x, y, start))
                continue

            left = pos[0] + x * side
            top = pos[1] + y * side
            # 先铺旧色作底，再把新色的方块弹出来
            pg.draw.rect(screen, self.src_color, pg.Rect(left, top, side, side))

            scale = MIN_SCALE + (1 - MIN_SCALE) * ease_out_back(progress)
            inner = max(1, min(side, round(side * scale)))
            offset = (side - inner) // 2
            color = mix(
                self.dst_color, (255, 255, 255), FLASH * (1 - ease_out_cubic(progress))
            )
            inner_rect = pg.Rect(left + offset, top + offset, inner, inner)
            pg.draw.rect(screen, color, inner_rect)

            if progress < 1:
                still_pending.append((x, y, start))
        self.pending = still_pending

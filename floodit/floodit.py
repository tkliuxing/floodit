#!/usr/bin/env python
import sys

import pygame as pg

from . import fill
from .anim import FloodAnimation
from .event import ClickEventListen
from .particle import ParticleSystem, Ripple, ScreenShake, burst, confetti
from .ui import Button, GameTable

ZOOM = 1
WINDOW_SIZE = (int(580 * ZOOM), int(340 * ZOOM))
ORIGIN_POINT = (int(20 * ZOOM), int(20 * ZOOM))
TABLE_SIZE = (15, 15)
BLOCK_SIZE = int(20 * ZOOM)
# 六色需要两两都能一眼分开，否则看不出连通区域的边界。
# 色值经 CIE Lab ΔE 校验：最小两两 ΔE=71.6，最小亮度差=17.1
# （纯 RGB 原色为 58.0 / 29.1，等亮度的柔和配色仅 33.9 / 2.7）。
# 亮度刻意铺开，使得即便色相相近，明暗差也能撑出边界。
BLOCK_COLORS = {
    1: (214, 49, 49),  # 红   luma  98
    2: (40, 85, 149),  # 蓝   luma  79
    3: (74, 235, 74),  # 绿   luma 169
    4: (235, 205, 117),  # 沙黄 luma 204
    5: (74, 235, 235),  # 青   luma 187
    6: (235, 74, 235),  # 品红 luma 141
}

BG_COLOR = (238, 240, 243)
TEXT_COLOR = (60, 64, 72)
WIN_COLOR = (56, 142, 60)
LOSE_COLOR = (198, 70, 70)

MAX_STEPS = 30

# 单帧最大步进时间，防止窗口卡顿/拖动后一帧把整段动画跳完
MAX_FRAME_TIME = 0.1

# 波前每帧最多有几格迸碎屑，以及每格迸几颗
DEBRIS_PER_FRAME = 6
DEBRIS_PER_CELL = 4


class Floodit:
    """游戏主类"""

    def __init__(
        self,
        colors: dict = None,
        window_size: tuple = WINDOW_SIZE,
        table_size: tuple = TABLE_SIZE,
        table_position: tuple = ORIGIN_POINT,
        block_side: int = BLOCK_SIZE,
    ):
        self.COLORS = colors if colors is not None else BLOCK_COLORS
        self.WINDOW_SIZE = window_size
        self.TABLE_SIZE = table_size
        self.TABLE_POSITION = table_position
        self.BLOCK_SIDE = block_side
        self.display = pg.display.set_mode(self.WINDOW_SIZE)
        # 游戏画面先画到离屏 surface，再整体贴到窗口上。
        # 这样震动可以整体位移，粒子叠在最上层且不会弄脏底下的画面。
        self.screen = pg.Surface(self.WINDOW_SIZE)
        pg.display.set_caption("Flood it!")
        pg.font.init()
        self.font = pg.font.SysFont("AR PL UMing CN", int(20 * ZOOM))
        self.screen.fill(BG_COLOR)
        self.table = GameTable(
            self.COLORS.keys(),
            self.TABLE_SIZE,
            self.TABLE_POSITION,
            self.BLOCK_SIDE,
        )

        # 色块按钮起始坐标
        cl_x = self.TABLE_POSITION[0] + self.BLOCK_SIDE * (self.TABLE_SIZE[0] + 1)
        cl_y = self.TABLE_POSITION[1] + self.BLOCK_SIDE * (self.TABLE_SIZE[1] - 1)

        # "New game" 按钮
        x = self.TABLE_POSITION[0] + self.BLOCK_SIDE * (self.TABLE_SIZE[0] + 1)
        w = self.BLOCK_SIDE * (len(self.COLORS) * 2 - 1)
        y = self.TABLE_POSITION[1]
        h = self.BLOCK_SIDE * 2
        self.rb = Button(
            (x, y),
            (w, h),
            text="New Game!",
            fontsize=int(20 * ZOOM),
            radius=int(8 * ZOOM),
        )

        self.events = ClickEventListen()
        self.events.register(self.rb, self.reset)

        # 初始化色块按钮
        left = cl_x
        self.color_buttons = []
        for k, v in self.COLORS.items():
            button = Button(
                (left, cl_y),
                (self.BLOCK_SIDE, self.BLOCK_SIDE),
                color=v,
                fontsize=int(20 * ZOOM),
                radius=int(5 * ZOOM),
            )
            self.color_buttons.append(button)
            self.events.register(button, self.colors_click, number=k)
            left += self.BLOCK_SIDE * 2

        self._draw_buttons()
        self.table.draw(self.screen, self.COLORS)
        self.won = False
        self.lost = False
        self.steps = 0
        self.animation = None
        self.statusrect = None
        self.particles = ParticleSystem()
        self.ripples = []
        self.shake = None
        self._draw_steps()

    def show(self):
        """把离屏画面贴到窗口，再把特效叠在最上层。"""
        offset = self.shake.offset() if self.shake else (0, 0)
        if offset != (0, 0):
            self.display.fill(BG_COLOR)
        self.display.blit(self.screen, offset)
        for ripple in self.ripples:
            ripple.draw(self.display)
        self.particles.draw(self.display)
        pg.display.flip()

    def update_effects(self, dt: float):
        """推进粒子、涟漪和震动。特效不参与任何游戏逻辑。"""
        self.particles.update(dt)
        for ripple in self.ripples:
            ripple.update(dt)
        self.ripples = [r for r in self.ripples if r.alive]
        if self.shake:
            self.shake.update(dt)
            if not self.shake.alive:
                self.shake = None

    @property
    def effects_active(self) -> bool:
        return bool(self.particles.active or self.ripples or self.shake)

    def _draw_buttons(self):
        """重绘全部按钮，使悬停/按下状态即时可见。"""
        self.rb.show(self.screen)
        for button in self.color_buttons:
            button.show(self.screen)

    def _draw_steps(self):
        """在 New Game 按钮下方显示当前步数。"""
        x = self.rb.x
        y = self.rb.y1 + int(10 * ZOOM)
        w = self.rb.w
        h = int(24 * ZOOM)
        pg.draw.rect(self.screen, BG_COLOR, pg.Rect(x, y, w, h))
        color = LOSE_COLOR if self.steps >= MAX_STEPS else TEXT_COLOR
        text = self.font.render(f"Steps: {self.steps} / {MAX_STEPS}", True, color)
        tr = text.get_rect()
        tr.centerx = x + w // 2
        tr.centery = y + h // 2
        self.screen.blit(text, tr)

    def colors_click(self, number: int = None):
        assert number is not None, "CLICK ERROR!"
        if self.won or self.lost or self.animation:
            return
        if number in self.COLORS:
            button = self.color_buttons[list(self.COLORS).index(number)]
            self.ripples.append(Ripple(button.rect.center, self.COLORS[number]))
            src = self.table.ary[0][0]
            sequence = fill.get_fill_sequence(self.table.ary, number)
            self.steps += 1
            self._draw_steps()
            if sequence:
                # 逻辑状态立刻落盘，屏幕上的旧色由动画逐格覆盖
                for layer in sequence:
                    for x, y, color in layer:
                        self.table.ary[y][x] = color
                self.animation = FloodAnimation(
                    sequence, self.COLORS[src], self.COLORS[number]
                )
            else:
                self._check_end()
        self.show()

    def _check_end(self):
        """判定胜负并显示提示，在动画播完后调用。"""
        if fill.filldone(self.table.ary):
            self._show_status("You Win!", WIN_COLOR)
            self.won = True
            board = pg.Rect(
                self.TABLE_POSITION[0],
                self.TABLE_POSITION[1],
                self.TABLE_SIZE[0] * self.BLOCK_SIDE,
                self.TABLE_SIZE[1] * self.BLOCK_SIDE,
            )
            self.particles.emit(confetti(board, list(self.COLORS.values())))
        elif self.steps >= MAX_STEPS:
            self._show_status("Game Over!", LOSE_COLOR)
            self.lost = True
            self.shake = ScreenShake()

    def update_animation(self, dt: float):
        """按经过的秒数推进填充动画，播完后收尾。"""
        started = self.animation.update(dt)
        self._emit_debris(started, self.animation.dst_color)
        self.animation.draw(self.screen, self.TABLE_POSITION, self.BLOCK_SIDE)
        if self.animation.done:
            self.animation = None
            # 动画逐格绘制，收尾时整块重绘一次以保证和逻辑状态一致
            self.table.draw(self.screen, self.COLORS)
            self._check_end()

    def _emit_debris(self, cells: list, color: tuple):
        """在波前刚点亮的格子上撒碎屑。

        整块区域可能有几百格，每格都迸粒子既看不清也拖慢帧率，
        所以按固定间隔抽样。
        """
        if not cells:
            return
        stride = max(1, len(cells) // DEBRIS_PER_FRAME)
        half = self.BLOCK_SIDE // 2
        for x, y in cells[::stride]:
            center = (
                self.TABLE_POSITION[0] + x * self.BLOCK_SIDE + half,
                self.TABLE_POSITION[1] + y * self.BLOCK_SIDE + half,
            )
            self.particles.emit(burst(center, color, count=DEBRIS_PER_CELL))

    def _show_status(self, message: str, color: tuple):
        """在棋盘右侧中央显示胜负提示。"""
        font = pg.font.SysFont("AR PL UMing CN", int(28 * ZOOM))
        text = font.render(message, True, color)
        self.statusrect = text.get_rect()
        self.statusrect.centerx = (self.rb.x + self.rb.x1) // 2
        self.statusrect.centery = self.rb.y1 * 3
        pg.draw.rect(self.screen, BG_COLOR, self.statusrect)
        self.screen.blit(text, self.statusrect)

    def reset(self):
        self.won = False
        self.lost = False
        self.steps = 0
        self.animation = None
        self.particles.clear()
        self.ripples.clear()
        self.shake = None
        self.table = GameTable(
            self.COLORS.keys(),
            self.TABLE_SIZE,
            self.TABLE_POSITION,
            self.BLOCK_SIDE,
        )
        self.table.draw(self.screen, self.COLORS)
        if self.statusrect:
            pg.draw.rect(self.screen, BG_COLOR, self.statusrect)
            self.statusrect = None
        self._draw_steps()
        self.show()

    def mainloop(self):
        clock = pg.time.Clock()
        while True:
            dt = min(clock.tick(60) / 1000.0, MAX_FRAME_TIME)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    sys.exit(0)
                self.events.listen(event)

            if self.animation:
                self.update_animation(dt)
            self.update_effects(dt)

            self._draw_buttons()
            self.show()

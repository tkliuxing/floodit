#!/usr/bin/env python
import sys

import pygame as pg

from . import fill, filters, fonts
from .anim import FloodAnimation, RevealAnimation
from .event import ClickEventListen
from .i18n import Translator
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

# --- 版面参数 ---------------------------------------------------------------
# 尺寸统一以格子边长 BLOCK_SIDE 为单位表示，改缩放或格子大小时版面自动跟随。
# 棋盘与右侧面板之间空出几格
PANEL_GUTTER_BLOCKS = 1
# 色块按钮的间距，2 表示"一格按钮 + 一格空隙"
SWATCH_STRIDE_BLOCKS = 2
# New Game 按钮高度占几格
NEW_GAME_HEIGHT_BLOCKS = 2
# 步数文字区域与 New Game 按钮之间的间距、以及该区域的高度（像素）
STEPS_MARGIN_TOP = int(10 * ZOOM)
STEPS_HEIGHT = int(24 * ZOOM)
# 胜负提示与步数文字之间的间距，以及提示区域的高度（像素）
STATUS_MARGIN_TOP = int(28 * ZOOM)
STATUS_HEIGHT = int(40 * ZOOM)
# 字号
FONT_SIZE = int(20 * ZOOM)
STATUS_FONT_SIZE = int(28 * ZOOM)
# 圆角半径
NEW_GAME_RADIUS = int(8 * ZOOM)
SWATCH_RADIUS = int(5 * ZOOM)


class Floodit:
    """游戏主类"""

    def __init__(
        self,
        colors: dict = None,
        window_size: tuple = WINDOW_SIZE,
        table_size: tuple = TABLE_SIZE,
        table_position: tuple = ORIGIN_POINT,
        block_side: int = BLOCK_SIZE,
        lang: str = None,
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
        pg.font.init()

        self.i18n = Translator(lang)
        # 字体按"所有语言的文案合集"来挑，否则运行时切到中文会变成空白
        sample = self.i18n.sample()
        self.font = fonts.resolve(FONT_SIZE, sample)
        self.status_font = fonts.resolve(STATUS_FONT_SIZE, sample)
        pg.display.set_caption(self.i18n.t("title"))

        self.screen.fill(BG_COLOR)
        self.table = GameTable(
            self.COLORS.keys(),
            self.TABLE_SIZE,
            self.TABLE_POSITION,
            self.BLOCK_SIDE,
        )

        # 右侧面板的左边缘，与棋盘之间空出 PANEL_GUTTER_BLOCKS 格
        panel_x = self.TABLE_POSITION[0] + self.BLOCK_SIDE * (
            self.TABLE_SIZE[0] + PANEL_GUTTER_BLOCKS
        )
        # 面板宽度正好容纳一排色块按钮（末尾不留空隙）
        panel_w = self.BLOCK_SIDE * (len(self.COLORS) * SWATCH_STRIDE_BLOCKS - 1)
        # 色块按钮与棋盘底部对齐
        swatch_y = self.TABLE_POSITION[1] + self.BLOCK_SIDE * (self.TABLE_SIZE[1] - 1)

        self.rb = Button(
            (panel_x, self.TABLE_POSITION[1]),
            (panel_w, self.BLOCK_SIDE * NEW_GAME_HEIGHT_BLOCKS),
            text=self.i18n.t("new_game"),
            font=self.font,
            radius=NEW_GAME_RADIUS,
        )

        # 步数与胜负提示的位置由按钮底边推出，不再依赖魔数
        self.steps_rect = pg.Rect(
            panel_x, self.rb.y1 + STEPS_MARGIN_TOP, panel_w, STEPS_HEIGHT
        )
        self.status_rect = pg.Rect(
            panel_x,
            self.steps_rect.bottom + STATUS_MARGIN_TOP,
            panel_w,
            STATUS_HEIGHT,
        )

        self.events = ClickEventListen()
        self.events.register(self.rb, self.reset)

        # 初始化色块按钮
        left = panel_x
        self.color_buttons = []
        for k, v in self.COLORS.items():
            button = Button(
                (left, swatch_y),
                (self.BLOCK_SIDE, self.BLOCK_SIDE),
                color=v,
                font=self.font,
                radius=SWATCH_RADIUS,
            )
            self.color_buttons.append(button)
            self.events.register(button, self.colors_click, number=k)
            left += self.BLOCK_SIDE * SWATCH_STRIDE_BLOCKS

        self._register_keys()

        self.won = False
        self.lost = False
        self.steps = 0
        self.animation = None
        self.reveal = None
        self.particles = ParticleSystem()
        self.ripples = []
        self.shake = None

        self._draw_buttons()
        self._draw_steps()
        self._start_reveal()

    def _register_keys(self):
        """绑定键盘快捷键。"""
        # 数字键 1..9 依次对应调色板上的颜色
        for index, number in enumerate(self.COLORS):
            if index >= 9:
                break
            digit = str(index + 1)
            self.events.register_key(
                [getattr(pg, f"K_{digit}"), getattr(pg, f"K_KP{digit}")],
                self.colors_click,
                number=number,
            )
        self.events.register_key([pg.K_r, pg.K_F2], self.reset)
        self.events.register_key([pg.K_l], self.cycle_language)
        self.events.register_key([pg.K_ESCAPE, pg.K_q], self.quit)

    def quit(self):
        sys.exit(0)

    def cycle_language(self):
        """切换界面语言并重绘所有文案。"""
        self.i18n.cycle()
        pg.display.set_caption(self.i18n.t("title"))
        self.rb.set_text(self.i18n.t("new_game"))
        self._draw_buttons()
        self._draw_steps()
        # 胜负提示正显示时也要跟着换语言
        if self.won:
            self._show_status("win", WIN_COLOR)
        elif self.lost:
            self._show_status("lose", LOSE_COLOR)
        self.show()

    @property
    def board_rect(self) -> pg.Rect:
        """棋盘占据的矩形区域。"""
        return pg.Rect(
            self.TABLE_POSITION[0],
            self.TABLE_POSITION[1],
            self.TABLE_SIZE[0] * self.BLOCK_SIDE,
            self.TABLE_SIZE[1] * self.BLOCK_SIDE,
        )

    def _start_reveal(self):
        """开局把棋盘逐格铺开。"""
        pg.draw.rect(self.screen, BG_COLOR, self.board_rect)
        self.reveal = RevealAnimation(self.table, self.COLORS, BG_COLOR)

    def update_reveal(self, dt: float):
        """推进开局铺开动画。"""
        self.reveal.update(dt)
        self.reveal.draw(self.screen)
        if self.reveal.done:
            self.reveal = None
            self.table.draw(self.screen, self.COLORS)

    def show(self):
        """把离屏画面贴到窗口，再把特效叠在最上层。"""
        offset = self.shake.offset() if self.shake else (0, 0)
        if offset != (0, 0):
            self.display.fill(BG_COLOR)
        self.display.blit(self.screen, offset)
        # 融合滤镜作用在窗口副本上，不动离屏画面，
        # 所以它对铺开/波纹/震动一视同仁，也不会污染后续帧
        filters.blend_rect(
            self.display, self.board_rect.move(offset), self.TABLE_SIZE, filters.CELL_PX
        )
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
        pg.draw.rect(self.screen, BG_COLOR, self.steps_rect)
        color = LOSE_COLOR if self.steps >= MAX_STEPS else TEXT_COLOR
        message = self.i18n.t("steps", steps=self.steps, max_steps=MAX_STEPS)
        text = self.font.render(message, True, color)
        self.screen.blit(text, text.get_rect(center=self.steps_rect.center))

    def colors_click(self, number: int = None):
        assert number is not None, "CLICK ERROR!"
        if self.won or self.lost or self.animation or self.reveal:
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
            self._show_status("win", WIN_COLOR)
            self.won = True
            self.particles.emit(confetti(self.board_rect, list(self.COLORS.values())))
        elif self.steps >= MAX_STEPS:
            self._show_status("lose", LOSE_COLOR)
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

    def _show_status(self, key: str, color: tuple):
        """在步数下方显示胜负提示。"""
        pg.draw.rect(self.screen, BG_COLOR, self.status_rect)
        text = self.status_font.render(self.i18n.t(key), True, color)
        self.screen.blit(text, text.get_rect(center=self.status_rect.center))

    def _clear_status(self):
        pg.draw.rect(self.screen, BG_COLOR, self.status_rect)

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
        self._clear_status()
        self._draw_steps()
        self._start_reveal()
        self.show()

    def mainloop(self):
        clock = pg.time.Clock()
        while True:
            dt = min(clock.tick(60) / 1000.0, MAX_FRAME_TIME)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    sys.exit(0)
                self.events.listen(event)

            if self.reveal:
                self.update_reveal(dt)
            elif self.animation:
                self.update_animation(dt)
            self.update_effects(dt)

            self._draw_buttons()
            self.show()

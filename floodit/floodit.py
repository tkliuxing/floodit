#!/usr/bin/env python
import sys

import pygame as pg

from . import fill
from .event import ClickEventListen
from .ui import Button, GameTable


ZOOM = 1
WINDOW_SIZE = (int(580 * ZOOM), int(340 * ZOOM))
ORIGIN_POINT = (int(20 * ZOOM), int(20 * ZOOM))
TABLE_SIZE = (15, 15)
BLOCK_SIZE = int(20 * ZOOM)
BLOCK_COLORS = {
    1: (255, 0, 0),
    2: (0, 0, 255),
    3: (0, 255, 0),
    4: (255, 255, 0),
    5: (0, 255, 255),
    6: (255, 0, 255),
}

MAX_STEPS = 30


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
        self.screen = pg.display.set_mode(self.WINDOW_SIZE)
        pg.display.set_caption("Flood it!")
        pg.font.init()
        self.font = pg.font.SysFont("AR PL UMing CN", int(20 * ZOOM))
        self.screen.fill((200, 200, 200))
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
        self.rb = Button((x, y), (w, h), text="New Game!", fontsize=int(20 * ZOOM))
        self.rb.show(self.screen)

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
            )
            button.show(self.screen)
            self.color_buttons.append(button)
            self.events.register(button, self.colors_click, number=k)
            left += self.BLOCK_SIDE * 2

        self.table.draw(self.screen, BLOCK_COLORS)
        self.won = False
        self.lost = False
        self.steps = 0
        self.statusrect = None
        self._draw_steps()

    def show(self):
        pg.display.flip()

    def _draw_steps(self):
        """在 New Game 按钮下方显示当前步数。"""
        x = self.rb.x
        y = self.rb.y1 + int(10 * ZOOM)
        w = self.rb.w
        h = int(24 * ZOOM)
        pg.draw.rect(self.screen, (200, 200, 200), pg.Rect(x, y, w, h))
        color = (180, 0, 0) if self.steps >= MAX_STEPS else (50, 50, 50)
        text = self.font.render(f"Steps: {self.steps} / {MAX_STEPS}", True, color)
        tr = text.get_rect()
        tr.centerx = x + w // 2
        tr.centery = y + h // 2
        self.screen.blit(text, tr)

    def colors_click(self, number: int = None):
        assert number is not None, "CLICK ERROR!"
        if self.won or self.lost:
            return
        if number in self.COLORS:
            fill.fill(self.table, number, x=0, y=0)
            self.steps += 1
            self.table.draw(self.screen, BLOCK_COLORS)
            self._draw_steps()
            if fill.filldone(self.table):
                self._show_status("You Win!", (0, 140, 0))
                self.won = True
            elif self.steps >= MAX_STEPS:
                self._show_status("Game Over!", (180, 0, 0))
                self.lost = True
        self.show()

    def _show_status(self, message: str, color: tuple):
        """在棋盘右侧中央显示胜负提示。"""
        font = pg.font.SysFont("AR PL UMing CN", int(28 * ZOOM))
        text = font.render(message, True, color)
        self.statusrect = text.get_rect()
        self.statusrect.centerx = (self.rb.x + self.rb.x1) // 2
        self.statusrect.centery = self.rb.y1 * 3
        pg.draw.rect(self.screen, (200, 200, 200), self.statusrect)
        self.screen.blit(text, self.statusrect)

    def reset(self):
        self.won = False
        self.lost = False
        self.steps = 0
        self.table = GameTable(
            self.COLORS.keys(),
            self.TABLE_SIZE,
            self.TABLE_POSITION,
            self.BLOCK_SIDE,
        )
        self.table.draw(self.screen, BLOCK_COLORS)
        if self.statusrect:
            pg.draw.rect(self.screen, (200, 200, 200), self.statusrect)
            self.statusrect = None
        self._draw_steps()
        self.show()

    def mainloop(self):
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    sys.exit(0)
                self.events.listen(event)


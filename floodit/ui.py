import pygame as pg
from .datastruct import Table


class Button:
    """游戏操作按钮"""

    def __init__(
        self,
        pos: tuple,
        size: tuple,
        color: tuple = (255, 255, 255),
        text: str = "",
        fontname: str = "AR PL UMing CN",
        fontsize: int = 20,
    ):
        """
        生成按钮。

        pos: (坐标x, 坐标y)
        size: (宽度, 高度)
        color: 按钮背景色
        text: 按钮文字
        fontname: 按钮字体名称
        fontsize: 按钮字体大小
        """
        self.x = pos[0]
        self.y = pos[1]
        self.w = size[0]
        self.h = size[1]
        self.x1 = self.x + self.w
        self.y1 = self.y + self.h
        self.color = color
        self.rect = pg.Rect(pos, size)
        self.font = pg.font.SysFont(fontname, fontsize)
        self.text = self.font.render(text, True, (0, 0, 0))
        self.textpos = self.text.get_rect()
        self.textpos.centerx = (self.x + self.x1) // 2
        self.textpos.centery = (self.y + self.y1) // 2

    def show(self, screen: pg.Surface):
        """在指定的 screen 上绘制按钮。"""
        pg.draw.rect(screen, self.color, self.rect)
        screen.blit(self.text, self.textpos)

    def check_click(self, pos: tuple) -> bool:
        """检查是否被点击，pos 为点击时的坐标。"""
        return self.x < pos[0] < self.x1 and self.y < pos[1] < self.y1


class GameTable(Table):
    """游戏棋盘格"""

    def __init__(self, numbers: list, size: tuple, pos: tuple, side: int):
        """
        生成二维表，并附带位置和格子边长属性。

        pos: 起始位置，如 (0, 0)
        side: 每格的边长（像素）
        """
        super().__init__(numbers, size)
        self.pos_x = pos[0]
        self.pos_y = pos[1]
        self.pos_x1 = pos[0] + self.size[0] * side
        self.pos_y1 = pos[1] + self.size[1] * side
        self.side = side

    def draw(self, screen: pg.Surface, colors: dict):
        """在指定的 screen 上绘制棋盘格。"""
        top = self.pos_y
        for row in self:
            left = self.pos_x
            for cell in row:
                rect = pg.Rect(left, top, self.side, self.side)
                pg.draw.rect(screen, colors[cell], rect)
                left += self.side
            top += self.side

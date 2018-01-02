# -*- coding:utf-8 -*-
import pygame as pg
from datastruct import Table


class Button(object):
    """游戏操作按钮"""

    def __init__(self, pos, size, color=(255, 255, 255), text="", fontname="AR PL UMing CN", fontsize=20):
        """
            生成按钮
            pos: (坐标x,坐标y)
            size: (宽度,高度)
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
        self.text = self.font.render(text, 1, (0, 0, 0))
        self.textpos = self.text.get_rect()
        self.textpos.centerx = (self.x + self.x1) // 2
        self.textpos.centery = (self.y + self.y1) // 2

    def show(self, screen):
        """
            在指定的screen上绘制按钮
            screen: pygame.Surface
        """
        pg.draw.rect(screen, self.color, self.rect)
        screen.blit(self.text, self.textpos)

    def check_click(self, pos):
        """
            检查是否被点击
            pos: 点击时的坐标
        """
        if self.x < pos[0] < self.x1 and \
                self.y < pos[1] < self.y1:
            return True
        return False


class GameTable(Table):
    """游戏的棋盘格"""

    def __init__(self, numbers, size, pos, side):
        """
            生成二维表,并具有位置和边长属性
            pos: 所在位置如(0,0)
            side: 每一格的边长
        """
        super(GameTable, self).__init__(numbers, size)
        self.pos_x = pos[0]
        self.pos_y = pos[1]
        self.pos_x1 = pos[0] + self.size[0] * side
        self.pos_y1 = pos[1] + self.size[1] * side
        self.side = side

    def draw(self, screen, colors):
        """
            在指定的screen上绘制棋盘格
            screen: pygame.Surface
        """
        top = self.pos_y
        for i in self:
            left = self.pos_x
            for j in i:
                rect = pg.Rect(left, top, self.side, self.side)
                pg.draw.rect(screen, colors[j], rect)
                left += self.side
            top += self.side

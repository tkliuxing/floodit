#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import pygame as pg
import fill
from ui import Button, GameTable
from event import ClickEventListen


ZOOM = 1
WINDOW_SIZE = (int(580 * ZOOM), int(340 * ZOOM))
ORIGIN_POINT = (int(20 * ZOOM), int(20 * ZOOM))
TABLE_SIZE = (15, 15)
BLOCK_SIZE = int(20 * ZOOM)
BLOCK_COLORS = {1: (255, 0, 0),
                2: (0, 0, 255),
                3: (0, 255, 0),
                4: (255, 255, 0),
                5: (0, 255, 255),
                6: (255, 0, 255)}


class Floodit(object):
    """游戏"""

    def __init__(self, conf_dict={}):
        self.__dict__.update(conf_dict)
        self.screen = pg.display.set_mode(self.WINDOW_SIZE)
        pg.display.set_caption("Flood it!")
        pg.font.init()
        self.font = pg.font.SysFont("AR PL UMing CN", int(20 * ZOOM))
        self.screen.fill([200, 200, 200])
        self.table = GameTable(self.COLORS.keys(),
                               self.TABLE_SIZE,
                               self.TABLE_POSITION,
                               self.BLOCK_SIDE)

        # 色块按钮起始坐标
        cl_x = self.TABLE_POSITION[0] + \
            self.BLOCK_SIDE * (self.TABLE_SIZE[0] + 1)
        cl_y = self.TABLE_POSITION[1] + \
            self.BLOCK_SIDE * (self.TABLE_SIZE[1] - 1)

        # "New game"按钮
        x = self.TABLE_POSITION[0] + self.BLOCK_SIDE * (self.TABLE_SIZE[0] + 1)
        w = self.BLOCK_SIDE * (len(self.COLORS) * 2 - 1)
        y = self.TABLE_POSITION[1]
        h = self.BLOCK_SIDE * 2
        self.rb = Button((x, y), (w, h), text=u"New Game!",
                         fontsize=int(20 * ZOOM))
        self.rb.show(self.screen)
        self.events = ClickEventListen()
        self.events.register(self.rb, self.reset)

        # 初始化色块按钮
        left = cl_x
        self.color_buttons = []
        for k, v in self.COLORS.iteritems():
            button = Button((left, cl_y), (self.BLOCK_SIDE,
                                           self.BLOCK_SIDE), color=v, fontsize=int(20 * ZOOM))
            button.show(self.screen)
            self.color_buttons.append(button)
            self.events.register(button, self.colors_click, number=k)
            left += self.BLOCK_SIDE * 2
        self.table.draw(self.screen, BLOCK_COLORS)
        self.wined = False

    def show(self):
        pg.display.flip()

    def colors_click(self, number=None):
        assert number, "CLICK ERROR!"
        if self.wined:
            return
        if number in self.COLORS.keys():
            fill.fill(self.table, number, x=0, y=0)
            self.table.draw(self.screen, BLOCK_COLORS)
            self.wined = self.win()
        self.show()

    def win(self):
        if fill.filldone(self.table):
            font = pg.font.SysFont("AR PL UMing CN", int(32 * ZOOM))
            win_text = font.render("win", 1, (0, 0, 0))
            self.winrect = win_text.get_rect()
            self.winrect.centerx = (self.rb.x + self.rb.x1) // 2
            self.winrect.centery = self.rb.y1 * 2
            pg.draw.rect(self.screen, [200, 200, 200], self.winrect)
            self.screen.blit(win_text, self.winrect)
            return True
        return False

    def reset(self):
        self.wined = False
        del self.table
        self.table = GameTable(self.COLORS.keys(),
                               self.TABLE_SIZE,
                               self.TABLE_POSITION,
                               self.BLOCK_SIDE)
        self.table.draw(self.screen, BLOCK_COLORS)
        pg.draw.rect(self.screen, [200, 200, 200], self.winrect)
        self.show()

    def mainloop(self):
        while 1:
            events = pg.event.get()
            for event in events:
                if event.type == pg.QUIT:
                    sys.exit(0)
                self.events.listen(event)


if __name__ == '__main__':
    conf_dict = {"COLORS": BLOCK_COLORS,
                 "WINDOW_SIZE": WINDOW_SIZE,
                 "TABLE_SIZE": TABLE_SIZE,
                 "TABLE_POSITION": ORIGIN_POINT,
                 "BLOCK_SIDE": BLOCK_SIZE}
    fi = Floodit(conf_dict=conf_dict)
    fi.show()
    fi.mainloop()

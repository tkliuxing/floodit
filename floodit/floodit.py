# -*- coding:utf-8 -*-
import sys, os
import pygame as pg
import random
import fill

WINDOW_SIZE = (580,340)
ORIGIN_POINT = (20,20)
TABLE_SIZE = (15,15)
BLOCK_SIZE = 20
BLOCK_COLORS = {1:(255,0,0),
                2:(0,0,255),
                3:(0,255,0),
                4:(255,255,0),
                5:(0,255,255),
                6:(255,0,255)}

class Table(object):
    def __init__(self,numbers,size):
        self.numbers = numbers
        self.size = size
        self.init()
    def init(self):
        self.ary = []
        for i in xrange(self.size[1]):
            at = []
            for j in xrange(self.size[0]):
                at.append(random.choice(self.numbers))
            self.ary.append(at)
    def __iter__(self):
        return iter(self.ary)
    def __getitem__(self, item):
        return self.ary[item]
    def __len__(self):
        return len(self.ary)

class GameTable(Table):
    def __init__(self,numbers,size,pos,side):
        super(GameTable,self).__init__(numbers,size)
        self.pos_x = pos[0]
        self.pos_y = pos[1]
        self.side = side
    def draw(self,screen):
        top = self.pos_y
        for i in self:
            left = self.pos_x
            for j in i:
                rect = pg.Rect(left,top,self.side,self.side)
                pg.draw.rect(screen,BLOCK_COLORS[j],rect)
                left += self.side
            top += self.side

class Button(object):
    def __init__(self,x,y,w,h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.x1 = x+w
        self.y1 = y+h
        self.rect = pg.Rect(self.x, self.y, self.w, self.h)
    def set_text(self,font,string):
        self.text = font.render(string, 1, (0, 0, 0))
        self.textpos = self.text.get_rect()
        self.textpos.centerx = (self.x+self.x1)//2
        self.textpos.centery = (self.y+self.y1)//2
    def show(self,screen):
        pg.draw.rect(screen,(255,255,255),self.rect)
        screen.blit(self.text,self.textpos)


class Floodit(object):
    def __init__(self,conf_dict={}):
        self.__dict__.update(conf_dict)
        self.screen = pg.display.set_mode(self.WINDOW_SIZE)
        pg.display.set_caption("Flood it!")
        pg.font.init()
        self.font = pg.font.SysFont("AR PL UMing CN", 20)
        self.screen.fill([200,200,200])
        self.table = GameTable(self.COLORS.keys(),
                               self.TABLE_SIZE,
                               self.TABLE_POSITION,
                               self.BLOCK_SIDE)
        x = self.TABLE_POSITION[0]+self.BLOCK_SIDE*(self.TABLE_SIZE[0]+1)
        w = self.BLOCK_SIDE*(len(self.COLORS)*2-1)
        y = self.TABLE_POSITION[1]+self.BLOCK_SIDE*(self.TABLE_SIZE[1]-1)
        h = self.BLOCK_SIDE
        self.cl = Button(x,y,w,h)

        x = self.TABLE_POSITION[0]+self.BLOCK_SIDE*(self.TABLE_SIZE[0]+1)
        w = self.BLOCK_SIDE*(len(self.COLORS)*2-1)
        y = self.TABLE_POSITION[1]
        h = self.BLOCK_SIDE*2
        self.rb = Button(x,y,w,h)
        self.rb.set_text(self.font,u"New Game!")
        self.rb.show(self.screen)


        left = self.cl.x
        for v in self.COLORS.values():
            rect = pg.Rect(left,self.cl.y,self.BLOCK_SIDE,self.BLOCK_SIDE)
            pg.draw.rect(self.screen,v,rect)
            left += self.BLOCK_SIDE*2
        self.table.draw(self.screen)

    def show(self):
        pg.display.flip()

    def click(self,pos):
        if self.cl.x < pos[0] < self.cl.x1 and \
            self.cl.y < pos[1] < self.cl.y1:
            math_number = (((pos[0]-self.cl.x)//self.BLOCK_SIDE)+2)//2
            if math_number in self.COLORS.keys():
                fill.fill(self.table,math_number)
                self.table.draw(self.screen)
                self.win()
            self.show()
        elif self.rb.x < pos[0] < self.rb.x1 and \
            self.rb.y < pos[1] < self.rb.y1:
            self.reset()

    def win(self):
        if fill.filldone(self.table):
            font = pg.font.SysFont("AR PL UMing CN", 32)
            self.win_text = font.render("win", 1, (0, 0, 0))
            textpos = win_text.get_rect()
            textpos.centerx = (self.rb.x+self.rb.x1)//2
            textpos.centery = self.rb.y1*2
            self.screen.blit(win_text,textpos)
            return True
        return False
    def reset(self):
        del self.table
        self.table = GameTable(self.COLORS.keys(),
                               self.TABLE_SIZE,
                               self.TABLE_POSITION,
                               self.BLOCK_SIDE)
        self.table.draw(self.screen)
        self.show()
    def mainloop(self):
        while 1:
            events = pg.event.get()
            for event in events:
                if event.type == pg.QUIT: sys.exit(0)
                if event.type == pg.MOUSEBUTTONDOWN:
                    self.click(event.pos)

if __name__== '__main__':
    conf_dict={"COLORS":BLOCK_COLORS,
               "WINDOW_SIZE":WINDOW_SIZE,
               "TABLE_SIZE":TABLE_SIZE,
               "TABLE_POSITION":ORIGIN_POINT,
               "BLOCK_SIDE":BLOCK_SIZE}
    fi = Floodit(conf_dict=conf_dict)
    fi.show()
    fi.mainloop()
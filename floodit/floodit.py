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
    """二维表"""
    def __init__(self,numbers,size):
        """
            生成一个宽为size[0]高为size[1],从numbers中随机取样为元素的二维表
            numbers: 内容为数字的list
            size: 具有两个数字元素的list或者tuple
        """
        self.numbers = numbers
        self.size = size
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
    """游戏的棋盘格"""
    def __init__(self,numbers,size,pos,side):
        """
            生成二维表,并具有位置和边长属性
            pos: 所在位置如(0,0)
            side: 每一格的边长
        """
        super(GameTable,self).__init__(numbers,size)
        self.pos_x = pos[0]
        self.pos_y = pos[1]
        self.pos_x1 = pos[0] + self.size[0]*side
        self.pos_y1 = pos[1] + self.size[1]*side
        self.side = side
    def draw(self,screen):
        """
            在指定的screen上绘制棋盘格
            screen: pygame.Surface
        """
        top = self.pos_y
        for i in self:
            left = self.pos_x
            for j in i:
                rect = pg.Rect(left,top,self.side,self.side)
                pg.draw.rect(screen,BLOCK_COLORS[j],rect)
                left += self.side
            top += self.side

class Button(object):
    """游戏操作按钮"""
    def __init__(self,pos,size,color=(255,255,255),text="",fontname="AR PL UMing CN",fontsize=20):
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
        self.x1 = self.x+self.w
        self.y1 = self.y+self.h
        self.color = color
        self.rect = pg.Rect(pos, size)
        self.font = pg.font.SysFont(fontname, fontsize)
        self.text = self.font.render(text, 1, (0, 0, 0))
        self.textpos = self.text.get_rect()
        self.textpos.centerx = (self.x+self.x1)//2
        self.textpos.centery = (self.y+self.y1)//2
    def show(self,screen):
        """
            在指定的screen上绘制按钮
            screen: pygame.Surface
        """
        pg.draw.rect(screen,self.color,self.rect)
        screen.blit(self.text,self.textpos)
    def check_click(self,pos):
        """
            检查是否被点击
            pos: 点击时的坐标
        """
        if self.x < pos[0] < self.x1 and \
            self.y < pos[1] < self.y1:
            return True
        return False

class ClickEventListen(object):
    """点击事件监听类"""
    def __init__(self):
        """
            初始化事件监听列表
        """
        self.check_list=[]
    def register(self,obj,func,func_args=[],**func_kwargs):
        """
            注册事件
            obj: 事件所在对象
            func: 事件处理函数
            func_args: 事件处理函数位置参数
            func_kwargs: 事件处理函数关键字参数
        """
        assert hasattr(obj,"check_click"),"obj not exist 'check_click' function"
        class EventObject(object):
            pass
        ev = EventObject()
        ev.check = obj.check_click
        ev.obj = obj
        ev.func = func
        ev.func_args = func_args
        ev.func_kwargs = func_kwargs
        self.check_list.append(ev)
    def listen(self,event):
        """
            监测事件并执行事件处理函数
            event: 触发的事件
        """
        if event.type != pg.MOUSEBUTTONDOWN:
            return
        for e in self.check_list:
            if e.check(event.pos):
                return e.func(*e.func_args,**e.func_kwargs)

class Floodit(object):
    """游戏"""
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
        
        #色块按钮起始坐标
        cl_x = self.TABLE_POSITION[0]+self.BLOCK_SIDE*(self.TABLE_SIZE[0]+1)
        cl_y = self.TABLE_POSITION[1]+self.BLOCK_SIDE*(self.TABLE_SIZE[1]-1)
        
        #"New game"按钮
        x = self.TABLE_POSITION[0]+self.BLOCK_SIDE*(self.TABLE_SIZE[0]+1)
        w = self.BLOCK_SIDE*(len(self.COLORS)*2-1)
        y = self.TABLE_POSITION[1]
        h = self.BLOCK_SIDE*2
        self.rb = Button((x,y),(w,h),text=u"New Game!")
        self.rb.show(self.screen)
        self.events = ClickEventListen()
        self.events.register(self.rb,self.reset)
        
        #初始化色块按钮
        left = cl_x
        self.color_buttons = []
        for k,v in self.COLORS.iteritems():
            button = Button((left,cl_y),(self.BLOCK_SIDE,self.BLOCK_SIDE),color=v)
            button.show(self.screen)
            self.color_buttons.append(button)
            self.events.register(button,self.colors_click,number=k)
            left += self.BLOCK_SIDE*2
        self.table.draw(self.screen)
        self.wined = False

    def show(self):
        pg.display.flip()

    def colors_click(self,number=None):
        assert number,"CLICK ERROR!"
        if self.wined:
            return
        if number in self.COLORS.keys():
            fill.fill(self.table,number)
            self.table.draw(self.screen)
            self.wined=self.win()
        self.show()

    def win(self):
        if fill.filldone(self.table):
            font = pg.font.SysFont("AR PL UMing CN", 32)
            win_text = font.render("win", 1, (0, 0, 0))
            self.winrect = win_text.get_rect()
            self.winrect.centerx = (self.rb.x+self.rb.x1)//2
            self.winrect.centery = self.rb.y1*2
            pg.draw.rect(self.screen,[200,200,200],self.winrect)
            self.screen.blit(win_text,self.winrect)
            return True
        return False
    def reset(self):
        self.wined = False
        del self.table
        self.table = GameTable(self.COLORS.keys(),
                               self.TABLE_SIZE,
                               self.TABLE_POSITION,
                               self.BLOCK_SIDE)
        self.table.draw(self.screen)
        pg.draw.rect(self.screen,[200,200,200],self.winrect)
        self.show()
    def mainloop(self):
        while 1:
            events = pg.event.get()
            for event in events:
                if event.type == pg.QUIT: sys.exit(0)
                self.events.listen(event)

if __name__== '__main__':
    conf_dict={"COLORS":BLOCK_COLORS,
               "WINDOW_SIZE":WINDOW_SIZE,
               "TABLE_SIZE":TABLE_SIZE,
               "TABLE_POSITION":ORIGIN_POINT,
               "BLOCK_SIDE":BLOCK_SIZE}
    fi = Floodit(conf_dict=conf_dict)
    fi.show()
    fi.mainloop()

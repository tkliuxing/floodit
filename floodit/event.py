# -*- coding:utf-8 -*-
import pygame as pg


class ClickEventListen(object):
    """点击事件监听类"""

    def __init__(self):
        """
            初始化事件监听列表
        """
        self.check_list = []

    def register(self, obj, func, func_args=[], **func_kwargs):
        """
            注册事件
            obj: 事件所在对象
            func: 事件处理函数
            func_args: 事件处理函数位置参数
            func_kwargs: 事件处理函数关键字参数
        """
        assert hasattr(
            obj, "check_click"), "obj not exist 'check_click' function"

        class EventObject(object):
            pass
        ev = EventObject()
        ev.check = obj.check_click
        ev.obj = obj
        ev.func = func
        ev.func_args = func_args
        ev.func_kwargs = func_kwargs
        self.check_list.append(ev)

    def listen(self, event):
        """
            监测事件并执行事件处理函数
            event: 触发的事件
        """
        if event.type != pg.MOUSEBUTTONDOWN:
            return
        for e in self.check_list:
            if e.check(event.pos):
                return e.func(*e.func_args, **e.func_kwargs)

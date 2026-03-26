from dataclasses import dataclass, field
from typing import Callable

import pygame as pg


@dataclass
class _EventEntry:
    check: Callable
    func: Callable
    func_args: list = field(default_factory=list)
    func_kwargs: dict = field(default_factory=dict)


class ClickEventListen:
    """点击事件监听类"""

    def __init__(self):
        self.check_list: list[_EventEntry] = []

    def register(self, obj, func: Callable, func_args: list = None, **func_kwargs):
        """
        注册点击事件。

        obj: 拥有 check_click 方法的对象
        func: 点击后调用的处理函数
        func_args: 处理函数的位置参数
        func_kwargs: 处理函数的关键字参数
        """
        if not hasattr(obj, "check_click"):
            raise AttributeError(f"{obj!r} 缺少 'check_click' 方法")
        self.check_list.append(
            _EventEntry(
                check=obj.check_click,
                func=func,
                func_args=func_args or [],
                func_kwargs=func_kwargs,
            )
        )

    def listen(self, event: pg.event.Event):
        """监测事件并调用对应的处理函数。"""
        if event.type != pg.MOUSEBUTTONDOWN:
            return
        for entry in self.check_list:
            if entry.check(event.pos):
                entry.func(*entry.func_args, **entry.func_kwargs)
                return

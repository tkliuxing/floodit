from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pygame as pg

LEFT_BUTTON = 1


@dataclass
class _EventEntry:
    obj: Any
    func: Callable
    func_args: list = field(default_factory=list)
    func_kwargs: dict = field(default_factory=dict)


class ClickEventListen:
    """点击事件监听类"""

    def __init__(self, cursor_enabled: bool = True):
        self.check_list: list[_EventEntry] = []
        self.key_map: dict[int, _EventEntry] = {}
        self.cursor_enabled = cursor_enabled
        self._hand_cursor = False

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
                obj=obj,
                func=func,
                func_args=func_args or [],
                func_kwargs=func_kwargs,
            )
        )

    def register_key(self, keys, func: Callable, func_args: list = None, **func_kwargs):
        """
        注册键盘快捷键。

        keys: 单个 pygame 键码，或键码的可迭代对象（多个键触发同一动作）
        func: 按下后调用的处理函数
        """
        if isinstance(keys, int):
            keys = [keys]
        entry = _EventEntry(
            obj=None,
            func=func,
            func_args=func_args or [],
            func_kwargs=func_kwargs,
        )
        for key in keys:
            self.key_map[key] = entry

    def _set_state(self, name: str, entry: _EventEntry, value: bool):
        """调用对象上可选的状态设置方法（set_hover / set_pressed）。"""
        setter = getattr(entry.obj, name, None)
        if setter is not None:
            setter(value)

    def _apply_cursor(self):
        """悬停在可点击对象上时切换成手型光标。"""
        if not self.cursor_enabled:
            return
        wanted = any(getattr(e.obj, "hovered", False) for e in self.check_list)
        if wanted == self._hand_cursor:
            return
        self._hand_cursor = wanted
        cursor = pg.SYSTEM_CURSOR_HAND if wanted else pg.SYSTEM_CURSOR_ARROW
        try:
            pg.mouse.set_cursor(cursor)
        except pg.error:
            # 部分无头/精简环境不支持系统光标，忽略即可
            self.cursor_enabled = False

    def listen(self, event: pg.event.Event):
        """监测事件并更新交互状态、调用对应的处理函数。"""
        if event.type == pg.KEYDOWN:
            entry = self.key_map.get(event.key)
            if entry is not None:
                entry.func(*entry.func_args, **entry.func_kwargs)
            return

        if event.type == pg.MOUSEMOTION:
            for entry in self.check_list:
                self._set_state("set_hover", entry, entry.obj.check_click(event.pos))
            self._apply_cursor()
            return

        if event.type == pg.MOUSEBUTTONDOWN and event.button == LEFT_BUTTON:
            for entry in self.check_list:
                self._set_state("set_pressed", entry, entry.obj.check_click(event.pos))
            return

        if event.type == pg.MOUSEBUTTONUP and event.button == LEFT_BUTTON:
            # 先清空所有按下状态再触发回调，避免回调重建界面后状态残留
            fired = None
            for entry in self.check_list:
                was_pressed = getattr(entry.obj, "pressed", False)
                self._set_state("set_pressed", entry, False)
                if fired is None and was_pressed and entry.obj.check_click(event.pos):
                    fired = entry
            if fired is not None:
                fired.func(*fired.func_args, **fired.func_kwargs)

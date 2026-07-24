"""事件分发测试：鼠标三态、键盘快捷键、手型光标。"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame as pg  # noqa: E402
import pytest  # noqa: E402

from floodit.event import ClickEventListen  # noqa: E402


class FakeButton:
    """最小可点击对象，行为与 ui.Button 的状态接口一致。"""

    def __init__(self, rect):
        self.rect = pg.Rect(rect)
        self.hovered = False
        self.pressed = False

    def check_click(self, pos):
        return self.rect.collidepoint(pos)

    def set_hover(self, value):
        self.hovered = value

    def set_pressed(self, value):
        self.pressed = value


@pytest.fixture(autouse=True)
def _init():
    pg.init()
    yield


@pytest.fixture
def listener():
    # 无头环境下关掉光标切换，避免依赖系统光标
    return ClickEventListen(cursor_enabled=False)


def motion(pos):
    return pg.event.Event(pg.MOUSEMOTION, pos=pos)


def down(pos, button=1):
    return pg.event.Event(pg.MOUSEBUTTONDOWN, pos=pos, button=button)


def up(pos, button=1):
    return pg.event.Event(pg.MOUSEBUTTONUP, pos=pos, button=button)


def key(code):
    return pg.event.Event(pg.KEYDOWN, key=code)


class TestRegistration:
    def test_rejects_object_without_check_click(self, listener):
        with pytest.raises(AttributeError):
            listener.register(object(), lambda: None)


class TestMouse:
    def test_click_fires_on_release(self, listener):
        calls = []
        b = FakeButton((0, 0, 10, 10))
        listener.register(b, lambda: calls.append(1))
        listener.listen(down((5, 5)))
        assert not calls, "按下时不应触发，要等抬起"
        listener.listen(up((5, 5)))
        assert calls == [1]

    def test_press_cancelled_by_dragging_off(self, listener):
        calls = []
        b = FakeButton((0, 0, 10, 10))
        listener.register(b, lambda: calls.append(1))
        listener.listen(down((5, 5)))
        listener.listen(up((50, 50)))
        assert calls == []
        assert not b.pressed

    def test_release_without_press_does_nothing(self, listener):
        calls = []
        listener.register(FakeButton((0, 0, 10, 10)), lambda: calls.append(1))
        listener.listen(up((5, 5)))
        assert calls == []

    def test_right_button_is_ignored(self, listener):
        calls = []
        listener.register(FakeButton((0, 0, 10, 10)), lambda: calls.append(1))
        listener.listen(down((5, 5), button=3))
        listener.listen(up((5, 5), button=3))
        assert calls == []

    def test_hover_tracks_the_pointer(self, listener):
        a = FakeButton((0, 0, 10, 10))
        b = FakeButton((20, 0, 10, 10))
        listener.register(a, lambda: None)
        listener.register(b, lambda: None)
        listener.listen(motion((5, 5)))
        assert a.hovered and not b.hovered
        listener.listen(motion((25, 5)))
        assert b.hovered and not a.hovered
        listener.listen(motion((100, 100)))
        assert not a.hovered and not b.hovered

    def test_only_one_handler_fires_when_buttons_overlap(self, listener):
        calls = []
        listener.register(FakeButton((0, 0, 10, 10)), lambda: calls.append("a"))
        listener.register(FakeButton((0, 0, 10, 10)), lambda: calls.append("b"))
        listener.listen(down((5, 5)))
        listener.listen(up((5, 5)))
        assert len(calls) == 1

    def test_kwargs_are_forwarded(self, listener):
        got = []
        listener.register(
            FakeButton((0, 0, 10, 10)), lambda number: got.append(number), number=4
        )
        listener.listen(down((5, 5)))
        listener.listen(up((5, 5)))
        assert got == [4]


class TestKeyboard:
    def test_key_triggers_handler(self, listener):
        calls = []
        listener.register_key(pg.K_r, lambda: calls.append("r"))
        listener.listen(key(pg.K_r))
        assert calls == ["r"]

    def test_multiple_keys_share_one_handler(self, listener):
        calls = []
        listener.register_key([pg.K_r, pg.K_F2], lambda: calls.append(1))
        listener.listen(key(pg.K_r))
        listener.listen(key(pg.K_F2))
        assert calls == [1, 1]

    def test_unbound_key_is_ignored(self, listener):
        calls = []
        listener.register_key(pg.K_r, lambda: calls.append(1))
        listener.listen(key(pg.K_z))
        assert calls == []

    def test_kwargs_are_forwarded(self, listener):
        got = []
        listener.register_key(pg.K_1, lambda number: got.append(number), number=3)
        listener.listen(key(pg.K_1))
        assert got == [3]

    def test_keyboard_does_not_disturb_hover_state(self, listener):
        b = FakeButton((0, 0, 10, 10))
        listener.register(b, lambda: None)
        listener.register_key(pg.K_r, lambda: None)
        listener.listen(motion((5, 5)))
        listener.listen(key(pg.K_r))
        assert b.hovered


class TestCursor:
    def test_cursor_switches_on_hover(self):
        listener = ClickEventListen(cursor_enabled=True)
        b = FakeButton((0, 0, 10, 10))
        listener.register(b, lambda: None)
        listener.listen(motion((5, 5)))
        # 无头环境可能不支持系统光标，那时会自动禁用而不是崩溃
        if listener.cursor_enabled:
            assert listener._hand_cursor
            listener.listen(motion((99, 99)))
            assert not listener._hand_cursor

    def test_disabled_cursor_never_switches(self):
        listener = ClickEventListen(cursor_enabled=False)
        listener.register(FakeButton((0, 0, 10, 10)), lambda: None)
        listener.listen(motion((5, 5)))
        assert not listener._hand_cursor

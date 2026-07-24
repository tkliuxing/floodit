import pygame as pg

from .datastruct import Table


def _mix(color: tuple, target: tuple, ratio: float) -> tuple:
    """按 ratio 把 color 向 target 混合，用于生成悬停/按下/描边色。"""
    return tuple(int(c + (t - c) * ratio) for c, t in zip(color, target, strict=True))


def lighten(color: tuple, ratio: float = 0.18) -> tuple:
    """提亮颜色。"""
    return _mix(color, (255, 255, 255), ratio)


def darken(color: tuple, ratio: float = 0.18) -> tuple:
    """压暗颜色。"""
    return _mix(color, (0, 0, 0), ratio)


def _luma(color: tuple) -> float:
    """感知亮度，用于决定悬停时该提亮还是压暗。"""
    r, g, b = color[:3]
    return 0.299 * r + 0.587 * g + 0.114 * b


LIGHT_THRESHOLD = 200


class Button:
    """游戏操作按钮"""

    def __init__(
        self,
        pos: tuple,
        size: tuple,
        color: tuple = (250, 250, 252),
        text: str = "",
        fontname: str = "AR PL UMing CN",
        fontsize: int = 20,
        radius: int = 6,
        text_color: tuple = (45, 48, 54),
    ):
        """
        生成按钮。

        pos: (坐标x, 坐标y)
        size: (宽度, 高度)
        color: 按钮背景色
        text: 按钮文字
        fontname: 按钮字体名称
        fontsize: 按钮字体大小
        radius: 圆角半径（像素）
        text_color: 按钮文字颜色
        """
        self.x = pos[0]
        self.y = pos[1]
        self.w = size[0]
        self.h = size[1]
        self.x1 = self.x + self.w
        self.y1 = self.y + self.h
        self.color = color
        self.radius = radius
        self.rect = pg.Rect(pos, size)

        # 三种交互状态的填充色与描边色，由基色推导，保证配色一致。
        # 浅色按钮提亮几乎看不出来，所以按亮度决定悬停方向。
        is_light = _luma(color) > LIGHT_THRESHOLD
        self.hover_color = darken(color, 0.07) if is_light else lighten(color, 0.22)
        self.press_color = darken(color, 0.18)
        self.border_color = darken(color, 0.30)

        self.hovered = False
        self.pressed = False

        self.font = pg.font.SysFont(fontname, fontsize)
        self.text = self.font.render(text, True, text_color)
        self.textpos = self.text.get_rect()
        self.textpos.centerx = (self.x + self.x1) // 2
        self.textpos.centery = (self.y + self.y1) // 2

    def _fill_color(self) -> tuple:
        """根据当前交互状态返回填充色。"""
        if self.pressed and self.hovered:
            return self.press_color
        if self.hovered:
            return self.hover_color
        return self.color

    def show(self, screen: pg.Surface):
        """在指定的 screen 上绘制按钮。"""
        pg.draw.rect(screen, self._fill_color(), self.rect, border_radius=self.radius)
        pg.draw.rect(
            screen, self.border_color, self.rect, width=1, border_radius=self.radius
        )
        # 按下时文字下沉 1px，模拟被按进去的手感
        offset = 1 if (self.pressed and self.hovered) else 0
        screen.blit(self.text, self.textpos.move(0, offset))

    def check_click(self, pos: tuple) -> bool:
        """检查坐标 pos 是否落在按钮范围内。"""
        return self.rect.collidepoint(pos)

    def set_hover(self, hovered: bool) -> bool:
        """设置悬停状态，返回状态是否发生变化。"""
        changed = self.hovered != hovered
        self.hovered = hovered
        return changed

    def set_pressed(self, pressed: bool) -> bool:
        """设置按下状态，返回状态是否发生变化。"""
        changed = self.pressed != pressed
        self.pressed = pressed
        return changed


class GameTable(Table):
    """游戏棋盘格"""

    def __init__(
        self,
        numbers: list,
        size: tuple,
        pos: tuple,
        side: int,
        gap: int = 0,
        radius: int = 0,
    ):
        """
        生成二维表，并附带位置和格子边长属性。

        pos: 起始位置，如 (0, 0)
        side: 每格的边长（像素）
        gap: 格子之间的缝隙宽度（像素），缝隙处露出背景色。
             默认 0：flood it 需要一眼看出连通区域的形状，留缝会把
             同色区域切成散点，反而看不清边界。
        radius: 格子圆角半径（像素），默认 0，理由同上。
        """
        super().__init__(numbers, size)
        self.pos_x = pos[0]
        self.pos_y = pos[1]
        self.pos_x1 = pos[0] + self.size[0] * side
        self.pos_y1 = pos[1] + self.size[1] * side
        self.side = side
        self.gap = gap
        self.radius = radius

    def draw(self, screen: pg.Surface, colors: dict):
        """在指定的 screen 上绘制棋盘格。"""
        inner = self.side - self.gap
        top = self.pos_y
        for row in self:
            left = self.pos_x
            for cell in row:
                rect = pg.Rect(left, top, inner, inner)
                pg.draw.rect(screen, colors[cell], rect, border_radius=self.radius)
                left += self.side
            top += self.side

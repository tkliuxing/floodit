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

# 未显式传入字体时的兜底字号
DEFAULT_FONT_SIZE = 20

# 立体按钮的投影：向下偏移量与不透明度
SHADOW_OFFSET = 2
SHADOW_ALPHA = 60

# 数字压在色块上时，按底色亮度取深/浅字，保证可读。
# 阈值取 150 而非 LIGHT_THRESHOLD(200)：青、绿这类中等亮度色配深字更清楚。
TEXT_LUMA_THRESHOLD = 150
TEXT_ON_LIGHT = (30, 34, 40)
TEXT_ON_DARK = (255, 255, 255)


def text_on(color: tuple) -> tuple:
    """返回在 color 上清晰可读的文字颜色。"""
    return TEXT_ON_LIGHT if _luma(color) > TEXT_LUMA_THRESHOLD else TEXT_ON_DARK


# 步数压力条的三段取色：越接近步数上限越红。与胜/负提示同色系，
# 让"绿=从容、红=告急"的语义在整个界面里保持一致。
PRESSURE_CALM = (56, 142, 60)  # 绿，与 WIN_COLOR 同
PRESSURE_WARN = (223, 163, 53)  # 琥珀
PRESSURE_DANGER = (198, 70, 70)  # 红，与 LOSE_COLOR 同
# 压力条底槽：未填充部分的浅色轨道
PRESSURE_TRACK = (214, 218, 224)


def pressure_color(ratio: float) -> tuple:
    """按 0..1 的压力比例取色：0 从容(绿) → 0.5 警戒(琥珀) → 1 告急(红)。

    ratio 通常是"已用步数 / 步数上限"。超出 [0,1] 会被夹住，
    使调用方不必自己防越界。
    """
    ratio = min(1.0, max(0.0, ratio))
    if ratio <= 0.5:
        return _mix(PRESSURE_CALM, PRESSURE_WARN, ratio / 0.5)
    return _mix(PRESSURE_WARN, PRESSURE_DANGER, (ratio - 0.5) / 0.5)


class Button:
    """游戏操作按钮"""

    def __init__(
        self,
        pos: tuple,
        size: tuple,
        color: tuple = (250, 250, 252),
        text: str = "",
        font: pg.font.Font = None,
        radius: int = 6,
        text_color: tuple = (45, 48, 54),
        raised: bool = False,
    ):
        """
        生成按钮。

        pos: (坐标x, 坐标y)
        size: (宽度, 高度)
        color: 按钮背景色
        text: 按钮文字
        font: 已解析好的字体对象；为 None 时用 pygame 内置字体
        radius: 圆角半径（像素）
        text_color: 按钮文字颜色
        raised: 立体样式——投影 + 顶部高光 + 按下贴地。用于色块选色按钮，
                让它一眼看上去就是可按的按钮。
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

        # 立体样式的附加图层：预先算好投影和高光/内描边色，show() 时直接用
        self.raised = raised
        if raised:
            self.highlight_color = lighten(color, 0.25)
            self.inner_border = darken(color, 0.28)
            self._shadow = pg.Surface((self.w, self.h), pg.SRCALPHA)
            pg.draw.rect(
                self._shadow,
                (0, 0, 0, SHADOW_ALPHA),
                self._shadow.get_rect(),
                border_radius=radius,
            )

        self.font = font or pg.font.Font(None, DEFAULT_FONT_SIZE)
        self.text_color = text_color
        self.set_text(text)

    def set_text(self, text: str):
        """替换按钮文字并重新居中，用于切换语言。"""
        self.label = text
        self.text = self.font.render(text, True, self.text_color)
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
        """在指定的 screen 上绘制按钮。

        立体样式的按钮带半透明投影，调用方须在重绘前用背景色抹掉该区域，
        否则逐帧叠画会让投影越积越深（见 Floodit._draw_buttons）。
        """
        pressed = self.pressed and self.hovered
        if self.raised:
            self._show_raised(screen, pressed)
        else:
            self._show_flat(screen, pressed)

    def _show_flat(self, screen: pg.Surface, pressed: bool):
        pg.draw.rect(screen, self._fill_color(), self.rect, border_radius=self.radius)
        pg.draw.rect(
            screen, self.border_color, self.rect, width=1, border_radius=self.radius
        )
        # 按下时文字下沉 1px，模拟被按进去的手感
        screen.blit(self.text, self.textpos.move(0, 1 if pressed else 0))

    def _show_raised(self, screen: pg.Surface, pressed: bool):
        if pressed:
            # 按下：整块下沉到投影位置，投影消失，像被按进平面
            rect = self.rect.move(0, SHADOW_OFFSET)
        else:
            screen.blit(self._shadow, (self.x, self.y + SHADOW_OFFSET))
            rect = self.rect
        pg.draw.rect(screen, self._fill_color(), rect, border_radius=self.radius)
        # 外圈高光 + 内圈暗边，制造微微凸起的立体感
        pg.draw.rect(
            screen, self.highlight_color, rect, width=1, border_radius=self.radius
        )
        pg.draw.rect(
            screen,
            self.inner_border,
            rect.inflate(-2, -2),
            width=1,
            border_radius=max(1, self.radius - 1),
        )
        screen.blit(self.text, self.text.get_rect(center=rect.center))

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

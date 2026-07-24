#!/usr/bin/env python
import sys

import pygame as pg

from . import fill, filters, fonts, overlay
from .anim import FloodAnimation, RevealAnimation
from .event import ClickEventListen
from .i18n import Translator
from .particle import ParticleSystem, Ripple, ScreenShake, burst, confetti
from .scores import BestScores
from .ui import (
    PRESSURE_TRACK,
    SHADOW_OFFSET,
    Button,
    GameTable,
    pressure_color,
    text_on,
)

ZOOM = 1
WINDOW_SIZE = (int(580 * ZOOM), int(340 * ZOOM))
# 棋盘固定占据一个方形区域：左上角 ORIGIN_POINT、边长 BOARD_PX。难度只改变
# 网格数，格子边长由 BOARD_PX // 网格数 得到，棋盘在区域内居中——于是窗口
# 尺寸与右侧面板位置都不随难度变化。
ORIGIN_POINT = (int(20 * ZOOM), int(20 * ZOOM))
BOARD_PX = int(300 * ZOOM)
# 面板几何统一以固定的 UI_UNIT 为单位，与棋盘格子边长解耦，否则换难度会连带
# 挪动整个右侧面板。
UI_UNIT = int(20 * ZOOM)
# 六色需要两两都能一眼分开，否则看不出连通区域的边界。
# 色值经 CIE Lab ΔE 校验：最小两两 ΔE=71.6，最小亮度差=17.1
# （纯 RGB 原色为 58.0 / 29.1，等亮度的柔和配色仅 33.9 / 2.7）。
# 亮度刻意铺开，使得即便色相相近，明暗差也能撑出边界。
BLOCK_COLORS = {
    1: (214, 49, 49),  # 红   luma  98
    2: (40, 85, 149),  # 蓝   luma  79
    3: (74, 235, 74),  # 绿   luma 169
    4: (235, 205, 117),  # 沙黄 luma 204
    5: (74, 235, 235),  # 青   luma 187
    6: (235, 74, 235),  # 品红 luma 141
}

BG_COLOR = (238, 240, 243)
TEXT_COLOR = (60, 64, 72)
WIN_COLOR = (56, 142, 60)
LOSE_COLOR = (198, 70, 70)
# 刷新最佳成绩时的提示用金色，与普通胜利区分开
RECORD_COLOR = (201, 154, 32)

# --- 难度 -------------------------------------------------------------------
# 每档只改网格大小与步数上限，颜色固定 6 种：这样右侧面板、1-6 键位、提示
# 文案都不受影响，只有棋盘变密/变疏。网格数取 BOARD_PX(=300) 的因数，棋盘正好
# 铺满区域（10->30px、15->20px、20->15px 每格）。
DIFFICULTIES = [
    {"key": "diff_easy", "grid": 10, "max_steps": 20},
    {"key": "diff_normal", "grid": 15, "max_steps": 30},
    {"key": "diff_hard", "grid": 20, "max_steps": 45},
]
# 默认普通，与旧版一致：15x15 / 30 步
DEFAULT_DIFFICULTY = 1


def board_geometry(preset: dict, board_px: int = None, origin: tuple = None):
    """由难度预设算出棋盘几何。

    返回 (网格尺寸, 格子边长, 棋盘左上角, 步数上限)。棋盘边长固定为 board_px，
    格子边长由网格数整除得到，余下的边距用来把棋盘在区域内居中。抽成纯函数
    便于脱离显示环境测试。
    """
    if board_px is None:
        board_px = BOARD_PX
    if origin is None:
        origin = ORIGIN_POINT
    grid = preset["grid"]
    side = board_px // grid
    offset = (board_px - grid * side) // 2
    position = (origin[0] + offset, origin[1] + offset)
    return (grid, grid), side, position, preset["max_steps"]

# 单帧最大步进时间，防止窗口卡顿/拖动后一帧把整段动画跳完
MAX_FRAME_TIME = 0.1

# 波前每帧最多有几格迸碎屑，以及每格迸几颗
DEBRIS_PER_FRAME = 6
DEBRIS_PER_CELL = 4

# --- 版面参数 ---------------------------------------------------------------
# 尺寸统一以格子边长 BLOCK_SIDE 为单位表示，改缩放或格子大小时版面自动跟随。
# 棋盘与右侧面板之间空出几格
PANEL_GUTTER_BLOCKS = 1
# 色块按钮的间距，2 表示"一格按钮 + 一格空隙"
SWATCH_STRIDE_BLOCKS = 2
# New Game 按钮高度占几格
NEW_GAME_HEIGHT_BLOCKS = 2
# 难度切换按钮：紧贴 New Game 下方，高度与到按钮的间距（像素）
DIFF_MARGIN_TOP = int(8 * ZOOM)
DIFF_HEIGHT = int(30 * ZOOM)
# 步数文字区域与 New Game 按钮之间的间距、以及该区域的高度（像素）
STEPS_MARGIN_TOP = int(10 * ZOOM)
STEPS_HEIGHT = int(24 * ZOOM)
# 步数压力条：紧贴步数文字下方，填充比例=已用步数/上限，越满越红。
STEPS_BAR_MARGIN_TOP = int(6 * ZOOM)
STEPS_BAR_HEIGHT = int(8 * ZOOM)
STEPS_BAR_RADIUS = int(4 * ZOOM)
# 胜负提示与步数文字之间的间距，以及提示区域的高度（像素）
STATUS_MARGIN_TOP = int(28 * ZOOM)
STATUS_HEIGHT = int(40 * ZOOM)
# 字号
FONT_SIZE = int(20 * ZOOM)
# 难度按钮文字更长（"Difficulty: Normal"），用比 New Game 略小的字号才不溢出
DIFF_FONT_SIZE = int(16 * ZOOM)
STATUS_FONT_SIZE = int(28 * ZOOM)
# 圆角半径
NEW_GAME_RADIUS = int(8 * ZOOM)
SWATCH_RADIUS = int(7 * ZOOM)
# 色块选色按钮：放大成有体量的立体按钮，数字压在块内。
SWATCH_SIZE = int(30 * ZOOM)
# 数字只含 0-9，用拉丁字体而非界面中文字体渲染：后者的 "4" 是开口造型，
# 小字号下会糊成像对勾的形状，拉丁字体是标准闭口 "4"，更清晰。
SWATCH_LABEL_FONT_SIZE = int(18 * ZOOM)
SWATCH_LABEL_SAMPLE = "0123456789"

# --- 新手引导 ---------------------------------------------------------------
# 引导文案的字号，以及行间距
HINT_FONT_SIZE = int(14 * ZOOM)
HINT_KEYS_FONT_SIZE = int(12 * ZOOM)
HINT_LINE_GAP = int(3 * ZOOM)
# 提示文字的颜色（比正文更淡，不与棋盘抢注意力）
HINT_COLOR = (110, 116, 128)
# 落子后引导淡出的时长（秒）
HINT_FADE_TIME = 0.45


class Floodit:
    """游戏主类"""

    def __init__(
        self,
        colors: dict = None,
        difficulty: int = DEFAULT_DIFFICULTY,
        lang: str = None,
    ):
        self.COLORS = colors if colors is not None else BLOCK_COLORS
        self.WINDOW_SIZE = WINDOW_SIZE
        # 棋盘几何（网格、格子边长、位置、步数上限）由难度决定
        self.difficulty = difficulty % len(DIFFICULTIES)
        self._apply_board_geometry(DIFFICULTIES[self.difficulty])
        # SCALED：把 WINDOW_SIZE 当作固定的逻辑分辨率，SDL 负责等比缩放填满窗口
        # 并自动把鼠标坐标映射回逻辑空间——于是全部布局与命中检测代码无需改动，
        # 就能支持任意窗口尺寸。RESIZABLE：允许拖拽窗口边缘缩放。两者配合，
        # 画面按比例放大/缩小、超出的边用背景色补齐（letterbox），不会变形。
        self.display = pg.display.set_mode(self.WINDOW_SIZE, pg.SCALED | pg.RESIZABLE)
        # 关掉 SDL 文本输入。视频初始化后它默认开启，会把键盘事件先送进
        # 输入法(IME)合成——中日韩输入法开着时，按 1-6 / R / L 会被输入法
        # 吞掉，游戏收不到干净的 KEYDOWN。本游戏不需要文字录入，直接关掉。
        pg.key.stop_text_input()
        # 游戏画面先画到离屏 surface，再整体贴到窗口上。
        # 这样震动可以整体位移，粒子叠在最上层且不会弄脏底下的画面。
        self.screen = pg.Surface(self.WINDOW_SIZE)
        pg.font.init()

        self.i18n = Translator(lang)
        # 字体按"所有语言的文案合集"来挑，否则运行时切到中文会变成空白
        sample = self.i18n.sample()
        self.font = fonts.resolve(FONT_SIZE, sample)
        self.diff_font = fonts.resolve(DIFF_FONT_SIZE, sample)
        self.status_font = fonts.resolve(STATUS_FONT_SIZE, sample)
        self.hint_font = fonts.resolve(HINT_FONT_SIZE, sample)
        self.hint_keys_font = fonts.resolve(HINT_KEYS_FONT_SIZE, sample)
        self.swatch_font = fonts.resolve(SWATCH_LABEL_FONT_SIZE, SWATCH_LABEL_SAMPLE)
        pg.display.set_caption(self.i18n.t("title"))

        self.screen.fill(BG_COLOR)
        self.table = GameTable(
            self.COLORS.keys(),
            self.TABLE_SIZE,
            self.TABLE_POSITION,
            self.BLOCK_SIDE,
        )

        # 右侧面板：几何以固定的 UI_UNIT 和固定棋盘区域为基准，不随难度移动。
        # 面板左缘与棋盘区域之间空出 PANEL_GUTTER_BLOCKS 个单位。
        panel_x = ORIGIN_POINT[0] + BOARD_PX + UI_UNIT * PANEL_GUTTER_BLOCKS
        # 面板宽度正好容纳一排色块按钮（末尾不留空隙）
        panel_w = UI_UNIT * (len(self.COLORS) * SWATCH_STRIDE_BLOCKS - 1)
        # 立体色块按钮：底边与固定棋盘区域底边对齐
        board_bottom = ORIGIN_POINT[1] + BOARD_PX
        swatch_y = board_bottom - SWATCH_SIZE

        self.rb = Button(
            (panel_x, ORIGIN_POINT[1]),
            (panel_w, UI_UNIT * NEW_GAME_HEIGHT_BLOCKS),
            text=self.i18n.t("new_game"),
            font=self.font,
            radius=NEW_GAME_RADIUS,
        )
        # 难度切换按钮，紧贴 New Game 下方；点击或按 D 键循环 简单/普通/困难
        self.diff_btn = Button(
            (panel_x, self.rb.y1 + DIFF_MARGIN_TOP),
            (panel_w, DIFF_HEIGHT),
            text=self._difficulty_label(),
            font=self.diff_font,
            radius=NEW_GAME_RADIUS,
        )

        # 步数、压力条与胜负提示的位置由按钮底边逐段推出，不再依赖魔数
        self.steps_rect = pg.Rect(
            panel_x, self.diff_btn.y1 + STEPS_MARGIN_TOP, panel_w, STEPS_HEIGHT
        )
        self.steps_bar_rect = pg.Rect(
            panel_x,
            self.steps_rect.bottom + STEPS_BAR_MARGIN_TOP,
            panel_w,
            STEPS_BAR_HEIGHT,
        )
        self.status_rect = pg.Rect(
            panel_x,
            self.steps_bar_rect.bottom + STATUS_MARGIN_TOP,
            panel_w,
            STATUS_HEIGHT,
        )

        self.events = ClickEventListen()
        self.events.register(self.rb, self.reset)
        self.events.register(self.diff_btn, self.cycle_difficulty)

        # 初始化色块按钮：在 panel_w 内等距铺开，数字压在块内
        count = len(self.COLORS)
        free = panel_w - count * SWATCH_SIZE
        stride = SWATCH_SIZE + (free / (count - 1) if count > 1 else 0)
        self.color_buttons = []
        for index, (k, v) in enumerate(self.COLORS.items()):
            x = panel_x + round(index * stride)
            # 只有前 9 个绑定了数字键（见 _register_keys），才标号
            digit = str(index + 1) if index < 9 else ""
            button = Button(
                (x, swatch_y),
                (SWATCH_SIZE, SWATCH_SIZE),
                color=v,
                text=digit,
                font=self.swatch_font,
                text_color=text_on(v),
                radius=SWATCH_RADIUS,
                raised=True,
            )
            self.color_buttons.append(button)
            self.events.register(button, self.colors_click, number=k)
        # 立体按钮的投影是半透明的，重绘前要抹掉整条区域，否则逐帧叠加会变黑
        self.swatch_band = pg.Rect(
            self.color_buttons[0].x,
            swatch_y,
            self.color_buttons[-1].x1 - self.color_buttons[0].x,
            SWATCH_SIZE + SHADOW_OFFSET,
        )

        self._register_keys()

        # 最佳成绩按难度持久化；is_record 记住本局胜利是否刷新了纪录，
        # 供换语言时重绘正确的提示。
        self.scores = BestScores()
        self.is_record = False
        self.won = False
        self.lost = False
        self.steps = 0
        self.animation = None
        self.reveal = None
        self.particles = ParticleSystem()
        self.ripples = []
        self.shake = None
        # 领地、悬停预览与新手引导
        self.owned = set()
        self.preview_key = None
        self.preview_cells = set()
        self.pulse = overlay.Pulse()
        self.hint_alpha = 1.0
        self._hint_cache = None

        self._draw_buttons()
        self._draw_steps()
        self._start_reveal()

    def _register_keys(self):
        """绑定键盘快捷键。"""
        # 数字键 1..9 依次对应调色板上的颜色
        for index, number in enumerate(self.COLORS):
            if index >= 9:
                break
            digit = str(index + 1)
            self.events.register_key(
                [getattr(pg, f"K_{digit}"), getattr(pg, f"K_KP{digit}")],
                self.colors_click,
                number=number,
            )
        self.events.register_key([pg.K_r, pg.K_F2], self.reset)
        self.events.register_key([pg.K_l], self.cycle_language)
        self.events.register_key([pg.K_d], self.cycle_difficulty)
        self.events.register_key([pg.K_F11], self.toggle_fullscreen)
        self.events.register_key([pg.K_ESCAPE, pg.K_q], self.quit)

    def quit(self):
        sys.exit(0)

    def toggle_fullscreen(self):
        """在窗口与全屏之间切换。SCALED 下画面会等比铺满屏幕。"""
        try:
            pg.display.toggle_fullscreen()
        except pg.error:
            # 部分无头/精简环境不支持切换全屏，忽略即可
            pass

    def cycle_language(self):
        """切换界面语言并重绘所有文案。"""
        self.i18n.cycle()
        pg.display.set_caption(self.i18n.t("title"))
        self.rb.set_text(self.i18n.t("new_game"))
        self.diff_btn.set_text(self._difficulty_label())
        self._draw_buttons()
        self._draw_steps()
        self._hint_cache = None
        # 胜负提示正显示时也要跟着换语言
        if self.won:
            if self.is_record:
                self._show_status("record", RECORD_COLOR)
            else:
                self._show_status("win", WIN_COLOR)
        elif self.lost:
            self._show_status("lose", LOSE_COLOR)
        self.show()

    # --- 难度 -----------------------------------------------------------
    def _apply_board_geometry(self, preset: dict):
        """按难度预设算出棋盘几何与步数上限。

        棋盘边长固定为 BOARD_PX，格子边长由网格数整除得到，棋盘在固定区域内
        居中——因此换难度不改变窗口尺寸与右侧面板位置。
        """
        (
            self.TABLE_SIZE,
            self.BLOCK_SIDE,
            self.TABLE_POSITION,
            self.max_steps,
        ) = board_geometry(preset)

    def _difficulty_label(self) -> str:
        """难度按钮文字，如 "难度：普通"。"""
        name = self.i18n.t(DIFFICULTIES[self.difficulty]["key"])
        return self.i18n.t("difficulty", name=name)

    def cycle_difficulty(self):
        """循环切换到下一档难度并按新难度开局。"""
        self.difficulty = (self.difficulty + 1) % len(DIFFICULTIES)
        self._apply_board_geometry(DIFFICULTIES[self.difficulty])
        self.diff_btn.set_text(self._difficulty_label())
        self.reset()

    # --- 领地 / 预览 / 引导 ---------------------------------------------
    def _sync_owned(self):
        """重算当前领地。落子结束、开新局后调用。"""
        self.owned = fill.region_cells(self.table.ary)

    @property
    def accepting_input(self) -> bool:
        """此刻是否接受落子。预览只在能落子时才有意义。"""
        return not (self.won or self.lost or self.animation or self.reveal)

    def sync_preview(self):
        """按当前悬停的色块更新预览，只在悬停目标变化时重算。"""
        target = None
        if self.accepting_input:
            for number, button in zip(self.COLORS, self.color_buttons, strict=True):
                if button.hovered:
                    target = number
                    break
        if target == self.preview_key:
            return
        self.preview_key = target
        if target is None:
            self.preview_cells = set()
        else:
            self.preview_cells = fill.region_after(self.table.ary, target) - self.owned

    @property
    def hint_visible(self) -> bool:
        return self.hint_alpha > 0

    def _invalidate_hint(self):
        """让引导文案重新排版（领地格数会随落子变化）。

        淡出与否由 update_hint 按 steps 判定，误点当前色不算落子，
        引导会继续留着。
        """
        self._hint_cache = None

    def _hint_lines(self) -> list:
        """引导文案：目标、领地位置、下一步该做什么，外加快捷键小字。"""
        return [
            (self.i18n.t("hint_goal"), TEXT_COLOR, self.hint_font),
            (
                self.i18n.t("hint_origin", cells=len(self.owned)),
                HINT_COLOR,
                self.hint_font,
            ),
            (self.i18n.t("hint_pick"), HINT_COLOR, self.hint_font),
            (self.i18n.t("hint_keys"), HINT_COLOR, self.hint_keys_font),
        ]

    def _hint_surface(self) -> pg.Surface:
        """把引导文案渲染成一张可整体调透明度的图，并缓存。"""
        if self._hint_cache is not None:
            return self._hint_cache
        width = self.status_rect.width
        # 逐行折行后再渲染，任何语言都不会溢出面板
        images = []
        for text, color, font in self._hint_lines():
            for line in fonts.wrap(font, text, width):
                images.append(font.render(line, True, color))
        height = sum(img.get_height() for img in images)
        height += HINT_LINE_GAP * (len(images) - 1)
        surf = pg.Surface((width, height), pg.SRCALPHA)
        y = 0
        for img in images:
            surf.blit(img, img.get_rect(centerx=width // 2, y=y))
            y += img.get_height() + HINT_LINE_GAP
        self._hint_cache = surf
        return surf

    def update_hint(self, dt: float):
        """落子之后把引导淡出。"""
        if self.steps > 0 and self.hint_alpha > 0:
            self.hint_alpha = max(0.0, self.hint_alpha - dt / HINT_FADE_TIME)

    def _draw_overlay(self, offset: tuple):
        """在窗口副本上叠加领地描边、悬停预览与起点标记。

        必须在融合滤镜之后调用，否则描边会被一起糊掉。
        """
        pos = (self.TABLE_POSITION[0] + offset[0], self.TABLE_POSITION[1] + offset[1])
        side = self.BLOCK_SIDE
        if self.reveal or not self.owned:
            return

        if self.preview_cells:
            overlay.highlight_cells(self.display, self.preview_cells, pos, side)
        overlay.region_outline(self.display, self.owned, pos, side)
        if self.preview_cells:
            overlay.region_outline(
                self.display,
                self.owned | self.preview_cells,
                pos,
                side,
                width=overlay.PREVIEW_OUTLINE_WIDTH,
                inner=None,
            )
        # 第一步之前，用脉动圆环把视线引到起点
        if self.hint_visible and self.steps == 0:
            overlay.origin_marker(self.display, pos, side, self.pulse.value)

        if self.hint_visible:
            surf = self._hint_surface()
            surf.set_alpha(round(255 * self.hint_alpha))
            self.display.blit(
                surf,
                surf.get_rect(centerx=self.status_rect.centerx, y=self.status_rect.y),
            )

    def _draw_target_line(self):
        """压力条下方的一行小字。

        悬停色块时显示这一步能吃到多少格（+N），否则显示当前难度的最佳成绩，
        给玩家一个可追赶的目标。两者互斥，共用同一行、每帧重画，不占额外版面。
        """
        if self.preview_cells:
            text = self.i18n.t("preview_gain", cells=len(self.preview_cells))
            color = TEXT_COLOR
        else:
            best = self.scores.best_for(DIFFICULTIES[self.difficulty]["key"])
            text = (
                self.i18n.t("best_none")
                if best is None
                else self.i18n.t("best", steps=best)
            )
            color = HINT_COLOR
        img = self.hint_font.render(text, True, color)
        self.display.blit(
            img,
            img.get_rect(
                centerx=self.steps_rect.centerx, y=self.steps_bar_rect.bottom + 2
            ),
        )

    @property
    def board_rect(self) -> pg.Rect:
        """棋盘占据的矩形区域。"""
        return pg.Rect(
            self.TABLE_POSITION[0],
            self.TABLE_POSITION[1],
            self.TABLE_SIZE[0] * self.BLOCK_SIDE,
            self.TABLE_SIZE[1] * self.BLOCK_SIDE,
        )

    def _start_reveal(self):
        """开局把棋盘逐格铺开。"""
        pg.draw.rect(self.screen, BG_COLOR, self.board_rect)
        self.reveal = RevealAnimation(self.table, self.COLORS, BG_COLOR)

    def update_reveal(self, dt: float):
        """推进开局铺开动画。"""
        self.reveal.update(dt)
        self.reveal.draw(self.screen)
        if self.reveal.done:
            self.reveal = None
            self.table.draw(self.screen, self.COLORS)
            self._sync_owned()

    def show(self):
        """把离屏画面贴到窗口，再把特效叠在最上层。"""
        offset = self.shake.offset() if self.shake else (0, 0)
        if offset != (0, 0):
            self.display.fill(BG_COLOR)
        self.display.blit(self.screen, offset)
        # 融合滤镜作用在窗口副本上，不动离屏画面，
        # 所以它对铺开/波纹/震动一视同仁，也不会污染后续帧
        filters.blend_rect(
            self.display, self.board_rect.move(offset), self.TABLE_SIZE, filters.CELL_PX
        )
        self._draw_overlay(offset)
        self._draw_target_line()
        for ripple in self.ripples:
            ripple.draw(self.display)
        self.particles.draw(self.display)
        pg.display.flip()

    def update_effects(self, dt: float):
        """推进粒子、涟漪和震动。特效不参与任何游戏逻辑。"""
        self.particles.update(dt)
        for ripple in self.ripples:
            ripple.update(dt)
        self.ripples = [r for r in self.ripples if r.alive]
        if self.shake:
            self.shake.update(dt)
            if not self.shake.alive:
                self.shake = None

    @property
    def effects_active(self) -> bool:
        return bool(self.particles.active or self.ripples or self.shake)

    def _draw_buttons(self):
        """重绘全部按钮，使悬停/按下状态即时可见。数字键标号已画在块内。"""
        self.rb.show(self.screen)
        self.diff_btn.show(self.screen)
        # 立体色块按钮带半透明投影，逐帧叠画会越积越深，重绘前先抹底
        self.screen.fill(BG_COLOR, self.swatch_band)
        for button in self.color_buttons:
            button.show(self.screen)

    def _draw_steps(self):
        """在 New Game 按钮下方显示当前步数与压力条。"""
        pg.draw.rect(self.screen, BG_COLOR, self.steps_rect)
        color = LOSE_COLOR if self.steps >= self.max_steps else TEXT_COLOR
        message = self.i18n.t("steps", steps=self.steps, max_steps=self.max_steps)
        text = self.font.render(message, True, color)
        self.screen.blit(text, text.get_rect(center=self.steps_rect.center))
        self._draw_pressure_bar()

    def _draw_pressure_bar(self):
        """步数压力条：浅色底槽 + 按已用比例填充，越接近上限越红。

        一眼就能看出还剩多少步、有多告急，比纯数字更快传达压力。
        """
        bar = self.steps_bar_rect
        self.screen.fill(BG_COLOR, bar)
        pg.draw.rect(self.screen, PRESSURE_TRACK, bar, border_radius=STEPS_BAR_RADIUS)
        ratio = self.steps / self.max_steps if self.max_steps else 0.0
        filled = round(bar.width * min(1.0, ratio))
        if filled > 0:
            fill_rect = pg.Rect(bar.x, bar.y, filled, bar.height)
            pg.draw.rect(
                self.screen,
                pressure_color(ratio),
                fill_rect,
                border_radius=STEPS_BAR_RADIUS,
            )

    def colors_click(self, number: int = None):
        assert number is not None, "CLICK ERROR!"
        if self.won or self.lost or self.animation or self.reveal:
            return
        if number in self.COLORS:
            button = self.color_buttons[list(self.COLORS).index(number)]
            self.ripples.append(Ripple(button.rect.center, self.COLORS[number]))
            src = self.table.ary[0][0]
            # 序列为空 <=> 点的就是当前领地的颜色，棋盘不会有任何变化。
            # 这种多半是误点，不计步也不判负，只留一个涟漪表示点击已被接收。
            sequence = fill.get_fill_sequence(self.table.ary, number)
            if sequence:
                self.steps += 1
                self._draw_steps()
                # 逻辑状态立刻落盘，屏幕上的旧色由动画逐格覆盖
                for layer in sequence:
                    for x, y, color in layer:
                        self.table.ary[y][x] = color
                self.animation = FloodAnimation(
                    sequence, self.COLORS[src], self.COLORS[number]
                )
                # 棋盘变了，缓存的引导文案和悬停预览都失效
                self._invalidate_hint()
                self.preview_key = None
                self.preview_cells = set()
        self.show()

    def _check_end(self):
        """判定胜负并显示提示，在动画播完后调用。"""
        if fill.filldone(self.table.ary):
            # 通关：登记成绩，刷新纪录则显示金色"新纪录"，否则普通胜利提示
            key = DIFFICULTIES[self.difficulty]["key"]
            self.is_record = self.scores.record(key, self.steps)
            if self.is_record:
                self._show_status("record", RECORD_COLOR)
            else:
                self._show_status("win", WIN_COLOR)
            self.won = True
            self.particles.emit(confetti(self.board_rect, list(self.COLORS.values())))
        elif self.steps >= self.max_steps:
            self._show_status("lose", LOSE_COLOR)
            self.lost = True
            self.shake = ScreenShake()

    def update_animation(self, dt: float):
        """按经过的秒数推进填充动画，播完后收尾。"""
        started = self.animation.update(dt)
        self._emit_debris(started, self.animation.dst_color)
        self.animation.draw(self.screen, self.TABLE_POSITION, self.BLOCK_SIDE)
        if self.animation.done:
            self.animation = None
            # 动画逐格绘制，收尾时整块重绘一次以保证和逻辑状态一致
            self.table.draw(self.screen, self.COLORS)
            self._sync_owned()
            self._check_end()

    def _emit_debris(self, cells: list, color: tuple):
        """在波前刚点亮的格子上撒碎屑。

        整块区域可能有几百格，每格都迸粒子既看不清也拖慢帧率，
        所以按固定间隔抽样。
        """
        if not cells:
            return
        stride = max(1, len(cells) // DEBRIS_PER_FRAME)
        half = self.BLOCK_SIDE // 2
        for x, y in cells[::stride]:
            center = (
                self.TABLE_POSITION[0] + x * self.BLOCK_SIDE + half,
                self.TABLE_POSITION[1] + y * self.BLOCK_SIDE + half,
            )
            self.particles.emit(burst(center, color, count=DEBRIS_PER_CELL))

    def _show_status(self, key: str, color: tuple):
        """在步数下方显示胜负提示。"""
        pg.draw.rect(self.screen, BG_COLOR, self.status_rect)
        text = self.status_font.render(self.i18n.t(key), True, color)
        self.screen.blit(text, text.get_rect(center=self.status_rect.center))

    def _clear_status(self):
        pg.draw.rect(self.screen, BG_COLOR, self.status_rect)

    def reset(self):
        self.won = False
        self.lost = False
        self.is_record = False
        self.steps = 0
        self.animation = None
        self.particles.clear()
        self.ripples.clear()
        self.shake = None
        self.owned = set()
        self.preview_key = None
        self.preview_cells = set()
        self.hint_alpha = 1.0
        self._hint_cache = None
        self.table = GameTable(
            self.COLORS.keys(),
            self.TABLE_SIZE,
            self.TABLE_POSITION,
            self.BLOCK_SIDE,
        )
        self._clear_status()
        self._draw_steps()
        self._start_reveal()
        self.show()

    def mainloop(self):
        clock = pg.time.Clock()
        while True:
            dt = min(clock.tick(60) / 1000.0, MAX_FRAME_TIME)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    sys.exit(0)
                self.events.listen(event)

            if self.reveal:
                self.update_reveal(dt)
            elif self.animation:
                self.update_animation(dt)
            self.update_effects(dt)
            self.pulse.update(dt)
            self.update_hint(dt)
            self.sync_preview()

            self._draw_buttons()
            self.show()

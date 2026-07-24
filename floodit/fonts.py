"""字体解析。

`pg.font.SysFont` 找不到字体时会静默回退到默认字体，而默认字体画不出中文，
于是界面上会出现空白。这里按候选列表挑选**确实存在、且真的能画出目标文字**
的字体，全部落空时才退回默认字体。
"""

import sys

import pygame as pg

# 各平台常见的中日韩字体，按优先级排列
CJK_CANDIDATES = {
    "darwin": [
        "PingFang SC",
        "Hiragino Sans GB",
        "STHeiti",
        "Heiti SC",
        "Songti SC",
        "Arial Unicode MS",
    ],
    "win32": [
        "Microsoft YaHei",
        "Microsoft JhengHei",
        "SimHei",
        "SimSun",
        "NSimSun",
    ],
    "linux": [
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "WenQuanYi Micro Hei",
        "WenQuanYi Zen Hei",
        "Droid Sans Fallback",
        "AR PL UMing CN",
    ],
}

# 拉丁字母优先用的无衬线字体
LATIN_CANDIDATES = {
    "darwin": ["Helvetica Neue", "Helvetica", "Arial", "Verdana"],
    "win32": ["Segoe UI", "Tahoma", "Arial", "Verdana"],
    "linux": ["DejaVu Sans", "Liberation Sans", "FreeSans", "Arial"],
}

# 私用区码位，几乎不会有字体收录，用来识别"豆腐块"字形
NOTDEF = "\ue000"


def _platform_key() -> str:
    if sys.platform.startswith("win"):
        return "win32"
    if sys.platform == "darwin":
        return "darwin"
    return "linux"


def candidates(need_cjk: bool) -> list:
    """返回当前平台的候选字体名，必要时把中文字体排在前面。"""
    key = _platform_key()
    latin = LATIN_CANDIDATES[key]
    if not need_cjk:
        return list(latin)
    # 需要中文时，只有 CJK 字体才靠谱；拉丁字体留作垫底
    return CJK_CANDIDATES[key] + latin


def _pixels(surface: pg.Surface) -> bytes:
    return pg.image.tostring(surface, "RGBA")


def can_render(font: pg.font.Font, text: str) -> bool:
    """判断字体能否真正画出 text 里的每个字符。

    不能用 `Font.metrics`：缺字时它返回的是豆腐块的度量而不是 None。
    这里改为把字符渲染出来，和"空串"以及"必定缺字的私用区码位"比对——
    画不出东西、或画出来和豆腐块一模一样，都算不支持。
    """
    if not text:
        return True
    blank = _pixels(font.render("", True, (0, 0, 0)))
    tofu = font.render(NOTDEF, True, (0, 0, 0))
    for ch in set(text):
        if ch.isspace():
            continue
        shape = font.render(ch, True, (0, 0, 0))
        if _pixels(shape) == blank:
            return False
        if shape.get_size() == tofu.get_size() and _pixels(shape) == _pixels(tofu):
            return False
    return True


def resolve(size: int, sample: str = "", names: list = None) -> pg.font.Font:
    """挑一个能画出 sample 的字体。

    size: 字号
    sample: 需要被正确渲染的示例文字，通常是界面上会出现的所有文案
    names: 自定义候选列表，默认按平台和 sample 是否含中文推断
    """
    if names is None:
        names = candidates(need_cjk=any(ord(c) > 0x2E80 for c in sample))

    for name in names:
        path = pg.font.match_font(name)
        if not path:
            continue
        try:
            font = pg.font.Font(path, size)
        except OSError:
            continue
        if can_render(font, sample):
            return font

    # 全部落空：退回 pygame 内置字体，至少拉丁字母是可读的
    return pg.font.Font(None, size)

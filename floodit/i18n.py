"""界面文案的多语言支持。

语言按以下优先级确定：显式传入 > 环境变量 FLOODIT_LANG > 系统区域设置 >
英文。运行时可以循环切换，方便直接看到效果。
"""

import locale
import os

DEFAULT_LANG = "en"
ENV_VAR = "FLOODIT_LANG"

TRANSLATIONS = {
    "en": {
        "title": "Flood it!",
        "new_game": "New Game!",
        "difficulty": "Difficulty: {name}",
        "diff_easy": "Easy",
        "diff_normal": "Normal",
        "diff_hard": "Hard",
        "steps": "Steps: {steps} / {max_steps}",
        "best": "Best: {steps}",
        "best_none": "Best: --",
        "win": "You Win!",
        "record": "New Record!",
        "lose": "Game Over!",
        "hint_goal": "Fill the board with one colour",
        "hint_origin": "You start top-left: {cells} cells",
        "hint_pick": "Pick a colour to grow it",
        "hint_keys": "1-6 colour  R restart  L lang",
        "preview_gain": "+{cells}",
    },
    "zh": {
        "title": "点格子",
        "new_game": "新游戏",
        "difficulty": "难度：{name}",
        "diff_easy": "简单",
        "diff_normal": "普通",
        "diff_hard": "困难",
        "steps": "步数：{steps} / {max_steps}",
        "best": "最佳：{steps}",
        "best_none": "最佳：--",
        "win": "你赢了！",
        "record": "新纪录！",
        "lose": "游戏结束",
        "hint_goal": "把整盘变成同一种颜色",
        "hint_origin": "领地在左上角，现在 {cells} 格",
        "hint_pick": "点下面的色块扩张领地",
        "hint_keys": "1-6 选色   R 新局   L 语言",
        "preview_gain": "+{cells} 格",
    },
}

# 语言切换的循环顺序
LANG_ORDER = ["en", "zh"]


def normalize(tag: str) -> str:
    """把 zh_CN.UTF-8 / zh-Hans 之类的区域标记归一成受支持的语言码。"""
    if not tag:
        return ""
    code = tag.replace("-", "_").split(".")[0].split("_")[0].lower()
    return code if code in TRANSLATIONS else ""


def detect() -> str:
    """推断应使用的语言。"""
    env = normalize(os.environ.get(ENV_VAR, ""))
    if env:
        return env
    try:
        # getlocale 在未设置区域时可能返回 (None, None)
        system = locale.getlocale()[0] or ""
    except ValueError:
        system = ""
    return normalize(system) or DEFAULT_LANG


class Translator:
    """按 key 取文案，缺失时回退到英文，再缺失就返回 key 本身。"""

    def __init__(self, lang: str = None):
        self.lang = normalize(lang or "") or detect()

    def t(self, key: str, **kwargs) -> str:
        table = TRANSLATIONS.get(self.lang, {})
        template = table.get(key) or TRANSLATIONS[DEFAULT_LANG].get(key) or key
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError):
            # 占位符对不上时宁可显示原模板，也不要崩在渲染路径上
            return template

    def cycle(self) -> str:
        """切到下一种语言并返回新的语言码。"""
        try:
            i = LANG_ORDER.index(self.lang)
        except ValueError:
            i = -1
        self.lang = LANG_ORDER[(i + 1) % len(LANG_ORDER)]
        return self.lang

    def sample(self) -> str:
        """所有语言里会出现的字符集合，用来挑选字体。

        必须覆盖全部语言而不只是当前语言，否则运行时切到中文会变成空白。
        """
        chars = set()
        for table in TRANSLATIONS.values():
            for text in table.values():
                chars.update(text)
        # 占位符本身不参与渲染，数字才是
        chars.update("0123456789")
        return "".join(sorted(chars - set("{}")))

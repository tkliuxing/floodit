"""字体解析测试。需要 pygame.font，但用 dummy 视频驱动即可，无需真实显示。"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame as pg  # noqa: E402
import pytest  # noqa: E402

from floodit import fonts  # noqa: E402
from floodit.i18n import Translator  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _init_font():
    pg.init()
    pg.font.init()
    yield
    pg.quit()


class TestCandidates:
    def test_cjk_requested_puts_cjk_fonts_first(self):
        cjk = fonts.candidates(need_cjk=True)
        latin = fonts.candidates(need_cjk=False)
        assert len(cjk) > len(latin)
        assert cjk[0] not in latin, "需要中文时首选应是中文字体"

    def test_latin_list_is_a_suffix_of_cjk_list(self):
        # 中文字体全部落空时，仍应退到拉丁字体而不是直接放弃
        cjk = fonts.candidates(need_cjk=True)
        latin = fonts.candidates(need_cjk=False)
        assert cjk[-len(latin) :] == latin


class TestCanRender:
    def test_builtin_font_handles_latin(self):
        assert fonts.can_render(pg.font.Font(None, 20), "Steps 0/30")

    def test_builtin_font_lacks_cjk(self):
        # 这正是原来 SysFont 静默回退后中文变空白的根因
        assert not fonts.can_render(pg.font.Font(None, 20), "步数")

    def test_empty_text_is_always_renderable(self):
        assert fonts.can_render(pg.font.Font(None, 20), "")

    def test_whitespace_is_ignored(self):
        assert fonts.can_render(pg.font.Font(None, 20), "   ")


class TestResolve:
    def test_always_returns_a_usable_font(self):
        font = fonts.resolve(20, "Steps")
        assert isinstance(font, pg.font.Font)
        assert font.render("Steps", True, (0, 0, 0)).get_width() > 0

    def test_falls_back_when_no_candidate_matches(self):
        font = fonts.resolve(20, "Steps", names=["No Such Font 12345"])
        assert isinstance(font, pg.font.Font)

    def test_resolved_font_can_render_the_sample(self):
        sample = Translator("en").sample()
        font = fonts.resolve(20, sample)
        # 找得到中文字体就该真的能画中文；找不到时至少不能崩
        assert isinstance(font, pg.font.Font)
        if fonts.can_render(font, "步数"):
            assert font.render("步数", True, (0, 0, 0)).get_width() > 0

    def test_size_is_respected(self):
        small = fonts.resolve(12, "Steps")
        big = fonts.resolve(30, "Steps")
        assert big.get_height() > small.get_height()


class TestWrap:
    @pytest.fixture
    def font(self):
        return pg.font.Font(None, 20)

    def test_short_text_stays_on_one_line(self, font):
        assert fonts.wrap(font, "hi", 500) == ["hi"]

    def test_empty_text_yields_one_empty_line(self, font):
        assert fonts.wrap(font, "", 100) == [""]

    def test_long_text_is_split(self, font):
        lines = fonts.wrap(font, "the quick brown fox jumps over it", 80)
        assert len(lines) > 1

    def test_every_line_fits(self, font):
        text = "Fill the board with one colour and win"
        for line in fonts.wrap(font, text, 90):
            assert font.size(line)[0] <= 90

    def test_no_words_are_lost(self, font):
        text = "the quick brown fox jumps over the lazy dog"
        joined = " ".join(fonts.wrap(font, text, 70)).split()
        assert joined == text.split()

    def test_cjk_without_spaces_is_split_by_character(self, font):
        # 中文整句没有空格，必须逐字断行，否则会溢出被裁掉
        text = "把整盘变成同一种颜色再来一次"
        lines = fonts.wrap(font, text, 40)
        assert len(lines) > 1
        assert "".join(lines) == text

    def test_narrow_width_still_terminates(self, font):
        # 宽度比单个字符还窄时不能死循环
        lines = fonts.wrap(font, "abcdef", 1)
        assert "".join(lines) == "abcdef"

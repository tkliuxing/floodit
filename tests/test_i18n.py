"""多语言文案的纯逻辑测试。"""

import pytest

from floodit.i18n import (
    DEFAULT_LANG,
    ENV_VAR,
    LANG_ORDER,
    TRANSLATIONS,
    Translator,
    detect,
    normalize,
)


class TestNormalize:
    @pytest.mark.parametrize(
        "tag,expected",
        [
            ("zh_CN.UTF-8", "zh"),
            ("zh-Hans", "zh"),
            ("ZH", "zh"),
            ("en_US", "en"),
            ("fr_FR", ""),
            ("", ""),
            (None, ""),
        ],
    )
    def test_normalize(self, tag, expected):
        assert normalize(tag) == expected


class TestDetect:
    def test_env_var_wins(self, monkeypatch):
        monkeypatch.setenv(ENV_VAR, "zh")
        assert detect() == "zh"

    def test_unsupported_env_falls_back(self, monkeypatch):
        monkeypatch.setenv(ENV_VAR, "kl")
        assert detect() in TRANSLATIONS

    def test_detect_always_returns_supported_lang(self, monkeypatch):
        monkeypatch.delenv(ENV_VAR, raising=False)
        assert detect() in TRANSLATIONS


class TestTranslator:
    def test_explicit_lang_overrides_env(self, monkeypatch):
        monkeypatch.setenv(ENV_VAR, "en")
        assert Translator("zh").lang == "zh"

    def test_every_language_defines_every_key(self):
        expected = set(TRANSLATIONS[DEFAULT_LANG])
        for lang, table in TRANSLATIONS.items():
            assert set(table) == expected, f"{lang} 的文案 key 与英文不一致"

    def test_steps_placeholder_is_filled(self):
        for lang in TRANSLATIONS:
            out = Translator(lang).t("steps", steps=3, max_steps=30)
            assert "3" in out and "30" in out
            assert "{" not in out

    def test_unknown_key_returns_key(self):
        assert Translator("en").t("nope") == "nope"

    def test_missing_placeholder_does_not_raise(self):
        # 渲染路径上宁可显示原模板，也不能抛异常
        assert "{" in Translator("en").t("steps")

    def test_cycle_visits_every_language_and_wraps(self):
        tr = Translator(LANG_ORDER[0])
        seen = [tr.lang]
        for _ in range(len(LANG_ORDER)):
            seen.append(tr.cycle())
        assert set(seen) == set(LANG_ORDER)
        assert seen[0] == seen[-1], "循环一圈应回到起点"

    def test_cycle_recovers_from_unlisted_lang(self):
        tr = Translator("en")
        tr.lang = "xx"
        assert tr.cycle() in LANG_ORDER


class TestSample:
    def test_sample_covers_all_languages(self):
        sample = set(Translator("en").sample())
        for table in TRANSLATIONS.values():
            for text in table.values():
                assert set(text) - set("{}") <= sample

    def test_sample_includes_digits(self):
        assert set("0123456789") <= set(Translator("en").sample())

    def test_sample_excludes_placeholder_braces(self):
        assert "{" not in Translator("en").sample()

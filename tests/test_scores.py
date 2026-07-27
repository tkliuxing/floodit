"""最佳成绩存储的测试：记录规则、按难度隔离、持久化与脏数据容错。"""

import json

from floodit.scores import BestScores, default_path


def test_first_record_is_set(tmp_path):
    s = BestScores(tmp_path / "scores.json")
    assert s.best_for("diff_normal") is None
    assert s.record("diff_normal", 12) is True
    assert s.best_for("diff_normal") == 12


def test_worse_or_equal_is_not_recorded(tmp_path):
    s = BestScores(tmp_path / "scores.json")
    s.record("diff_normal", 12)
    assert s.record("diff_normal", 15) is False
    assert s.record("diff_normal", 12) is False
    assert s.best_for("diff_normal") == 12


def test_better_updates(tmp_path):
    s = BestScores(tmp_path / "scores.json")
    s.record("diff_normal", 12)
    assert s.record("diff_normal", 9) is True
    assert s.best_for("diff_normal") == 9


def test_persists_across_instances(tmp_path):
    p = tmp_path / "scores.json"
    BestScores(p).record("diff_hard", 40)
    assert BestScores(p).best_for("diff_hard") == 40


def test_per_difficulty_independent(tmp_path):
    s = BestScores(tmp_path / "scores.json")
    s.record("diff_easy", 8)
    s.record("diff_hard", 30)
    assert s.best_for("diff_easy") == 8
    assert s.best_for("diff_hard") == 30
    assert s.best_for("diff_normal") is None


def test_missing_file_is_empty(tmp_path):
    assert BestScores(tmp_path / "nope.json").best_for("diff_normal") is None


def test_corrupt_file_is_ignored_and_still_writable(tmp_path):
    p = tmp_path / "scores.json"
    p.write_text("{not valid json", encoding="utf-8")
    s = BestScores(p)
    assert s.best_for("diff_normal") is None  # 不崩
    assert s.record("diff_normal", 10) is True  # 之后仍能写


def test_dirty_values_are_dropped(tmp_path):
    p = tmp_path / "scores.json"
    p.write_text(
        json.dumps({"diff_normal": -3, "x": "bad", "diff_easy": True, "diff_hard": 7}),
        encoding="utf-8",
    )
    s = BestScores(p)
    assert s.best_for("diff_normal") is None  # 负数丢弃
    assert s.best_for("diff_easy") is None  # bool 不当作步数
    assert s.best_for("diff_hard") == 7


def test_nonpositive_steps_not_recorded(tmp_path):
    s = BestScores(tmp_path / "scores.json")
    assert s.record("diff_normal", 0) is False
    assert s.best_for("diff_normal") is None


def test_default_path_shape():
    p = default_path()
    assert p.name == "scores.json"
    assert p.parent.name == "floodit"

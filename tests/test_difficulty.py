"""难度几何计算测试：网格、格子边长、居中偏移、步数上限。"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from floodit.floodit import BOARD_PX, DEFAULT_DIFFICULTY, DIFFICULTIES, board_geometry


def test_presets_divide_the_board_evenly():
    # 每档网格都应整除固定棋盘边长，棋盘正好铺满、无居中偏移
    for preset in DIFFICULTIES:
        (cols, rows), side, pos, _ = board_geometry(preset)
        assert BOARD_PX % cols == 0
        assert cols * side == BOARD_PX
        assert pos == (20, 20)


def test_default_matches_legacy_layout():
    # 默认难度必须复刻旧版：15x15、每格 20px、30 步、原点 (20,20)
    size, side, pos, max_steps = board_geometry(DIFFICULTIES[DEFAULT_DIFFICULTY])
    assert size == (15, 15)
    assert side == 20
    assert pos == (20, 20)
    assert max_steps == 30


def test_harder_grids_use_smaller_cells():
    sides = [board_geometry(p)[1] for p in DIFFICULTIES]
    # 网格越密，格子越小
    grids = [p["grid"] for p in DIFFICULTIES]
    order = sorted(range(len(grids)), key=lambda i: grids[i])
    assert [sides[i] for i in order] == sorted(sides, reverse=True)


def test_non_divisor_grid_is_centred():
    # 非因数网格：棋盘略小于区域，剩余边距对半分到左上
    (cols, rows), side, pos, _ = board_geometry(
        {"grid": 7, "max_steps": 10}, board_px=300, origin=(20, 20)
    )
    assert side == 300 // 7  # 42
    span = 7 * side  # 294
    off = (300 - span) // 2  # 3
    assert pos == (20 + off, 20 + off)

"""fill 模块的纯逻辑测试，不依赖 pygame，可在无显示环境运行。"""

import copy
import random

import pytest

from floodit.fill import fill, filldone, get_fill_sequence


def apply_sequence(ary: list, sequence: list) -> list:
    """把 get_fill_sequence 的分层结果依次作用到棋盘上。"""
    result = copy.deepcopy(ary)
    for layer in sequence:
        for x, y, color in layer:
            result[y][x] = color
    return result


def random_board(size: int = 15, colors: int = 6, seed: int = 0) -> list:
    rng = random.Random(seed)
    return [[rng.randint(1, colors) for _ in range(size)] for _ in range(size)]


class TestFilldone:
    def test_uniform_board_is_done(self):
        assert filldone([[1, 1], [1, 1]])

    def test_mixed_board_is_not_done(self):
        assert not filldone([[1, 1], [1, 2]])


class TestFill:
    def test_fills_connected_region_only(self):
        ary = [
            [1, 1, 2],
            [1, 2, 2],
            [2, 2, 1],
        ]
        fill(ary, 3)
        assert ary == [
            [3, 3, 2],
            [3, 2, 2],
            [2, 2, 1],
        ]

    def test_same_color_is_a_noop(self):
        ary = [[1, 2], [2, 1]]
        fill(ary, 1)
        assert ary == [[1, 2], [2, 1]]

    def test_uniform_board_fills_completely(self):
        ary = [[1] * 4 for _ in range(4)]
        fill(ary, 5)
        assert filldone(ary) and ary[0][0] == 5


class TestGetFillSequence:
    def test_same_color_returns_empty_sequence(self):
        assert get_fill_sequence([[1, 2], [2, 1]], 1) == []

    def test_layers_are_ordered_by_distance(self):
        # 一条从左上角出发的直线，每层应恰好推进一格
        ary = [[1, 1, 1, 1]]
        sequence = get_fill_sequence(ary, 2)
        assert [len(layer) for layer in sequence] == [1, 1, 1, 1]
        assert [layer[0][:2] for layer in sequence] == [(0, 0), (1, 0), (2, 0), (3, 0)]

    def test_every_cell_appears_exactly_once(self):
        ary = random_board(seed=7)
        cells = [(x, y) for layer in get_fill_sequence(ary, 4) for x, y, _ in layer]
        assert len(cells) == len(set(cells))

    def test_does_not_mutate_input(self):
        ary = random_board(seed=11)
        before = copy.deepcopy(ary)
        get_fill_sequence(ary, 3)
        assert ary == before

    @pytest.mark.parametrize("seed", range(25))
    def test_matches_recursive_fill(self, seed):
        """BFS 分层序列全部作用完后，结果必须与递归 fill 完全一致。"""
        ary = random_board(seed=seed)
        expected = copy.deepcopy(ary)
        number = (seed % 6) + 1
        fill(expected, number)
        assert apply_sequence(ary, get_fill_sequence(ary, number)) == expected


class TestGameStateMachine:
    """复刻 Floodit.colors_click / update_animation 的判定逻辑，确保对局必然终止。"""

    MAX_STEPS = 30

    def play(self, seed: int, pick) -> tuple:
        ary = random_board(seed=seed)
        steps = 0
        won = lost = False
        while not (won or lost):
            sequence = get_fill_sequence(ary, pick(ary))
            steps += 1
            if sequence:
                ary = apply_sequence(ary, sequence)
                if filldone(ary):
                    won = True
                elif steps >= self.MAX_STEPS:
                    lost = True
            elif filldone(ary):
                won = True
            elif steps >= self.MAX_STEPS:
                lost = True
            assert steps <= self.MAX_STEPS, "对局未在步数上限内终止"
        return "win" if won else "lose", steps

    @pytest.mark.parametrize("seed", range(5))
    def test_greedy_play_terminates(self, seed):
        def greedy(ary):
            return max(
                range(1, 7),
                key=lambda n: sum(len(layer) for layer in get_fill_sequence(ary, n)),
            )

        outcome, steps = self.play(seed, greedy)
        assert outcome in {"win", "lose"}
        assert steps <= self.MAX_STEPS

    def test_clicking_current_color_still_consumes_steps(self):
        """点击当前泛洪色不改变棋盘，但仍需计步，最终必然判负。"""
        outcome, steps = self.play(0, lambda ary: ary[0][0])
        assert outcome == "lose"
        assert steps == self.MAX_STEPS

    def test_winning_board_is_detected(self):
        ary = [[1] * 5 for _ in range(5)]
        ary[0][0] = 2
        sequence = get_fill_sequence(ary, 1)
        assert filldone(apply_sequence(ary, sequence))

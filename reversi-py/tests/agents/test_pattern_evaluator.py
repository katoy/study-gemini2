"""PatternEvaluator（パターン抽出と評価）のテスト。"""
import pytest

from agents.pattern_evaluator import PatternEvaluator


class TestPatternEvaluator:
    """パターン評価器のテスト。"""

    def test_evaluator_initialization(self) -> None:
        """初期化できる。"""
        evaluator = PatternEvaluator(board_size=8)
        assert evaluator.board_size == 8

    def test_edge_pattern_all_empty(self) -> None:
        """全空のエッジパターンのインデックスは 0。"""
        evaluator = PatternEvaluator(board_size=8)
        board = [[0] * 8 for _ in range(8)]
        idx = evaluator.pattern_index(board, evaluator.top_edge_squares, turn=1)
        assert idx == 0

    def test_pattern_index_turn_dependency(self) -> None:
        """turn が異なるとインデックスが異なる。"""
        evaluator = PatternEvaluator(board_size=8)
        board = [[0] * 8 for _ in range(8)]
        board[0][0] = 1  # 白の石

        idx_black = evaluator.pattern_index(board, evaluator.top_edge_squares, turn=-1)
        idx_white = evaluator.pattern_index(board, evaluator.top_edge_squares, turn=1)
        assert idx_black != idx_white

    def test_evaluate_returns_float(self) -> None:
        """evaluate() が float を返す。"""
        evaluator = PatternEvaluator(board_size=8)
        board = [[0] * 8 for _ in range(8)]
        board[3][3] = 1
        board[4][4] = 1
        board[3][4] = -1
        board[4][3] = -1

        value = evaluator.evaluate(board, turn=1)
        assert isinstance(value, float)

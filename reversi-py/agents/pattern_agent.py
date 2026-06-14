"""パターン評価を使用したリバーシ AI エージェント。

TD 学習によって学習済みのパターン重みを使用して評価する。
"""
import time
from typing import TYPE_CHECKING, Optional

from .negamax_agent import _apply, _flips_for_move, _undo, _valid_moves
from .pattern_evaluator import PatternEvaluator
from .base_agent import Agent

if TYPE_CHECKING:
    from game import Game


class PatternAgent(Agent):
    """パターンベースの評価関数を使用した negamax エージェント。

    Args:
        weights_path: 学習済み重み（JSON）のパス。
        time_limit_ms: 思考時間上限（ミリ秒）。
        max_depth: 最大探索深さ。
    """

    def __init__(
        self,
        weights_path: Optional[str] = None,
        time_limit_ms: int = 3000,
        max_depth: int = 60,
    ) -> None:
        self._time_limit_ms = time_limit_ms
        self._max_depth = max_depth
        self._evaluator = PatternEvaluator(board_size=8, weights_path=weights_path)
        self._start_time: float = 0.0
        self._nodes_checked = 0

    def _time_exceeded(self) -> bool:
        """思考時間が超過したか確認。"""
        return (time.monotonic() - self._start_time) * 1000 >= self._time_limit_ms

    def _negamax(
        self,
        board: list[list[int]],
        n: int,
        turn: int,
        depth: int,
        alpha: float,
        beta: float,
        passed: bool,
    ) -> tuple[float, Optional[tuple[int, int]]]:
        """αβ枝刈り negamax（パターン評価版）。

        Returns:
            (評価値, 最善手)のタプル。
        """
        # 深さ 0
        if depth == 0:
            value = -self._evaluator.evaluate(board, turn)
            return (value, None)

        # 合法手取得
        moves = _valid_moves(board, n, turn)

        # パス処理
        if not moves:
            if passed:
                # 両者パス→終局（石差で評価）
                black = sum(1 for row in board for v in row if v == -1)
                white = sum(1 for row in board for v in row if v == 1)
                value = (black - white) * 10000
                return (-value if turn == 1 else value, None)

            value, _ = self._negamax(board, n, -turn, depth, -beta, -alpha, passed=True)
            return (-value, None)

        # αβ探索
        best_value: float = -float('inf')
        best_move: Optional[tuple[int, int]] = None

        for move in moves:
            self._nodes_checked += 1
            if self._nodes_checked % 512 == 0:
                if self._time_exceeded():
                    break

            flips = _flips_for_move(board, n, move[0], move[1], turn)
            _apply(board, move, flips, turn)

            value, _ = self._negamax(board, n, -turn, depth - 1, -beta, -alpha, False)
            value = -value

            _undo(board, move, flips, turn)

            if value > best_value:
                best_value = float(value)
                best_move = move

            alpha = max(alpha, best_value)
            if alpha >= beta:
                break

        return (best_value, best_move)

    def play(self, game: "Game") -> Optional[tuple[int, int]]:
        """与えられたゲーム状態で最善手を返す。"""
        self._start_time = time.monotonic()
        self._nodes_checked = 0

        board = game.board.board
        n = game.board_size
        turn = game.turn

        best_move = None
        for d in range(1, self._max_depth + 1):
            try:
                value, move = self._negamax(board, n, turn, d, -float('inf'), float('inf'), False)
                if move is not None:
                    best_move = move
            except KeyboardInterrupt:
                break

        return best_move

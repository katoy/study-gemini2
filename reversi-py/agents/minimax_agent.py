"""Minimax（アルファベータ枝刈り + 反復深化 + 終盤読み切り）エージェント。"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING, Optional

from .base_agent import Agent
from .negamax_agent import (
    _NODES_PER_TIME_CHECK,
    _SearchTimeout,
    _apply,
    _build_weight_table,
    _disc_diff,
    _evaluate,
    _flips_for_move,
    _terminal_score,
    _undo,
)

if TYPE_CHECKING:
    from game import Game


class MinimaxAgent(Agent):
    """明示的な Max/Min 分岐を持つ αβ枝刈り・反復深化 Minimax エージェント。

    空きマス数が endgame_empties 以下の場合は石差のみで完全読み切りを行う。

    Args:
        time_limit_ms: 思考時間の上限（ミリ秒）。
        max_depth: 探索深さの上限。
        endgame_empties: 終盤読み切りに切り替える空きマス数の閾値。
    """

    def __init__(
        self,
        time_limit_ms: int = 500,
        max_depth: int = 60,
        endgame_empties: int = 12,
    ) -> None:
        self.time_limit_ms = time_limit_ms
        self.max_depth = max_depth
        self.endgame_empties = endgame_empties
        self._deadline: float = 0.0
        self._node_count: int = 0

    def play(self, game: Game) -> Optional[tuple[int, int]]:
        """反復深化 Minimax 探索で最善手を選択する。"""
        valid_moves: list[tuple[int, int]] = game.get_valid_moves()
        if not valid_moves:
            return None
        if len(valid_moves) == 1:
            return valid_moves[0]

        board: list[list[int]] = [row[:] for row in game.get_board()]
        n = len(board)
        turn: int = game.turn
        empties = sum(row.count(0) for row in board)
        endgame = empties <= self.endgame_empties
        depth_cap = min(self.max_depth, empties)

        start = time.monotonic()
        self._deadline = start + self.time_limit_ms / 1000.0
        self._node_count = 0

        best_move: tuple[int, int] = valid_moves[0]
        depth = 1
        while depth <= depth_cap:
            try:
                best_move = self._search_root(
                    board, n, turn, depth, endgame, pv=best_move
                )
            except _SearchTimeout:
                break
            if depth >= empties:
                break
            elapsed = time.monotonic() - start
            remaining = self._deadline - time.monotonic()
            if remaining < elapsed:
                break
            depth += 1
        return best_move

    def _search_root(
        self,
        board: list[list[int]],
        n: int,
        turn: int,
        depth: int,
        endgame: bool,
        pv: Optional[tuple[int, int]] = None,
    ) -> tuple[int, int]:
        """ルート局面（最大化プレイヤー）を深さ depth で探索して最善手を返す。"""
        moves = self._ordered_moves(board, n, turn)
        if pv is not None:
            moves.sort(key=lambda mf: mf[0] != pv)

        alpha = float("-inf")
        beta = float("inf")
        best_score = float("-inf")
        best_move = moves[0][0]

        for move, flips in moves:
            _apply(board, move, flips, turn)
            try:
                score = self._minimax(
                    board,
                    n,
                    -turn,
                    turn,
                    depth - 1,
                    alpha,
                    beta,
                    maximizing=False,
                    endgame=endgame,
                    passed=False,
                )
            finally:
                _undo(board, move, flips, turn)
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)

        return best_move

    def _minimax(
        self,
        board: list[list[int]],
        n: int,
        turn: int,
        root_turn: int,
        depth: int,
        alpha: float,
        beta: float,
        maximizing: bool,
        endgame: bool,
        passed: bool,
    ) -> float:
        """root_turn 視点の αβ 枝刈り付き Minimax 値を返す。"""
        self._node_count += 1
        if (
            self._node_count % _NODES_PER_TIME_CHECK == 0
            and time.monotonic() > self._deadline
        ):
            raise _SearchTimeout()

        if depth <= 0:
            if endgame:
                return float(_disc_diff(board, root_turn))
            return _evaluate(board, n, root_turn)

        moves = self._ordered_moves(board, n, turn)
        if not moves:
            if passed:
                return _terminal_score(board, root_turn)
            return self._minimax(
                board,
                n,
                -turn,
                root_turn,
                depth,
                alpha,
                beta,
                maximizing=not maximizing,
                endgame=endgame,
                passed=True,
            )

        if maximizing:
            best = float("-inf")
            for move, flips in moves:
                _apply(board, move, flips, turn)
                try:
                    score = self._minimax(
                        board,
                        n,
                        -turn,
                        root_turn,
                        depth - 1,
                        alpha,
                        beta,
                        maximizing=False,
                        endgame=endgame,
                        passed=False,
                    )
                finally:
                    _undo(board, move, flips, turn)
                best = max(best, score)
                alpha = max(alpha, score)
                if alpha >= beta:
                    break
            return best

        best = float("inf")
        for move, flips in moves:
            _apply(board, move, flips, turn)
            try:
                score = self._minimax(
                    board,
                    n,
                    -turn,
                    root_turn,
                    depth - 1,
                    alpha,
                    beta,
                    maximizing=True,
                    endgame=endgame,
                    passed=False,
                )
            finally:
                _undo(board, move, flips, turn)
            best = min(best, score)
            beta = min(beta, score)
            if alpha >= beta:
                break
        return best

    def _ordered_moves(
        self, board: list[list[int]], n: int, turn: int
    ) -> list[tuple[tuple[int, int], list[tuple[int, int]]]]:
        """合法手を位置重み降順（同重みは row-major 順）で返す。"""
        weights = _build_weight_table(n)
        moves = [
            ((r, c), flips)
            for r in range(n)
            for c in range(n)
            if board[r][c] == 0
            for flips in (_flips_for_move(board, n, r, c, turn),)
            if flips
        ]
        moves.sort(key=lambda mf: weights[mf[0][0]][mf[0][1]], reverse=True)
        return moves

"""Negamax + トランスポジションテーブル + Killer move + History heuristic。

NegamaxAgent より高速な探索により、同じ時間で 2-3 倍深く読む。
"""
import random
import time
from typing import TYPE_CHECKING, Optional, TypedDict

from .negamax_agent import (
    _apply,
    _build_weight_table,
    _flips_for_move,
    _stable_edge_count,
    _undo,
    _valid_moves,
)
from .base_agent import Agent

if TYPE_CHECKING:
    from game import Game


class TTEntry(TypedDict, total=False):
    """トランスポジションテーブルエントリ。"""
    flag: str  # 'EXACT' | 'LOWERBOUND' | 'UPPERBOUND'
    depth: int
    value: float
    best_move: Optional[tuple[int, int]]


class _SearchTimeout(Exception):
    """探索時間超過例外。"""


class TranspositionNegamaxAgent(Agent):
    """Zobrist ハッシュ + TT + Killer move + History heuristic。

    Args:
        time_limit_ms: 思考時間上限（ミリ秒）。
        max_depth: 最大探索深さ。
        endgame_empties: これ以下の空きマスで終盤読み切りモード。
    """

    def __init__(
        self,
        time_limit_ms: int = 3000,
        max_depth: int = 60,
        endgame_empties: int = 12,
    ) -> None:
        self._time_limit_ms = time_limit_ms
        self._max_depth = max_depth
        self._endgame_empties = endgame_empties

        # Zobrist ハッシュテーブル（遅延初期化）
        self._zobrist: list[list[list[int]]] = []

        # トランスポジションテーブル
        self._tt: dict[int, TTEntry] = {}

        # Killer move ヒューリスティック
        self._killers: list[set[tuple[int, int]]] = [set() for _ in range(max_depth + 2)]

        # History heuristic
        self._history: dict[tuple[int, tuple[int, int]], int] = {}

        # 時間管理
        self._start_time: float = 0
        self._nodes_checked: int = 0

    def _initialize_zobrist(self, n: int) -> None:
        """Zobrist ハッシュテーブルを初期化。

        各 (r, c, color) に乱数 64-bit 値を割り当てる。
        color: 0=-1（黒）、1=0（空）、2=1（白）
        """
        if self._zobrist:
            return

        random.seed(0)
        self._zobrist = [
            [
                [random.getrandbits(64) for _ in range(3)]
                for _ in range(n)
            ]
            for _ in range(n)
        ]

    def _compute_initial_hash(self, board: list[list[int]], n: int) -> int:
        """盤面から初期ハッシュを計算。"""
        if not self._zobrist:
            self._initialize_zobrist(n)

        h = 0
        for r in range(n):
            for c in range(n):
                v = board[r][c]
                color_idx = {-1: 0, 0: 1, 1: 2}[v]
                h ^= self._zobrist[r][c][color_idx]
        return h

    def _update_hash(
        self,
        h: int,
        move: tuple[int, int],
        flips: list[tuple[int, int]],
        turn: int,
    ) -> int:
        """着手によるハッシュ更新（XOR で計算）。

        Args:
            h: 現在のハッシュ値。
            move: 着手位置。
            flips: 反転する石のリスト。
            turn: 着手プレイヤー。

        Returns:
            更新後のハッシュ値。
        """
        r, c = move
        # 着手マス: 空 → turn
        h ^= self._zobrist[r][c][1]  # 空の寄与を削除
        h ^= self._zobrist[r][c][(turn + 1) // 2]  # turn の寄与を追加

        # 反転したマス: -turn → turn
        for fr, fc in flips:
            h ^= self._zobrist[fr][fc][(-turn + 1) // 2]  # -turn の寄与を削除
            h ^= self._zobrist[fr][fc][(turn + 1) // 2]  # turn の寄与を追加

        return h

    def _tt_lookup(self, h: int, depth: int, alpha: float, beta: float) -> Optional[float]:
        """TT からエントリを取得。"""
        entry = self._tt.get(h)
        if entry is None:
            return None

        if entry['depth'] < depth:
            return None

        flag = entry['flag']
        v = entry['value']

        if flag == 'EXACT':
            return v
        if flag == 'LOWERBOUND' and v >= beta:
            return v
        if flag == 'UPPERBOUND' and v <= alpha:
            return v

        return None

    def _tt_store(
        self,
        h: int,
        depth: int,
        value: float,
        flag: str,
        best_move: Optional[tuple[int, int]] = None,
    ) -> None:
        """TT にエントリを書き込み。"""
        entry: TTEntry = {'flag': flag, 'depth': depth, 'value': value}
        if best_move is not None:
            entry['best_move'] = best_move
        self._tt[h] = entry

    def _time_exceeded(self) -> bool:
        """思考時間が超過したか確認。"""
        return (time.monotonic() - self._start_time) * 1000 >= self._time_limit_ms

    def _evaluate(
        self,
        board: list[list[int]],
        n: int,
        turn: int,
        endgame: bool,
    ) -> float:
        """盤面を評価。"""
        stones = sum(1 for row in board for v in row if v != 0)
        fill = stones / (n * n)
        empties = n * n - stones

        if endgame or empties <= self._endgame_empties:
            black = sum(1 for row in board for v in row if v == -1)
            white = sum(1 for row in board for v in row if v == 1)
            return (black - white) * 10000

        table = _build_weight_table(n)

        pos_score = 0
        for r in range(n):
            for c in range(n):
                if board[r][c] == turn:
                    pos_score += table[r][c]
                elif board[r][c] == -turn:
                    pos_score -= table[r][c]

        my_moves = len(_valid_moves(board, n, turn))
        opp_moves = len(_valid_moves(board, n, -turn))
        mobility = my_moves - opp_moves

        corners = 0
        corner_pos = [(0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)]
        for r, c in corner_pos:
            if board[r][c] == turn:
                corners += 1
            elif board[r][c] == -turn:
                corners -= 1

        stable = _stable_edge_count(board, n, turn) - _stable_edge_count(board, n, -turn)

        if fill < 0.33:
            pos_c, mob_c, cor_c, stab_c = 1.0, 8.0, 25.0, 10.0
        elif fill <= 0.70:
            pos_c, mob_c, cor_c, stab_c = 1.0, 6.0, 30.0, 15.0
        else:
            pos_c, mob_c, cor_c, stab_c = 0.3, 2.0, 30.0, 20.0

        return pos_c * pos_score + mob_c * mobility + cor_c * corners + stab_c * stable

    def _negamax(
        self,
        board: list[list[int]],
        n: int,
        turn: int,
        depth: int,
        alpha: float,
        beta: float,
        h: int,
        passed: bool,
    ) -> tuple[float, Optional[tuple[int, int]]]:
        """αβ枝刈り negamax + TT + Killer + History。

        Returns:
            (評価値, 最善手)のタプル。
        """
        # TT ルックアップ
        tt_value = self._tt_lookup(h, depth, alpha, beta)
        if tt_value is not None:
            tt_best = self._tt.get(h, {}).get('best_move')
            return (tt_value, tt_best)

        # 深さ 0
        if depth == 0:
            value = self._evaluate(board, n, turn, endgame=False)
            self._tt_store(h, depth, -value, 'EXACT')
            return (-value, None)

        # 合法手取得
        moves = _valid_moves(board, n, turn)

        # パス処理
        if not moves:
            if passed:
                value = self._evaluate(board, n, turn, endgame=True)
                self._tt_store(h, depth, -value, 'EXACT')
                return (-value, None)

            value, _ = self._negamax(board, n, -turn, depth, -beta, -alpha, h, passed=True)
            self._tt_store(h, depth, -value, 'EXACT')
            return (-value, None)

        # 手のオーダリング
        tt_best = self._tt.get(h, {}).get('best_move')
        ordered_moves = []
        if tt_best and tt_best in moves:
            ordered_moves.append(tt_best)

        remaining = [m for m in moves if m != tt_best]
        remaining.sort(
            key=lambda m: (
                self._history.get((turn, m), 0),
                m in self._killers[depth],
            ),
            reverse=True,
        )
        ordered_moves.extend(remaining)

        # αβ探索
        best_value = -float('inf')
        best_move = None

        for move in ordered_moves:
            # 時間チェック（深い深さのみ）
            self._nodes_checked += 1
            if self._nodes_checked % 512 == 0:
                if self._time_exceeded():
                    raise _SearchTimeout()

            flips = _flips_for_move(board, n, move[0], move[1], turn)
            _apply(board, move, flips, turn)
            h_new = self._update_hash(h, move, flips, turn)

            value, _ = self._negamax(board, n, -turn, depth - 1, -beta, -alpha, h_new, False)
            value = -value

            _undo(board, move, flips, turn)

            if value > best_value:
                best_value = value
                best_move = move

            alpha = max(alpha, best_value)
            if alpha >= beta:
                self._killers[depth].add(move)
                self._history[(turn, move)] = self._history.get((turn, move), 0) + (1 << (depth // 2))
                break

        # TT 書き込み
        if best_value <= alpha:
            flag = 'UPPERBOUND'
        elif best_value >= beta:
            flag = 'LOWERBOUND'
        else:
            flag = 'EXACT'

        self._tt_store(h, depth, best_value, flag, best_move)

        return (best_value, best_move)

    def play(self, game: "Game") -> Optional[tuple[int, int]]:
        """与えられたゲーム状態で最善手を返す。"""
        self._start_time = time.monotonic()
        self._nodes_checked = 0
        self._tt.clear()
        self._killers = [set() for _ in range(self._max_depth + 2)]

        board = game.board.board
        n = game.board_size
        turn = game.turn

        h = self._compute_initial_hash(board, n)

        best_move = None
        for d in range(1, self._max_depth + 1):
            try:
                value, move = self._negamax(board, n, turn, d, -float('inf'), float('inf'), h, False)
                if move is not None:
                    best_move = move
            except _SearchTimeout:
                break

        return best_move

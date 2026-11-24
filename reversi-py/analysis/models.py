"""終局後解析のデータモデル定義。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MoveAnalysis:
    """1 手ごとの解析結果。"""

    move_index: int
    move_number: int
    turn: int
    board_before: list[list[int]]
    played_move: tuple[int, int]
    best_move: tuple[int, int]
    played_score: float
    best_score: float
    score_loss: float
    is_exact: bool
    played_disc_diff: Optional[int]
    best_disc_diff: Optional[int]
    refutation_move: Optional[tuple[int, int]]
    pv: list[tuple[int, int]]
    is_decisive: bool
    reason_codes: list[str]
    summary: str
    explanation: str
    outcome_tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class GameAnalysis:
    """1 局全体の解析結果。"""

    loser: int
    winner: int
    final_black: int
    final_white: int
    total_moves: int
    key_mistakes: list[MoveAnalysis]
    moves_by_index: dict[int, MoveAnalysis]
    headline: str
    missed_win_move_index: Optional[int] = None
    loss_sealed_move_index: Optional[int] = None
    draw_sealed_move_index: Optional[int] = None

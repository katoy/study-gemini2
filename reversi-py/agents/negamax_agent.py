"""Negamax（アルファベータ枝刈り + 反復深化 + 終盤読み切り）エージェント。

純 Python・依存ゼロで現 MCTS より深く読む API プレイヤー。
設計書: docs/superpowers/specs/2026-06-13-negamax-agent-design.md
"""
from functools import lru_cache
from typing import List, Tuple

# マスの役割ごとの重み
_WEIGHT_CORNER = 100   # 角
_WEIGHT_X = -50        # X マス（角の斜め隣）
_WEIGHT_C = -20        # C マス（角の縦横隣）
_WEIGHT_EDGE = 10      # その他の辺
_WEIGHT_INNER = -2     # 辺の 1 つ内側
_WEIGHT_CENTER = 0     # 中央部

# 8 方向の走査ベクトル
_DIRECTIONS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1), (0, 1),
    (1, -1), (1, 0), (1, 1),
)


def _flips_for_move(
    board: List[List[int]], n: int, row: int, col: int, turn: int
) -> List[Tuple[int, int]]:
    """着手 (row, col) で反転する石のリストを返す（空なら不合法手）。

    board.py の Board._get_flipped_in_direction と同じ走査ロジックを
    探索用に関数化したもの。Board クラスは変更しない。

    Args:
        board: 盤面（0=空, 1=白, -1=黒）。
        n: 盤面サイズ。
        row: 着手行。
        col: 着手列。
        turn: プレイヤー（1=白, -1=黒）。

    Returns:
        反転する石の座標リスト（着手が不合法なら空リスト）。
    """
    if board[row][col] != 0:
        return []
    flips: List[Tuple[int, int]] = []
    for dr, dc in _DIRECTIONS:
        line: List[Tuple[int, int]] = []
        r, c = row + dr, col + dc
        while 0 <= r < n and 0 <= c < n:
            v = board[r][c]
            if v == 0:
                break
            if v == turn:
                flips.extend(line)
                break
            line.append((r, c))
            r += dr
            c += dc
    return flips


def _valid_moves(board: List[List[int]], n: int, turn: int) -> List[Tuple[int, int]]:
    """turn 側の合法手を row-major 順で返す。

    Args:
        board: 盤面（0=空, 1=白, -1=黒）。
        n: 盤面サイズ。
        turn: プレイヤー（1=白, -1=黒）。

    Returns:
        合法手のリスト（座標のタプル）。
    """
    return [
        (r, c)
        for r in range(n)
        for c in range(n)
        if board[r][c] == 0 and _flips_for_move(board, n, r, c, turn)
    ]


def _apply(
    board: List[List[int]],
    move: Tuple[int, int],
    flips: List[Tuple[int, int]],
    turn: int,
) -> None:
    """着手を盤面に破壊的に適用する（_undo と対で使う）。

    Args:
        board: 盤面（破壊的に変更される）。
        move: 着手（行, 列）。
        flips: 反転する石の座標リスト。
        turn: プレイヤー（1=白, -1=黒）。
    """
    board[move[0]][move[1]] = turn
    for r, c in flips:
        board[r][c] = turn


def _undo(
    board: List[List[int]],
    move: Tuple[int, int],
    flips: List[Tuple[int, int]],
    turn: int,
) -> None:
    """_apply の逆操作で盤面を元に戻す。

    Args:
        board: 盤面（破壊的に変更される）。
        move: 着手（行, 列）。
        flips: 反転する石の座標リスト。
        turn: プレイヤー（1=白, -1=黒）。
    """
    board[move[0]][move[1]] = 0
    for r, c in flips:
        board[r][c] = -turn


# 終局時の確定スコアの倍率。ヒューリスティック値と桁で確実に区別する
_TERMINAL_SCALE = 10000

# ゲームフェーズ係数: (位置重み, mobility, 角, 確定石, 石差)
_PHASE_COEFFS = (
    (1.0, 8.0, 25.0, 10.0, 0.0),   # 序盤 (fill < 0.33)
    (1.0, 6.0, 30.0, 15.0, 0.0),   # 中盤 (0.33 <= fill <= 0.70)
    (0.3, 2.0, 30.0, 20.0, 5.0),   # 終盤 (fill > 0.70)
)
_EARLY_FILL = 0.33
_MID_FILL = 0.70


@lru_cache(maxsize=None)
def _build_weight_table(n: int) -> Tuple[Tuple[int, ...], ...]:
    """サイズ n の位置重みテーブルをマスの役割から生成する。

    最寄りの辺までの距離 (er, ec) で役割を判定するため、
    どの盤面サイズでも一貫した 4 回回転対称のテーブルになる。

    Args:
        n: 盤面サイズ。

    Returns:
        n x n の重みテーブル（イミュータブルなタプルの入れ子）。
    """
    table = [[_WEIGHT_CENTER] * n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            er = min(r, n - 1 - r)
            ec = min(c, n - 1 - c)
            if er == 0 and ec == 0:
                w = _WEIGHT_CORNER
            elif er == 1 and ec == 1:
                w = _WEIGHT_X
            elif {er, ec} == {0, 1}:
                w = _WEIGHT_C
            elif er == 0 or ec == 0:
                w = _WEIGHT_EDGE
            elif er == 1 or ec == 1:
                w = _WEIGHT_INNER
            else:
                w = _WEIGHT_CENTER
            table[r][c] = w
    return tuple(tuple(row) for row in table)


def _phase_coeffs(board: List[List[int]], n: int) -> Tuple[float, ...]:
    """盤面の埋まり具合からゲームフェーズの係数組を返す。

    Args:
        board: 盤面（0=空, 1=白, -1=黒）。
        n: 盤面サイズ。

    Returns:
        (位置重み係数, mobility 係数, 角係数, 確定石係数, 石差係数) のタプル。
    """
    stones = sum(1 for row in board for v in row if v != 0)
    fill = stones / (n * n)
    if fill < _EARLY_FILL:
        return _PHASE_COEFFS[0]
    if fill <= _MID_FILL:
        return _PHASE_COEFFS[1]
    return _PHASE_COEFFS[2]


def _stable_edge_count(board: List[List[int]], n: int, color: int) -> int:
    """各角から辺に沿って連続する color の石を数える（簡易確定石カウント）。

    Args:
        board: 盤面。
        n: 盤面サイズ。
        color: カウント対象の色（1=白, -1=黒）。

    Returns:
        color の石で確定している数。
    """
    stable: set = set()
    corners = (
        (0, 0, (0, 1), (1, 0)),
        (0, n - 1, (0, -1), (1, 0)),
        (n - 1, 0, (0, 1), (-1, 0)),
        (n - 1, n - 1, (0, -1), (-1, 0)),
    )
    for r0, c0, d1, d2 in corners:
        if board[r0][c0] != color:
            continue
        for dr, dc in (d1, d2):
            r, c = r0, c0
            while 0 <= r < n and 0 <= c < n and board[r][c] == color:
                stable.add((r, c))
                r += dr
                c += dc
    return len(stable)


def _disc_diff(board: List[List[int]], turn: int) -> int:
    """手番側から見た石差。

    Args:
        board: 盤面。
        turn: 手番（1=白, -1=黒）。

    Returns:
        手番側の石数 - 相手側の石数。
    """
    return turn * sum(v for row in board for v in row)


def _terminal_score(board: List[List[int]], turn: int) -> float:
    """終局局面の確定スコア（手番側視点）。

    Args:
        board: 盤面。
        turn: 手番（1=白, -1=黒）。

    Returns:
        手番側視点の終局スコア。
    """
    return float(_disc_diff(board, turn) * _TERMINAL_SCALE)


def _evaluate(board: List[List[int]], n: int, turn: int) -> float:
    """手番側から見たヒューリスティック評価値。

    位置重み、着手可能数、角占有、確定石、石差の 5 要素を
    ゲームフェーズに応じた係数で合成する。

    Args:
        board: 盤面。
        n: 盤面サイズ。
        turn: 手番（1=白, -1=黒）。

    Returns:
        評価値（正=有利, 負=不利）。
    """
    w_pos, w_mob, w_corner, w_stable, w_disc = _phase_coeffs(board, n)
    weights = _build_weight_table(n)
    pos = 0
    disc = 0
    for r in range(n):
        for c in range(n):
            v = board[r][c]
            if v != 0:
                pos += v * weights[r][c]
                disc += v
    mobility = len(_valid_moves(board, n, turn)) - len(_valid_moves(board, n, -turn))
    corners = sum(board[r][c] for r in (0, n - 1) for c in (0, n - 1))
    stable = _stable_edge_count(board, n, turn) - _stable_edge_count(board, n, -turn)
    return (
        w_pos * pos * turn
        + w_mob * mobility
        + w_corner * corners * turn
        + w_stable * stable
        + w_disc * disc * turn
    )

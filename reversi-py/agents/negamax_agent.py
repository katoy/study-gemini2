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

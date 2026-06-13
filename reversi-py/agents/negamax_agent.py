"""Negamax（アルファベータ枝刈り + 反復深化 + 終盤読み切り）エージェント。

純 Python・依存ゼロで現 MCTS より深く読む API プレイヤー。
設計書: docs/superpowers/specs/2026-06-13-negamax-agent-design.md
"""
from functools import lru_cache
from typing import Tuple

# マスの役割ごとの重み
_WEIGHT_CORNER = 100   # 角
_WEIGHT_X = -50        # X マス（角の斜め隣）
_WEIGHT_C = -20        # C マス（角の縦横隣）
_WEIGHT_EDGE = 10      # その他の辺
_WEIGHT_INNER = -2     # 辺の 1 つ内側
_WEIGHT_CENTER = 0     # 中央部


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

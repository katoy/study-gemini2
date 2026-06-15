"""盤面テンソル変換ユーティリティ（board_to_tensor の統一実装）"""
from __future__ import annotations

import torch


def board_to_tensor(board: list[list[int]], turn: int) -> torch.Tensor:
    """盤面を現在プレイヤー視点のテンソルに変換。

    Args:
        board: 盤面（0=空, -1=黒, 1=白）。
        turn: 手番プレイヤー（-1=黒, 1=白）。

    Returns:
        (1, 1, n, n) のテンソル。値は 1（自分）, -1（相手）, 0（空）。
    """
    n = len(board)
    board_array = []
    for row in board:
        board_row = []
        for cell in row:
            if cell == 0:
                board_row.append(0)
            elif cell == turn:
                board_row.append(1)
            else:
                board_row.append(-1)
        board_array.append(board_row)
    return torch.tensor(board_array, dtype=torch.float32).unsqueeze(0).unsqueeze(0)

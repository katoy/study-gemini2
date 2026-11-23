"""局面単位で容量管理する AlphaZero リプレイバッファ。"""
from __future__ import annotations

from collections import deque
from typing import Iterable

import numpy as np
import torch


def _normalize_board(board: np.ndarray | torch.Tensor) -> np.ndarray:
    """盤面表現を (H, W) int8 配列へ正規化する。"""
    if isinstance(board, torch.Tensor):
        arr = board.detach().cpu().numpy()
    else:
        arr = np.asarray(board)
    while arr.ndim > 2 and arr.shape[0] == 1:
        arr = arr[0]
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        raise ValueError(f"Expected square 2D board, got shape {arr.shape}")
    return arr.astype(np.int8, copy=True)


def _normalize_pi(pi: np.ndarray | torch.Tensor) -> np.ndarray:
    """方策ベクトルを (action_size,) float32 配列へ正規化する。"""
    if isinstance(pi, torch.Tensor):
        arr = pi.detach().cpu().numpy()
    else:
        arr = np.asarray(pi)
    if arr.ndim != 1:
        raise ValueError(f"Expected 1D policy vector, got shape {arr.shape}")
    return arr.astype(np.float32, copy=True)


class ReplayBuffer:
    """局面単位の上限を持つ FIFO リプレイバッファ。

    Args:
        max_positions: 保持する最大局面数。
    """

    def __init__(self, max_positions: int = 20_000) -> None:
        if max_positions <= 0:
            raise ValueError(f"max_positions must be > 0, got {max_positions}")
        self.max_positions = max_positions
        self._items: deque[tuple[np.ndarray, np.ndarray, float, str]] = deque(
            maxlen=max_positions
        )

    def __len__(self) -> int:
        return len(self._items)

    def add_samples(
        self,
        samples: Iterable[
            tuple[np.ndarray | torch.Tensor, np.ndarray | torch.Tensor, float]
        ],
        source: str = "selfplay",
    ) -> None:
        """サンプル列を局面単位でバッファへ追加する。"""
        for board, pi, z in samples:
            self._items.append(
                (_normalize_board(board), _normalize_pi(pi), float(z), source)
            )

    def trim_to(self, max_keep: int) -> None:
        """直近 max_keep 局面のみを残し、古い局面を切り捨てる。"""
        if max_keep < 0:
            raise ValueError(f"max_keep must be >= 0, got {max_keep}")
        if max_keep == 0:
            self._items.clear()
            return
        while len(self._items) > max_keep:
            self._items.popleft()

    def stats(self) -> dict[str, int]:
        """データソース別の局面数を返す。"""
        counts: dict[str, int] = {}
        for _, _, _, src in self._items:
            counts[src] = counts.get(src, 0) + 1
        return counts

    def to_tensors(self) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """保持中の全局面を (boards, pis, zs) テンソルに変換する。"""
        if not self._items:
            return (
                torch.empty((0, 1, 8, 8), dtype=torch.float32),
                torch.empty((0, 65), dtype=torch.float32),
                torch.empty((0,), dtype=torch.float32),
            )
        boards_np = np.stack([item[0] for item in self._items], axis=0)
        pis_np = np.stack([item[1] for item in self._items], axis=0)
        zs_np = np.asarray([item[2] for item in self._items], dtype=np.float32)

        boards = torch.from_numpy(boards_np).unsqueeze(1).to(torch.float32)
        pis = torch.from_numpy(pis_np)
        zs = torch.from_numpy(zs_np)
        return boards, pis, zs

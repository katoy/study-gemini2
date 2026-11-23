"""オセロ盤面と方策ベクトルの D4 対称データ拡張（8 倍対称）。"""
from __future__ import annotations

import torch


def transform_board_and_policy(
    board: torch.Tensor,
    pi: torch.Tensor,
    sym_idx: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    """盤面テンソルと方策ベクトルに同一の D4 対称変換（0..7）を適用する。

    Args:
        board: (..., H, W) 形状の盤面テンソル。
        pi: (..., H*W + 1) または (..., H*W) 形状の方策ベクトル。
            末尾 1 要素（PASS_ACTION）は回転・反転の影響を受けず不変。
        sym_idx: 対称操作インデックス（0..7）。
            0..3 は反時計回り 90°×k 回転、4..7 は回転後に左右反転。

    Returns:
        変換後の (board, pi) タプル。

    Raises:
        ValueError: sym_idx が 0..7 の範囲外、または形状が整合しない場合。
    """
    if not 0 <= sym_idx < 8:
        raise ValueError(f"sym_idx must be in 0..7, got {sym_idx}")
    if board.ndim < 2 or board.shape[-2] != board.shape[-1]:
        raise ValueError(f"board must be square in last 2 dims, got {tuple(board.shape)}")

    board_size = board.shape[-1]
    n_cells = board_size * board_size
    if pi.shape[-1] not in (n_cells, n_cells + 1):
        raise ValueError(
            f"pi last dim must be {n_cells} or {n_cells + 1}, got {pi.shape[-1]}"
        )

    rot = sym_idx % 4
    do_flip = sym_idx >= 4

    b_out = torch.rot90(board, k=rot, dims=(-2, -1)) if rot else board
    pi_grid = pi[..., :n_cells].reshape(*pi.shape[:-1], board_size, board_size)
    if rot:
        pi_grid = torch.rot90(pi_grid, k=rot, dims=(-2, -1))

    if do_flip:
        b_out = torch.flip(b_out, dims=(-1,))
        pi_grid = torch.flip(pi_grid, dims=(-1,))

    pi_flat = pi_grid.reshape(*pi.shape[:-1], n_cells)
    if pi.shape[-1] > n_cells:
        pi_out = torch.cat([pi_flat, pi[..., n_cells:]], dim=-1)
    else:
        pi_out = pi_flat

    return b_out, pi_out


def augment_batch_d4(
    boards: torch.Tensor,
    pis: torch.Tensor,
    generator: torch.Generator | None = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    """ミニバッチ各サンプルに一様ランダムな D4 対称変換をオンザフライ適用する。"""
    batch_size = boards.shape[0]
    if batch_size == 0:
        return boards.clone(), pis.clone()

    syms = torch.randint(0, 8, (batch_size,), generator=generator)
    out_boards = torch.empty_like(boards)
    out_pis = torch.empty_like(pis)

    for sym in range(8):
        idx = torch.nonzero(syms == sym, as_tuple=True)[0]
        if idx.numel() == 0:
            continue
        idx_dev = idx.to(boards.device)
        tb, tp = transform_board_and_policy(
            boards.index_select(0, idx_dev),
            pis.index_select(0, idx_dev),
            sym,
        )
        out_boards.index_copy_(0, idx_dev, tb)
        out_pis.index_copy_(0, idx_dev, tp)

    return out_boards, out_pis

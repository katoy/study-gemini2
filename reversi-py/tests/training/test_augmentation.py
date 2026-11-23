"""training/alphazero/augmentation.py のテスト。"""
from __future__ import annotations

import pytest

TORCH_AVAILABLE = True
try:
    import torch
except ImportError:
    TORCH_AVAILABLE = False


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch が必要")
class TestD4Augmentation:
    def test_identity_transform_preserves_tensors(self) -> None:
        from training.alphazero.augmentation import transform_board_and_policy

        board = torch.arange(64, dtype=torch.float32).reshape(1, 8, 8)
        pi = torch.arange(65, dtype=torch.float32)
        b_out, p_out = transform_board_and_policy(board, pi, sym_idx=0)
        assert torch.equal(b_out, board)
        assert torch.equal(p_out, pi)

    def test_all_eight_symmetries_preserve_stones_sum_and_pass(self) -> None:
        from training.alphazero.augmentation import transform_board_and_policy

        board = torch.zeros((1, 8, 8), dtype=torch.float32)
        board[0, 0, 2] = 1.0
        board[0, 3, 4] = -1.0
        pi = torch.zeros(65, dtype=torch.float32)
        pi[0 * 8 + 2] = 0.7
        pi[3 * 8 + 4] = 0.2
        pi[64] = 0.1

        seen_boards: set[tuple[float, ...]] = set()
        for sym in range(8):
            b_out, p_out = transform_board_and_policy(board, pi, sym)
            assert b_out.shape == (1, 8, 8)
            assert p_out.shape == (65,)
            assert float(p_out[64]) == pytest.approx(0.1)
            assert float(p_out.sum()) == pytest.approx(1.0)
            assert int((b_out == 1.0).sum()) == 1
            assert int((b_out == -1.0).sum()) == 1
            # 1 と -1 の位置が方策の 0.7 と 0.2 の座標と一致すること
            pos_1 = int(torch.nonzero(b_out[0] == 1.0, as_tuple=False)[0][0] * 8 + torch.nonzero(b_out[0] == 1.0, as_tuple=False)[0][1])
            pos_m1 = int(torch.nonzero(b_out[0] == -1.0, as_tuple=False)[0][0] * 8 + torch.nonzero(b_out[0] == -1.0, as_tuple=False)[0][1])
            assert float(p_out[pos_1]) == pytest.approx(0.7)
            assert float(p_out[pos_m1]) == pytest.approx(0.2)
            seen_boards.add(tuple(b_out.flatten().tolist()))

        # 一般位置の 2 石ペアなので 8 変換すべてが異なる盤面を作る
        assert len(seen_boards) == 8

    def test_transform_without_pass_action(self) -> None:
        from training.alphazero.augmentation import transform_board_and_policy

        board = torch.eye(4, dtype=torch.float32)
        pi = torch.arange(16, dtype=torch.float32)
        b_out, p_out = transform_board_and_policy(board, pi, sym_idx=5)
        assert b_out.shape == (4, 4)
        assert p_out.shape == (16,)

    def test_invalid_inputs_raise_value_error(self) -> None:
        from training.alphazero.augmentation import transform_board_and_policy

        board = torch.zeros((1, 8, 8))
        pi = torch.zeros(65)
        with pytest.raises(ValueError, match="sym_idx"):
            transform_board_and_policy(board, pi, sym_idx=8)
        with pytest.raises(ValueError, match="square"):
            transform_board_and_policy(torch.zeros((8, 7)), pi, sym_idx=0)
        with pytest.raises(ValueError, match="pi last dim"):
            transform_board_and_policy(board, torch.zeros(60), sym_idx=0)

    def test_augment_batch_d4_shapes_and_empty_batch(self) -> None:
        from training.alphazero.augmentation import augment_batch_d4

        empty_b, empty_p = augment_batch_d4(torch.zeros((0, 1, 8, 8)), torch.zeros((0, 65)))
        assert empty_b.shape == (0, 1, 8, 8)
        assert empty_p.shape == (0, 65)

        boards = torch.zeros((16, 1, 8, 8))
        boards[:, 0, 1, 2] = 1.0
        pis = torch.zeros((16, 65))
        pis[:, 1 * 8 + 2] = 0.8
        pis[:, 64] = 0.2
        gen = torch.Generator().manual_seed(0)

        out_b, out_p = augment_batch_d4(boards, pis, generator=gen)
        assert out_b.shape == (16, 1, 8, 8)
        assert out_p.shape == (16, 65)
        assert torch.allclose(out_p[:, 64], torch.full((16,), 0.2))
        for i in range(16):
            idx = int(torch.argmax(out_p[i, :64]).item())
            r, c = divmod(idx, 8)
            assert float(out_b[i, 0, r, c]) == 1.0

"""training/alphazero/replay_buffer.py のテスト。"""
from __future__ import annotations

import numpy as np
import pytest

TORCH_AVAILABLE = True
try:
    import torch
except ImportError:
    TORCH_AVAILABLE = False


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch が必要")
class TestReplayBuffer:
    def test_invalid_max_positions_raises(self) -> None:
        from training.alphazero.replay_buffer import ReplayBuffer

        with pytest.raises(ValueError, match="max_positions"):
            ReplayBuffer(max_positions=0)

    def test_empty_buffer_to_tensors(self) -> None:
        from training.alphazero.replay_buffer import ReplayBuffer

        buf = ReplayBuffer(max_positions=10)
        boards, pis, zs = buf.to_tensors()
        assert boards.shape == (0, 1, 8, 8)
        assert pis.shape == (0, 65)
        assert zs.shape == (0,)

    def test_add_samples_fifo_eviction_and_stats(self) -> None:
        from training.alphazero.replay_buffer import ReplayBuffer

        buf = ReplayBuffer(max_positions=4)
        samples_a = [
            (np.full((8, 8), i, dtype=np.int8), np.full(65, float(i), dtype=np.float32), float(i))
            for i in range(3)
        ]
        samples_b = [
            (torch.full((1, 1, 8, 8), float(i + 10)), torch.full((65,), float(i + 10)), -1.0)
            for i in range(3)
        ]
        buf.add_samples(samples_a, source="dagger")
        buf.add_samples(samples_b, source="selfplay")

        assert len(buf) == 4
        assert buf.stats() == {"dagger": 1, "selfplay": 3}

        boards, pis, zs = buf.to_tensors()
        assert boards.shape == (4, 1, 8, 8)
        assert pis.shape == (4, 65)
        assert zs.shape == (4,)
        assert float(boards[0, 0, 0, 0]) == 2.0
        assert float(zs[0]) == 2.0
        assert float(boards[1, 0, 0, 0]) == 10.0

    def test_trim_to_and_validation(self) -> None:
        from training.alphazero.replay_buffer import ReplayBuffer

        buf = ReplayBuffer(max_positions=10)
        samples = [
            (np.full((8, 8), i, dtype=np.int8), np.zeros(65, dtype=np.float32), 1.0)
            for i in range(5)
        ]
        buf.add_samples(samples, source="dagger")
        buf.trim_to(2)
        assert len(buf) == 2
        boards, _, _ = buf.to_tensors()
        assert float(boards[0, 0, 0, 0]) == 3.0
        assert float(boards[1, 0, 0, 0]) == 4.0

        buf.trim_to(0)
        assert len(buf) == 0

        with pytest.raises(ValueError, match="max_keep"):
            buf.trim_to(-1)

    def test_invalid_sample_shapes_raise(self) -> None:
        from training.alphazero.replay_buffer import ReplayBuffer

        buf = ReplayBuffer(max_positions=5)
        with pytest.raises(ValueError, match="square 2D board"):
            buf.add_samples([(np.zeros((8, 7)), np.zeros(65), 0.0)])
        with pytest.raises(ValueError, match="1D policy"):
            buf.add_samples([(np.zeros((8, 8)), np.zeros((8, 8)), 0.0)])

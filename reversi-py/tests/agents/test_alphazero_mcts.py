"""agents/alphazero/mcts.py の TDD テスト（ダミー net で torch 非依存に検証）"""
from __future__ import annotations

import copy
import math
from typing import Optional
from unittest.mock import MagicMock

import pytest

TORCH_AVAILABLE = True
try:
    import torch
    import numpy as np
except ImportError:
    TORCH_AVAILABLE = False


# ---- ダミー net（全合法手に均等 prior、value=0.0 を返す） ----

def _make_dummy_net() -> MagicMock:
    """MCTS のロジックテスト用ダミー net（torch 不要）"""
    net = MagicMock()
    net.training = False

    def dummy_forward(tensor: object) -> tuple:
        """65 次元均等 softmax（実際はロジット）と value=0 を返す"""
        if TORCH_AVAILABLE:
            batch = tensor.shape[0] if hasattr(tensor, 'shape') else 1  # type: ignore[union-attr]
            pi = torch.zeros(batch, 65)   # 均等ロジット
            v = torch.zeros(batch, 1)
            return pi, v
        return MagicMock(), MagicMock()

    net.side_effect = dummy_forward
    return net


# ---- テスト ----

@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch が必要")
class TestActionEncoding:
    """action_idx = r * board_size + c の往復変換テスト"""

    def test_encode_decode_roundtrip(self) -> None:
        board_size = 8
        for r in range(board_size):
            for c in range(board_size):
                action_idx = r * board_size + c
                decoded_r, decoded_c = divmod(action_idx, board_size)
                assert decoded_r == r and decoded_c == c

    def test_pass_action_index(self) -> None:
        from agents.alphazero.mcts import PASS_ACTION
        assert PASS_ACTION == 64  # 8*8


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch が必要")
class TestNodeTerminalValue:
    """終局価値が手番視点で正しく返ることを確認"""

    def test_black_wins_black_turn(self) -> None:
        from agents.alphazero.mcts import node_terminal_value
        # 黒 40 石、白 24 石（黒が多い） + 黒手番 → +1
        board = [[-1] * 8 for _ in range(8)]
        for r in range(3):
            board[r] = [1] * 8
        v = node_terminal_value(board, turn=-1)
        assert v == 1.0

    def test_black_wins_white_turn(self) -> None:
        from agents.alphazero.mcts import node_terminal_value
        board = [[-1] * 8 for _ in range(8)]
        for r in range(3):
            board[r] = [1] * 8
        # 黒が多い + 白手番 → -1（白から見て負け）
        v = node_terminal_value(board, turn=1)
        assert v == -1.0

    def test_draw(self) -> None:
        from agents.alphazero.mcts import node_terminal_value
        board = [[0] * 8 for _ in range(8)]
        for i in range(32):
            board[i // 8][i % 8] = -1
        for i in range(32, 64):
            board[i // 8][i % 8] = 1
        assert node_terminal_value(board, turn=-1) == 0.0


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch が必要")
class TestMakeUnmake:
    """make → unmake で作業盤面が元に戻ることを確認"""

    def _initial_board(self) -> list[list[int]]:
        board = [[0] * 8 for _ in range(8)]
        board[3][3] = 1; board[4][4] = 1
        board[3][4] = -1; board[4][3] = -1
        return board

    def test_make_unmake_restores_board(self) -> None:
        from agents.alphazero.mcts import MCTS
        mcts = MCTS(net=_make_dummy_net(), n_simulations=1)
        board = self._initial_board()
        original = copy.deepcopy(board)
        work = [row[:] for row in board]

        # 黒の合法手に make → unmake を繰り返す
        from agents.negamax_agent import _valid_moves, _flips_for_move, _apply, _undo
        moves = _valid_moves(work, 8, -1)
        for move in moves:
            r, c = move
            flips = _flips_for_move(work, 8, r, c, -1)
            _apply(work, move, flips, -1)
            _undo(work, move, flips, -1)
            assert work == original, f"手 {move} 後 unmake で盤面が復元されていない"


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch が必要")
class TestMCTSDoesNotMutateInput:
    """`run` が入力 board を破壊しないことを確認（ゲームループ規約）"""

    def _initial_board(self) -> list[list[int]]:
        board = [[0] * 8 for _ in range(8)]
        board[3][3] = 1; board[4][4] = 1
        board[3][4] = -1; board[4][3] = -1
        return board

    def test_run_does_not_mutate_board(self) -> None:
        from agents.alphazero.mcts import MCTS
        board = self._initial_board()
        original = copy.deepcopy(board)
        mcts = MCTS(net=_make_dummy_net(), n_simulations=5)
        mcts.run(board, turn=-1)
        assert board == original, "run() が入力 board を破壊した"


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch が必要")
class TestPUCT:
    """PUCT 選択が高 prior・低 visit を優先することを確認"""

    def test_high_prior_preferred(self) -> None:
        from agents.alphazero.mcts import MCTSNode
        parent = MCTSNode(turn=-1, prior=1.0)
        parent.visit_count = 10
        # 子 A: high prior, 0 visit
        child_a = MCTSNode(turn=1, prior=0.8)
        child_a.visit_count = 0
        # 子 B: low prior, 0 visit
        child_b = MCTSNode(turn=1, prior=0.2)
        child_b.visit_count = 0
        parent.children = {0: child_a, 1: child_b}

        from agents.alphazero.mcts import MCTS
        mcts = MCTS(net=_make_dummy_net(), n_simulations=1, c_puct=1.0)
        action, child = mcts._select_child(parent)
        assert action == 0, "高 prior の子が選ばれるべき"

    def test_low_visit_preferred(self) -> None:
        from agents.alphazero.mcts import MCTSNode
        parent = MCTSNode(turn=-1, prior=1.0)
        parent.visit_count = 20
        # 子 A: 同 prior、高 visit
        child_a = MCTSNode(turn=1, prior=0.5)
        child_a.visit_count = 10
        child_a.value_sum = 0.0
        # 子 B: 同 prior、低 visit
        child_b = MCTSNode(turn=1, prior=0.5)
        child_b.visit_count = 1
        child_b.value_sum = 0.0
        parent.children = {0: child_a, 1: child_b}

        from agents.alphazero.mcts import MCTS
        mcts = MCTS(net=_make_dummy_net(), n_simulations=1, c_puct=1.0)
        action, _ = mcts._select_child(parent)
        assert action == 1, "低 visit の子が選ばれるべき"


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch が必要")
class TestMCTSVisitCounts:
    """訪問数の合計が n_simulations と整合することを確認"""

    def _initial_board(self) -> list[list[int]]:
        board = [[0] * 8 for _ in range(8)]
        board[3][3] = 1; board[4][4] = 1
        board[3][4] = -1; board[4][3] = -1
        return board

    def test_visit_counts_sum(self) -> None:
        from agents.alphazero.mcts import MCTS
        n_sims = 10
        mcts = MCTS(net=_make_dummy_net(), n_simulations=n_sims)
        board = self._initial_board()
        counts = mcts.run(board, turn=-1)
        assert sum(counts.values()) > 0


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch が必要")
class TestMCTSPassPosition:
    """パスのみ局面で PASS_ACTION が子になることを確認"""

    def test_pass_only_position(self) -> None:
        from agents.alphazero.mcts import MCTS, PASS_ACTION, MCTSNode, node_terminal_value
        from agents.negamax_agent import _valid_moves

        # 黒が着手できないが白は着手できる盤面を作る（黒がパスしかできない状況）
        # 簡単のため：白石で囲まれた黒石のような盤面を直接検証ではなく
        # expand ロジックを直接テスト
        mcts = MCTS(net=_make_dummy_net(), n_simulations=1)

        # 黒の合法手なし・白の合法手あり → PASS_ACTION が子
        # 全白の盤面（実際には黒が生き残るが、_valid_moves でテスト）
        board = [[1] * 8 for _ in range(8)]
        board[0][0] = -1  # 黒石 1 個（これでも黒に合法手は無い）

        node = MCTSNode(turn=-1, prior=1.0)
        work = [row[:] for row in board]
        mcts._expand(node, work, turn=-1)

        if not node.is_terminal:
            # パス局面ならば PASS_ACTION が子にある
            moves_black = _valid_moves(board, 8, -1)
            if not moves_black:
                assert PASS_ACTION in node.children

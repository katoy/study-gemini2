"""TranspositionNegamaxAgent（TT + PVS + Killer + History）のテスト。"""
import pytest

from agents.negamax_agent import _apply, _flips_for_move, _undo
from agents.transposition_negamax_agent import TranspositionNegamaxAgent


def _initial_board() -> list[list[int]]:
    """8x8 の初期盤面を返す。"""
    board = [[0] * 8 for _ in range(8)]
    board[3][3] = 1   # 白
    board[4][4] = 1   # 白
    board[3][4] = -1  # 黒
    board[4][3] = -1  # 黒
    return board


class TestZobristHash:
    """Zobrist ハッシュ関連のテスト。"""

    def test_zobrist_hash_empty_board(self) -> None:
        """空盤面のハッシュは int 型で計算できる。"""
        agent = TranspositionNegamaxAgent()
        board = [[0] * 8 for _ in range(8)]
        h = agent._compute_initial_hash(board, 8)
        assert isinstance(h, int)

    def test_zobrist_hash_deterministic(self) -> None:
        """同じ盤面から計算したハッシュは一定。"""
        agent1 = TranspositionNegamaxAgent()
        agent2 = TranspositionNegamaxAgent()
        board = _initial_board()
        h1 = agent1._compute_initial_hash(board, 8)
        h2 = agent2._compute_initial_hash(board, 8)
        assert h1 == h2

    def test_zobrist_symmetry(self) -> None:
        """同じ着手を make → undo すると、盤面が元に戻る。"""
        board = _initial_board()
        original = [row[:] for row in board]

        move = (2, 3)
        flips = _flips_for_move(board, 8, 2, 3, -1)
        assert len(flips) > 0

        _apply(board, move, flips, -1)
        _undo(board, move, flips, -1)

        assert board == original


class TestTranspositionTable:
    """トランスポジションテーブル関連のテスト。"""

    def test_tt_stores_entry(self) -> None:
        """TT にエントリを格納・取得できる。"""
        from agents.transposition_negamax_agent import TTEntry
        agent = TranspositionNegamaxAgent()
        hash_val = 12345
        entry: TTEntry = {'flag': 'EXACT', 'depth': 3, 'value': 10.0, 'best_move': (2, 3)}
        agent._tt[hash_val] = entry

        retrieved = agent._tt.get(hash_val)
        assert retrieved is not None
        assert retrieved['flag'] == 'EXACT'
        assert retrieved['value'] == 10.0

    def test_tt_lookup_miss(self) -> None:
        """TT miss で None が返される。"""
        agent = TranspositionNegamaxAgent()
        retrieved = agent._tt.get(99999)
        assert retrieved is None


class TestKillerMoveHeuristic:
    """Killer move heuristic のテスト。"""

    def test_killer_moves_initialized(self) -> None:
        """Killer move スロットが初期化される。"""
        agent = TranspositionNegamaxAgent()
        assert len(agent._killers) > 0
        for slot in agent._killers:
            assert isinstance(slot, set)


class TestTranspositionNegamaxAgentBasic:
    """TranspositionNegamaxAgent の基本動作テスト。"""

    def test_agent_initialization(self) -> None:
        """エージェントが初期化できる。"""
        agent = TranspositionNegamaxAgent(time_limit_ms=500)
        assert agent._time_limit_ms == 500

    def test_agent_play_returns_valid_move(self) -> None:
        """play() が合法手またはパスを返す。"""
        from game import Game
        agent = TranspositionNegamaxAgent(time_limit_ms=100)
        game = Game(board_size=8)
        move = agent.play(game)
        # 初期盤面では黒が手を打つ。合法手は存在する。
        assert move is not None
        assert isinstance(move, tuple)
        assert len(move) == 2
        assert 0 <= move[0] < 8 and 0 <= move[1] < 8

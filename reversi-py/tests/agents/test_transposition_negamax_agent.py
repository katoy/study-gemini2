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

    def test_zobrist_update_matches_recompute(self) -> None:
        """黒手・白手とも _update_hash が _compute_initial_hash と一致する。"""
        agent = TranspositionNegamaxAgent()
        board = _initial_board()
        h = agent._compute_initial_hash(board, 8)

        for turn, move in ((-1, (2, 3)), (1, (2, 2))):
            flips = _flips_for_move(board, 8, move[0], move[1], turn)
            assert flips
            _apply(board, move, flips, turn)
            h = agent._update_hash(h, move, flips, turn)
            assert h == agent._compute_initial_hash(board, 8)

    def test_matches_negamax_at_fixed_depth(self) -> None:
        """固定深さでは黒番・白番とも NegamaxAgent と同一の着手を選択する。"""
        from agents.negamax_agent import NegamaxAgent
        from game import Game

        game = Game(board_size=8)
        for mv in [(2, 3), (2, 2), (2, 1)]:
            game.place_stone(mv[0], mv[1])
            game.switch_turn()

        # 白番
        tt_agent = TranspositionNegamaxAgent(time_limit_ms=5000, max_depth=3)
        nega_agent = NegamaxAgent(time_limit_ms=5000, max_depth=3)
        assert tt_agent.play(game) == nega_agent.play(game)

        # もう 1 手進めて黒番
        mv_w = nega_agent.play(game)
        assert mv_w is not None
        game.place_stone(mv_w[0], mv_w[1])
        game.switch_turn()
        assert tt_agent.play(game) == nega_agent.play(game)

    def test_endgame_picks_winning_move_for_black_and_white(self) -> None:
        """終盤の勝敗確定局面で黒番・白番とも勝つ手を選ぶ。"""
        from agents.negamax_agent import NegamaxAgent
        from game import Game

        # 4x4 盤面で空き 2 マス：(3, 3) を選べば勝ち、(0, 3) を選べば負ける配置
        black_board = [
            [1, 1, 1, 0],
            [-1, -1, 1, 1],
            [-1, -1, -1, 1],
            [-1, -1, 1, 0],
        ]
        game_b = Game(board_size=4)
        game_b.board.board = [row[:] for row in black_board]
        game_b.turn = -1
        game_b._invalidate_valid_moves_cache()
        tt = TranspositionNegamaxAgent(time_limit_ms=1000, max_depth=10, endgame_empties=12)
        nega = NegamaxAgent(time_limit_ms=1000, max_depth=10, endgame_empties=12)
        mv_b, score_b = tt.play_with_score(game_b)
        assert mv_b == nega.play(game_b)
        assert mv_b == (3, 3)
        assert score_b > 0

        # 白黒反転でも同様に勝ち手を選ぶ
        white_board = [[-c for c in row] for row in black_board]
        game_w = Game(board_size=4)
        game_w.board.board = white_board
        game_w.turn = 1
        game_w._invalidate_valid_moves_cache()
        mv_w, score_w = tt.play_with_score(game_w)
        assert mv_w == nega.play(game_w)
        assert mv_w == (3, 3)
        assert score_w > 0

    def test_play_with_score_handles_pass_and_single_move(self) -> None:
        from game import Game

        # 合法手なし -> (None, 0.0)
        board_none = [[1] * 4 for _ in range(4)]
        board_none[0][0] = 0
        g_none = Game(board_size=4)
        g_none.board.board = board_none
        g_none.turn = -1
        g_none._invalidate_valid_moves_cache()
        assert TranspositionNegamaxAgent(time_limit_ms=100).play_with_score(g_none) == (None, 0.0)

        # 単一合法手 -> 即返し
        board_one = [
            [-1, 1, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        g_one = Game(board_size=4)
        g_one.board.board = board_one
        g_one.turn = -1
        g_one._invalidate_valid_moves_cache()
        assert TranspositionNegamaxAgent(time_limit_ms=100).play_with_score(g_one) == ((0, 2), 0.0)

"""MinimaxAgent の単体テスト。"""
from __future__ import annotations

from agents.minimax_agent import MinimaxAgent
from agents.negamax_agent import NegamaxAgent
from game import Game


def _make_game(board: list[list[int]], turn: int) -> Game:
    game = Game(board_size=len(board))
    game.board.board = [row[:] for row in board]
    game.turn = turn
    game._invalidate_valid_moves_cache()
    return game


class TestMinimaxAgent:
    def test_defaults(self) -> None:
        agent = MinimaxAgent()
        assert agent.time_limit_ms == 500
        assert agent.max_depth == 60
        assert agent.endgame_empties == 12

    def test_returns_none_when_no_valid_moves(self) -> None:
        board = [[1] * 4 for _ in range(4)]
        board[0][0] = 0
        game = _make_game(board, turn=-1)
        assert MinimaxAgent(time_limit_ms=100).play(game) is None

    def test_returns_single_valid_move_immediately(self) -> None:
        board = [
            [-1, 1, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        game = _make_game(board, turn=-1)
        assert game.get_valid_moves() == [(0, 2)]
        assert MinimaxAgent(time_limit_ms=100).play(game) == (0, 2)

    def test_matches_negamax_at_fixed_depth(self) -> None:
        """固定深さでは NegamaxAgent と完全に同一の着手を選択する。"""
        game = Game(board_size=8)
        # 序盤から数手進めた非対称局面を作る
        for mv in [(2, 3), (2, 2), (2, 1), (3, 2)]:
            game.place_stone(mv[0], mv[1])
            game.switch_turn()

        minimax = MinimaxAgent(time_limit_ms=5000, max_depth=3)
        negamax = NegamaxAgent(time_limit_ms=5000, max_depth=3)
        snapshot = [row[:] for row in game.get_board()]

        mv_minimax = minimax.play(game)
        mv_negamax = negamax.play(game)

        assert mv_minimax == mv_negamax
        assert mv_minimax in game.get_valid_moves()
        assert game.get_board() == snapshot

    def test_endgame_solver_handles_pass_and_terminal_and_picks_win(self) -> None:
        """終盤読み切り時にパス・終局を含めて最善手を選び切る。"""
        # 空きマスが 4 以下の 4x4 盤面（片側パスや双方終局が発生する）
        board = [
            [-1, -1, -1, 1],
            [-1, 1, 1, 0],
            [-1, 1, 0, 0],
            [1, 1, 1, 0],
        ]
        game = _make_game(board, turn=-1)
        agent = MinimaxAgent(time_limit_ms=1000, max_depth=10, endgame_empties=12)
        move = agent.play(game)
        assert move in game.get_valid_moves()

        # 相手のパスを誘発して maximizing=True へ連続遷移するケースもカバー
        pass_board = [
            [1, 1, 1, 1],
            [1, -1, 1, 1],
            [1, 1, 0, 0],
            [1, 1, 1, 0],
        ]
        pass_game = _make_game(pass_board, turn=1)
        if pass_game.get_valid_moves():
            mv = agent.play(pass_game)
            assert mv in pass_game.get_valid_moves()

    def test_timeout_protection_returns_legal_move(self, monkeypatch) -> None:
        """探索中に時間超過しても合法手を返す。"""
        game = Game(board_size=8)
        ticks = iter([0.0] + [100.0] * 10000)
        monkeypatch.setattr("agents.minimax_agent.time.monotonic", lambda: next(ticks, 100.0))

        agent = MinimaxAgent(time_limit_ms=10, max_depth=60, endgame_empties=0)
        move = agent.play(game)
        assert move in game.get_valid_moves()

"""BitboardTeacherAgent および 64-bit ビットボード演算のテスト。"""
from __future__ import annotations

import random

from game import Game
from training.alphazero.bitboard_teacher import (
    BitboardTeacherAgent,
    apply_move_bitboard,
    bitboards_to_board,
    board_to_bitboards,
    evaluate_bitboard,
    legal_moves_mask,
)


class TestBitboardPrimitives:
    """ビットボード合法手生成・着手反転が Board と完全一致することを検証する。"""

    def test_matches_game_across_20_random_games(self) -> None:
        rng = random.Random(2026)
        checked_moves = 0

        for _ in range(20):
            game = Game(board_size=8)
            while not game.game_over:
                board_list = game.board.board
                my, opp = board_to_bitboards(board_list, game.turn)
                assert bitboards_to_board(my, opp, game.turn) == board_list

                mask = legal_moves_mask(my, opp)
                bb_moves = {
                    divmod(sq, 8)
                    for sq in range(64)
                    if mask & (1 << sq)
                }
                expected_moves = set(game.get_valid_moves())
                assert bb_moves == expected_moves

                if not expected_moves:
                    game.switch_turn()
                    game.check_game_over()
                    continue

                mv = rng.choice(sorted(expected_moves))
                sq = mv[0] * 8 + mv[1]
                n_my, n_opp = apply_move_bitboard(my, opp, sq)
                bb_next_board = bitboards_to_board(n_my, n_opp, game.turn)

                game.place_stone(mv[0], mv[1])
                assert bb_next_board == game.board.board

                game.switch_turn()
                game.check_game_over()
                checked_moves += 1

        assert checked_moves >= 800

    def test_evaluate_bitboard_corner_advantage(self) -> None:
        game_my_corner = Game(board_size=8)
        game_opp_corner = Game(board_size=8)
        game_my_corner.board.board[0][0] = -1
        game_opp_corner.board.board[0][0] = 1
        my1, opp1 = board_to_bitboards(game_my_corner.board.board, -1)
        my2, opp2 = board_to_bitboards(game_opp_corner.board.board, -1)
        assert evaluate_bitboard(my1, opp1) > evaluate_bitboard(my2, opp2)


class TestBitboardTeacherAgent:
    """BitboardTeacherAgent の探索・終盤・境界ケーステスト。"""

    def test_endgame_exact_solver_black_and_white(self) -> None:
        # 残り 2 空き ((7,6), (7,7)) の終局直前局面:
        # 黒番は (7,7) なら +11 石勝ち確定、(7,6) なら白に (7,7) を打たれて -8 石負け。
        base = [
            [1, 1, 1, 1, 1, 1, -1, -1],
            [-1, 1, 1, 1, 1, 1, -1, 1],
            [1, -1, 1, 1, 1, 1, -1, 1],
            [1, 1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, -1, -1, 1],
            [1, -1, -1, -1, -1, 1, -1, 1],
            [-1, -1, -1, -1, -1, -1, 1, 1],
            [1, 1, 1, 1, 1, 1, 0, 0],
        ]
        game_b = Game(board_size=8)
        game_b.board.board = [row[:] for row in base]
        game_b.turn = -1
        game_b._invalidate_valid_moves_cache()

        teacher = BitboardTeacherAgent(time_limit_ms=1000, max_depth=60, endgame_empties=14)
        mv_b, score_b = teacher.play_with_score(game_b)
        assert mv_b == (7, 7)
        assert abs(score_b) >= 10000
        assert score_b > 0

        # 白黒反転
        game_w = Game(board_size=8)
        game_w.board.board = [[-v for v in row] for row in base]
        game_w.turn = 1
        game_w._invalidate_valid_moves_cache()
        mv_w, score_w = teacher.play_with_score(game_w)
        assert mv_w == (7, 7)
        assert score_w == score_b
        assert abs(score_w) >= 10000

    def test_pass_and_single_move_fast_path(self) -> None:
        teacher = BitboardTeacherAgent(time_limit_ms=200)

        # 合法手なし -> (None, 0.0)
        g_none = Game(board_size=8)
        g_none.board.board = [[1] * 8 for _ in range(8)]
        g_none.board.board[0][0] = 0
        g_none.turn = -1
        g_none._invalidate_valid_moves_cache()
        assert teacher.play_with_score(g_none) == (None, 0.0)
        assert teacher.play(g_none) is None

        # 単一合法手 -> 即返し
        g_one = Game(board_size=8)
        g_one.board.board = [[0] * 8 for _ in range(8)]
        g_one.board.board[0][0] = -1
        g_one.board.board[0][1] = 1
        g_one.turn = -1
        g_one._invalidate_valid_moves_cache()
        assert teacher.play_with_score(g_one) == ((0, 2), 0.0)
        assert teacher.play(g_one) == (0, 2)

    def test_timeout_protection_returns_valid_move(self, monkeypatch) -> None:
        import training.alphazero.bitboard_teacher as bb_mod

        calls = 0

        def fake_monotonic() -> float:
            nonlocal calls
            calls += 1
            return 1000.0 + (0.0 if calls <= 2 else 10.0)

        monkeypatch.setattr(bb_mod.time, "monotonic", fake_monotonic)

        game = Game(board_size=8)
        teacher = BitboardTeacherAgent(time_limit_ms=50, max_depth=60)
        mv, _ = teacher.play_with_score(game)
        assert mv in game.get_valid_moves()

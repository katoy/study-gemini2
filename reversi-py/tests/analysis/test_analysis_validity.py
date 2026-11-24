"""解説内容の妥当性（反事実検証・戦術シナリオ・誤検出防止・不変条件）テスト。"""
from __future__ import annotations

import random
from unittest.mock import patch

from agents.gain_agent import GainAgent
from agents.random_agent import RandomAgent
from analysis import analyze_game
from board import Board
from game import Game
from training.alphazero.bitboard_teacher import BitboardTeacherAgent


def _playout_from(
    board_before: list[list[int]],
    turn: int,
    first_move: tuple[int, int],
    agent: BitboardTeacherAgent,
) -> int:
    """board_before から first_move を打った後、agent 同士で終局まで指して turn 視点石差を返す。"""
    g = Game(8)
    g.board.board = [row[:] for row in board_before]
    g.turn = turn
    g._invalidate_valid_moves_cache()
    assert g.place_stone(first_move[0], first_move[1]) is True
    g.switch_turn()
    g.check_game_over()

    while not g.game_over:
        valid = g.get_valid_moves()
        if valid:
            move = agent.play(g)
            assert move is not None
            assert g.place_stone(move[0], move[1]) is True
        g.switch_turn()
        g.check_game_over()

    b_cnt, w_cnt = g.board.count_stones()
    return (b_cnt - w_cnt) if turn == -1 else (w_cnt - b_cnt)


def _play_game_with_agents(black_agent, white_agent, seed: int = 0) -> Game:
    random.seed(seed)
    g = Game(8)
    while not g.game_over:
        a = black_agent if g.turn == -1 else white_agent
        m = a.play(g)
        if m is not None:
            g.place_stone(m[0], m[1])
        g.switch_turn()
        g.check_game_over()
    return g


def test_counterfactual_endgame_best_move_wins_played_move_loses() -> None:
    """終盤敗着の反事実検証: best_move なら本当に勝ち/引分、played_move だと本当に負ける。"""
    # Random(seed=42) vs Gain は第55手で終盤角見逃しの決定的敗着が起きる実対局
    g = _play_game_with_agents(RandomAgent(), GainAgent(), seed=42)
    res = analyze_game(g.history, midgame_time_ms=40, endgame_time_ms=200, endgame_empties=12)

    assert res.loser == -1
    assert res.key_mistakes
    decisive = res.key_mistakes[0]
    assert decisive.is_decisive is True
    assert decisive.is_exact is True
    assert decisive.best_disc_diff is not None and decisive.best_disc_diff > 0
    assert decisive.played_disc_diff is not None and decisive.played_disc_diff < 0
    assert res.missed_win_move_index == decisive.move_index
    assert res.loss_sealed_move_index == decisive.move_index
    assert res.draw_sealed_move_index is None
    assert "missed_win" in decisive.outcome_tags
    assert "loss_sealed" in decisive.outcome_tags
    assert "【勝ち逃し・負け確定】" in decisive.summary
    assert "勝ちを逃し" in res.headline and "負けが決定しました" in res.headline

    oracle = BitboardTeacherAgent(time_limit_ms=150, endgame_empties=14)
    actual_best_diff = _playout_from(
        decisive.board_before, decisive.turn, decisive.best_move, oracle
    )
    actual_played_diff = _playout_from(
        decisive.board_before, decisive.turn, decisive.played_move, oracle
    )
    assert actual_best_diff >= 0, "推奨手 best_move で終局まで指したのに負けた"
    assert actual_played_diff < 0, "実戦手 played_move で終局まで指したのに負けなかった"
    assert actual_played_diff == decisive.played_disc_diff


def test_tactical_scenarios_golden() -> None:
    """角見逃し・X 打ち献上・C 打ち献上の戦術シナリオを実対局から正しく解説できる。"""
    # 1. 角見逃し（Random vs Gain seed=42 の第55手: H8 を見逃して F8）
    g_corner = _play_game_with_agents(RandomAgent(), GainAgent(), seed=42)
    res_corner = analyze_game(g_corner.history, midgame_time_ms=30, endgame_time_ms=150)
    top = res_corner.key_mistakes[0]
    assert "missed_corner" in top.reason_codes
    assert top.best_move in {(0, 0), (0, 7), (7, 0), (7, 7)}
    assert "見逃してしまいました" in top.explanation

    # 2. X 打ち / C 打ちによる角献上が起きた実対局を生成して検証
    x_squares = {(1, 1): (0, 0), (1, 6): (0, 7), (6, 1): (7, 0), (6, 6): (7, 7)}
    c_squares = {
        (0, 1): (0, 0), (1, 0): (0, 0),
        (0, 6): (0, 7), (1, 7): (0, 7),
        (6, 0): (7, 0), (7, 1): (7, 0),
        (6, 7): (7, 7), (7, 6): (7, 7),
    }

    def find_corner_gift_game(squares: dict[tuple[int, int], tuple[int, int]]) -> tuple[Game, int]:
        teacher = BitboardTeacherAgent(time_limit_ms=30, endgame_empties=12)
        for seed in range(50):
            rng = random.Random(seed)
            g = Game(8)
            gifted_idx: int | None = None
            while not g.game_over:
                valid = g.get_valid_moves()
                if valid:
                    chosen = None
                    if gifted_idx is None and g.turn == 1 and len(valid) >= 2:
                        # 白番で X/C マスがあり、打った直後に黒が対応角を取れるならあえて打つ
                        for mv in valid:
                            if mv in squares:
                                test_b = Board(8)
                                test_b.board = [r[:] for r in g.get_board()]
                                test_b.place_stone(mv[0], mv[1], 1)
                                corner = squares[mv]
                                if corner in test_b.get_valid_moves(-1):
                                    chosen = mv
                                    gifted_idx = len(g.history)
                                    break
                    if chosen is None:
                        if gifted_idx is not None and g.turn == -1:
                            chosen = teacher.play(g)
                        else:
                            chosen = rng.choice(valid)
                    assert chosen is not None
                    g.place_stone(chosen[0], chosen[1])
                g.switch_turn()
                g.check_game_over()
            if gifted_idx is not None and g.get_winner() == -1:
                return g, gifted_idx
        raise AssertionError("角献上テスト局面の生成に失敗しました")

    g_x, x_idx = find_corner_gift_game(x_squares)
    res_x = analyze_game(g_x.history, midgame_time_ms=30, endgame_time_ms=150)
    ma_x = res_x.moves_by_index[x_idx]
    assert "gave_corner_x" in ma_x.reason_codes
    assert ma_x.refutation_move == x_squares[ma_x.played_move]
    assert "Xマス" in ma_x.explanation

    g_c, c_idx = find_corner_gift_game(c_squares)
    res_c = analyze_game(g_c.history, midgame_time_ms=30, endgame_time_ms=150)
    ma_c = res_c.moves_by_index[c_idx]
    assert "gave_corner_c" in ma_c.reason_codes
    assert ma_c.refutation_move == c_squares[ma_c.played_move]
    assert "Cマス" in ma_c.explanation


def test_no_false_positive_decisive_and_garbage_time_ranking() -> None:
    """序盤の微小差を「負け確定」と誤認せず、大敗後の終盤ゴミ時間手が1位に来ない。"""
    # Gain(黒) vs Bitboard(白)
    g1 = _play_game_with_agents(GainAgent(), BitboardTeacherAgent(time_limit_ms=40))
    res1 = analyze_game(g1.history, midgame_time_ms=40, endgame_time_ms=150)
    assert res1.key_mistakes
    for m in res1.key_mistakes:
        if m.move_number <= 6:
            assert m.is_decisive is False

    # Bitboard(黒) vs Gain(白)（大差敗戦）
    g2 = _play_game_with_agents(BitboardTeacherAgent(time_limit_ms=40), GainAgent())
    res2 = analyze_game(g2.history, midgame_time_ms=40, endgame_time_ms=150)
    assert res2.key_mistakes
    top2 = res2.key_mistakes[0]
    # -40石以下の絶望的な終盤手ではなく、序中盤の形勢を失った手が選ばれる
    assert not (top2.is_exact and top2.best_disc_diff is not None and top2.best_disc_diff <= -40)


def test_real_game_invariants_across_all_analyzed_moves() -> None:
    """実対局の全解析着手について、合法性・PV整合性・反撃手整合性・文言整合性を検証する。"""
    g = _play_game_with_agents(RandomAgent(), GainAgent(), seed=42)
    res = analyze_game(g.history, midgame_time_ms=40, endgame_time_ms=150)

    assert len(res.moves_by_index) > 0
    for idx, ma in res.moves_by_index.items():
        b_obj = Board(8)
        b_obj.board = [r[:] for r in ma.board_before]
        valid = b_obj.get_valid_moves(ma.turn)

        assert ma.played_move in valid
        assert ma.best_move in valid
        assert ma.pv and ma.pv[0] == ma.best_move

        # PV が board_before から全手合法に再生できること
        pv_board = Board(8)
        pv_board.board = [r[:] for r in ma.board_before]
        cur_turn = ma.turn
        for step in ma.pv:
            if not pv_board.get_valid_moves(cur_turn):
                cur_turn = -cur_turn
            assert step in pv_board.get_valid_moves(cur_turn)
            assert pv_board.place_stone(step[0], step[1], cur_turn) is True
            cur_turn = -cur_turn

        # refutation_move があれば実戦手適用後の相手（パス時は自分）合法手であること
        if ma.refutation_move is not None:
            ref_board = Board(8)
            ref_board.board = [r[:] for r in ma.board_before]
            assert ref_board.place_stone(ma.played_move[0], ma.played_move[1], ma.turn) is True
            opp_valid = ref_board.get_valid_moves(-ma.turn)
            if opp_valid:
                assert ma.refutation_move in opp_valid

        # is_exact と disc_diff の整合性
        if ma.is_exact:
            assert ma.played_disc_diff is not None and ma.best_disc_diff is not None
        else:
            assert ma.played_disc_diff is None and ma.best_disc_diff is None

        assert ma.explanation.strip() != ""
        assert "相手（" not in ma.explanation


def test_explicit_win_draw_loss_branch_patterns() -> None:
    """勝ち逃し・負け確定・アイコ確定の各遷移パターンが明示的に出力される。"""
    # 初期盤面から合法的に指した 4 手（黒が負ける形 & 引き分け形の 2 本のダミー最終盤面）を用意
    g_loss = Game(8)
    for move in ((2, 3), (2, 2), (2, 1), (2, 4)):
        g_loss.place_stone(move[0], move[1])
        g_loss.switch_turn()
    # 最終盤面だけ白 (1) 優勢にして loser = -1 とし、黒の 2 手（idx=0, idx=2）が候補になるようにする
    # （history 上の盤面と勝敗だけ制御しつつ、盤面はすべて 8x8 合法手 2 手以上）
    loss_hist = [
        (g_loss.history[0][0], -1, g_loss.history[0][2]),
        (g_loss.history[1][0], 1, g_loss.history[1][2]),
        (g_loss.history[2][0], -1, g_loss.history[2][2]),
        (
            g_loss.history[3][0],
            1,
            [[1 if (r + c) % 2 == 0 else -1 for c in range(8)] for r in range(8)],
        ),
    ]
    # 最終盤面が 32 vs 32 にならないよう 1 マス白に変更 -> 黒31, 白33 (loser=-1)
    loss_hist[-1][2][0][1] = 1

    # パターン A: Win -> Draw -> Loss（第1手で勝ち逃し、第3手で負け決定）
    with patch("analysis.game_analyzer.BitboardTeacherAgent") as MockBB, patch(
        "analysis.game_analyzer._evaluate_after_move"
    ) as mock_after:
        inst = MockBB.return_value
        inst._tt = {}
        # 1手目: 最善は +4石、実戦は 0石（アイコ）、3手目: 最善は 0石、実戦は -6石（負け決定）
        inst.play_with_score.side_effect = [
            ((3, 2), 40000.0),
            ((4, 2), 0.0),
        ]
        mock_after.side_effect = [
            (0.0, (2, 2), True),
            (-60000.0, (2, 4), True),
        ]
        res_wdl = analyze_game(loss_hist, endgame_empties=64, max_mistakes=3)

    assert res_wdl.missed_win_move_index == 0
    assert res_wdl.loss_sealed_move_index == 2
    assert res_wdl.draw_sealed_move_index is None
    assert "missed_win" in res_wdl.moves_by_index[0].outcome_tags
    assert "loss_sealed" in res_wdl.moves_by_index[2].outcome_tags
    assert "【勝ちを逃した手】" in res_wdl.moves_by_index[0].summary
    assert "【負けが決定した手】" in res_wdl.moves_by_index[2].summary
    assert "第1手" in res_wdl.headline and "勝ちを逃し" in res_wdl.headline
    assert "第3手" in res_wdl.headline and "負けが決定しました" in res_wdl.headline
    assert {m.move_index for m in res_wdl.key_mistakes} >= {0, 2}

    # パターン B: Draw -> Loss（もともとアイコ最善だったのに第3手で負け決定）
    with patch("analysis.game_analyzer.BitboardTeacherAgent") as MockBB, patch(
        "analysis.game_analyzer._evaluate_after_move"
    ) as mock_after:
        inst = MockBB.return_value
        inst._tt = {}
        inst.play_with_score.side_effect = [
            ((3, 2), 0.0),
            ((4, 2), 0.0),
        ]
        mock_after.side_effect = [
            (0.0, (2, 2), True),
            (-40000.0, (2, 4), True),
        ]
        res_dl = analyze_game(loss_hist, endgame_empties=64, max_mistakes=3)

    assert res_dl.missed_win_move_index is None
    assert res_dl.loss_sealed_move_index == 2
    assert "【負けが決定した手】" in res_dl.moves_by_index[2].summary
    assert "でアイコ" in res_dl.headline

    # パターン C: Win -> Draw（引き分け終局で、勝ちを逃してアイコが決定）
    draw_hist = [
        (g_loss.history[0][0], -1, g_loss.history[0][2]),
        (
            g_loss.history[1][0],
            1,
            [[1 if (r + c) % 2 == 0 else -1 for c in range(8)] for r in range(8)],  # 32 vs 32 引分
        ),
    ]
    with patch("analysis.game_analyzer.BitboardTeacherAgent") as MockBB, patch(
        "analysis.game_analyzer._evaluate_after_move"
    ) as mock_after:
        inst = MockBB.return_value
        inst._tt = {}
        inst.play_with_score.side_effect = [
            ((3, 2), 60000.0),  # 黒（idx=0）は +6石勝ちを逃して 0石（アイコ）
            ((2, 4), 0.0),      # 白（idx=1）
        ]
        mock_after.side_effect = [
            (0.0, (2, 2), True),
            (0.0, None, True),
        ]
        res_wd = analyze_game(draw_hist, endgame_empties=64, max_mistakes=3)

    assert res_wd.loser == 0
    assert res_wd.missed_win_move_index == 0
    assert res_wd.draw_sealed_move_index == 0
    assert res_wd.loss_sealed_move_index is None
    assert "【勝ち逃し・アイコ確定】" in res_wd.moves_by_index[0].summary
    assert "勝ちを逃し、アイコが決定しました" in res_wd.headline

    # priority_indices が 2 件あるときに max_mistakes=1 で上限打ち切りされること
    with patch("analysis.game_analyzer.BitboardTeacherAgent") as MockBB, patch(
        "analysis.game_analyzer._evaluate_after_move"
    ) as mock_after:
        inst = MockBB.return_value
        inst._tt = {}
        inst.play_with_score.side_effect = [((3, 2), 40000.0), ((4, 2), 0.0)]
        mock_after.side_effect = [(0.0, (2, 2), True), (-60000.0, (2, 4), True)]
        res_cap = analyze_game(loss_hist, endgame_empties=64, max_mistakes=1)
    assert len(res_cap.key_mistakes) == 1
    assert res_cap.key_mistakes[0].move_index == 2


def test_endgame_12_empties_exact_solve_default() -> None:
    """既定設定（空き 12 マス以下・安全上限 3 秒/手）で終盤局面が完全読み切りされる。"""
    g = _play_game_with_agents(RandomAgent(), GainAgent(), seed=42)
    res = analyze_game(g.history)

    twelve_or_less = [
        ma
        for ma in res.moves_by_index.values()
        if sum(r.count(0) for r in ma.board_before) <= 12
    ]
    assert len(twelve_or_less) >= 1
    oracle = BitboardTeacherAgent(time_limit_ms=3000, endgame_empties=14)
    for ma in twelve_or_less:
        assert ma.is_exact is True
        assert ma.best_disc_diff is not None and ma.played_disc_diff is not None
        actual_best = _playout_from(ma.board_before, ma.turn, ma.best_move, oracle)
        assert actual_best == ma.best_disc_diff

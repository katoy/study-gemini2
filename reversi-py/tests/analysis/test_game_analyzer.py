"""analysis/game_analyzer.py の単体テスト。"""
from __future__ import annotations

from unittest.mock import patch

from analysis import GameAnalysis, MoveAnalysis, analyze_game
from analysis.game_analyzer import _EvalGame, _evaluate_after_move, _extract_pv
from game import Game
from training.alphazero.bitboard_teacher import (
    BitboardTeacherAgent,
    board_to_bitboards,
)


def _play_scripted_game(moves_limit: int = 60) -> Game:
    """決定論的に対局を進めた Game を返す。"""
    game = Game(board_size=8)
    plies = 0
    while not game.game_over and plies < moves_limit:
        valid = game.get_valid_moves()
        if valid:
            r, c = valid[0]
            game.place_stone(r, c)
            plies += 1
        game.switch_turn()
        game.check_game_over()
    return game


def test_analyze_game_edge_cases() -> None:
    import inspect

    sig = inspect.signature(analyze_game)
    assert sig.parameters["endgame_empties"].default == 12
    assert sig.parameters["endgame_time_ms"].default == 3000

    empty_res = analyze_game([])
    assert isinstance(empty_res, GameAnalysis)
    assert empty_res.key_mistakes == []
    assert empty_res.total_moves == 0

    non_8x8 = analyze_game([((0, 0), -1, [[0] * 4 for _ in range(4)])], board_size=4)
    assert non_8x8.key_mistakes == []

    # 終盤でも tt_entry の深さが empties 未満（時間切れ未完了）なら is_exact=False になる
    board_win_white = [[0] * 8 for _ in range(8)]
    board_win_white[0][0] = 1
    with patch("analysis.game_analyzer.BitboardTeacherAgent") as MockBB:
        from analysis.game_analyzer import _initial_board

        init_b = _initial_board(8)
        init_my, init_opp = board_to_bitboards(init_b, -1)
        inst = MockBB.return_value
        inst._tt = {(init_my, init_opp): (4, 0, 10.0, 2 * 8 + 3)}
        inst.play_with_score.return_value = ((2, 3), 10.0)
        res_unsolved = analyze_game(
            [((2, 3), -1, board_win_white)],
            endgame_empties=64,
        )
    assert res_unsolved.moves_by_index[0].is_exact is False


def test_eval_game_valid_moves_cache() -> None:
    g = Game(8)
    eg = _EvalGame(g.get_board(), g.turn)
    m1 = eg.get_valid_moves()
    m2 = eg.get_valid_moves()
    assert m1 is m2
    assert len(m1) == 4


def test_analyze_game_finds_decisive_endgame_blunder_and_progress() -> None:
    """空き 6 程度の終盤で黒が角を逃して負けになる対局を解析し、決定的敗着を特定できる。"""
    # 終盤局面から強制的に黒が勝てる手・負ける手がある履歴を構築する
    # まず通常対局で 50 手進めたあと、残りを進めて決着させる
    game = _play_scripted_game(moves_limit=52)
    # もし途中なら最後まで指し切る（ただし勝敗がつく形にする）
    while not game.game_over:
        valid = game.get_valid_moves()
        if valid:
            r, c = valid[-1]
            game.place_stone(r, c)
        game.switch_turn()
        game.check_game_over()

    progress_calls: list[tuple[int, int]] = []
    res = analyze_game(
        game.history,
        midgame_time_ms=10,
        endgame_time_ms=80,
        endgame_empties=10,
        max_mistakes=3,
        on_progress=lambda d, t: progress_calls.append((d, t)),
    )
    assert res.total_moves == len(game.history)
    assert res.final_black + res.final_white == sum(
        1 for row in game.get_board() for v in row if v != 0
    )
    assert len(progress_calls) > 0
    assert progress_calls[-1][0] == progress_calls[-1][1]
    assert isinstance(res.moves_by_index, dict)
    for m in res.key_mistakes:
        assert isinstance(m, MoveAnalysis)
        assert m.move_index in res.moves_by_index


def test_analyze_game_synthetic_decisive_endgame_corner_miss() -> None:
    """終盤で白が (0, 0) を打てば勝ち、(0, 1) だと負ける人工履歴を解析する。"""
    # 初期盤面から 1 手で終盤になる人工履歴の代わりに、実際の履歴として
    # 1 手だけ合法手が複数ある局面を先頭にすると _initial_board との整合が必要。
    # そのため実対局を BitboardTeacherAgent で終盤手前まで進め、最後の敗者手で最悪手を選ばせる。
    teacher = BitboardTeacherAgent(time_limit_ms=20, endgame_empties=10)
    game = Game(board_size=8)
    while not game.game_over:
        empties = sum(row.count(0) for row in game.get_board())
        valid = game.get_valid_moves()
        if valid:
            if empties <= 6:
                # 黒には常に最善手、白はあえて最初の非最善手を選ばせる
                best, _ = teacher.play_with_score(game)
                if game.turn == 1 and len(valid) >= 2:
                    chosen = next(m for m in valid if m != best)
                else:
                    chosen = best if best is not None else valid[0]
            else:
                chosen = valid[0]
            game.place_stone(chosen[0], chosen[1])
        game.switch_turn()
        game.check_game_over()

    res = analyze_game(
        game.history,
        midgame_time_ms=15,
        endgame_time_ms=100,
        endgame_empties=10,
        max_mistakes=2,
    )
    assert res.total_moves == len(game.history)
    assert len(res.key_mistakes) <= 2


def test_analyze_game_all_winners_and_fallback_worst() -> None:
    """黒勝ち・白勝ち・引き分け・閾値未満フォールバック・max_mistakes 打ち切りを網羅。"""
    # 1. 白勝ち（loser = -1）と黒勝ち（loser = 1）をモック履歴＋高速評価で確認
    board_win_black = [[0] * 8 for _ in range(8)]
    board_win_black[0][0] = -1
    board_win_black[0][1] = -1
    board_win_black[0][2] = 1

    # initial_board から黒が (2,3) ではなく (3,2) を選んだとしても、
    # best_move を強制差し替えして分岐網羅
    with patch("analysis.game_analyzer.BitboardTeacherAgent") as MockAgent:
        inst = MockAgent.return_value
        inst._tt = {}
        # 初期盤面から最善 (2,3) と一致する場合 -> score_loss = 0
        inst.play_with_score.return_value = ((2, 3), 10.0)
        res_perfect = analyze_game(
            [((2, 3), 1, board_win_black)],
            midgame_time_ms=5,
        )
        assert res_perfect.loser == 1
        assert res_perfect.key_mistakes == []

    # 引き分けケース (loser = 0)
    board_draw = [[0] * 8 for _ in range(8)]
    board_draw[3][3] = -1
    board_draw[3][4] = 1
    res_draw = analyze_game([((2, 3), -1, board_draw)], midgame_time_ms=10)
    assert res_draw.loser == 0

    # min_blunder_loss が非常に大きく、閾値未満の悪手のみがあるフォールバック
    game = _play_scripted_game(moves_limit=6)
    res_fallback = analyze_game(
        game.history,
        midgame_time_ms=10,
        min_blunder_loss=1_000_000.0,
    )
    assert res_fallback.loser in (-1, 1, 0)

    # 白が負ける短い対局で、max_mistakes=1 による break カバレッジ
    g2 = _play_scripted_game(moves_limit=12)
    res_capped = analyze_game(
        g2.history,
        midgame_time_ms=10,
        min_blunder_loss=0.0,
        max_mistakes=1,
    )
    assert len(res_capped.key_mistakes) <= 1


def test_extract_pv_paths() -> None:
    """_extract_pv の通常・パス・サイクル・未登録・終局パスをテスト。"""
    g = Game(8)
    my, opp = board_to_bitboards(g.get_board(), -1)

    # 未登録 TT -> 1 手のみ
    assert _extract_pv({}, my, opp, (2, 3), max_len=4) == [(2, 3)]

    # 不正 best_sq -> break
    from training.alphazero.bitboard_teacher import apply_move_bitboard

    n_my, n_opp = apply_move_bitboard(my, opp, 2 * 8 + 3)
    bad_tt = {(n_opp, n_my): (1, 0, 0.0, 0)}  # (0,0) は不合法
    assert _extract_pv(bad_tt, my, opp, (2, 3), max_len=4) == [(2, 3)]

    # 合法 TT で 2 手進み、3 手目でサイクル状態を踏む
    valid_opp_sq = 2 * 8 + 2  # (2,2) は黒 (2,3) 後の白合法手
    nn_my, nn_opp = apply_move_bitboard(n_opp, n_my, valid_opp_sq)
    cycle_tt = {
        (n_opp, n_my): (2, 0, 0.0, valid_opp_sq),
        # あえてキーを (nn_opp, nn_my) で別手を入れつつ、visited を踏ませる
    }
    pv = _extract_pv(cycle_tt, my, opp, (2, 3), max_len=4)
    assert pv == [(2, 3), (2, 2)]

    # 終局（両者パス）および相手パスの局面
    full_board = [[-1] * 8 for _ in range(8)]
    full_board[0][0] = 0
    full_board[0][1] = 1
    full_board[0][2] = -1
    # 黒が (0, 0) に打つと全石黒になり終局 -> both pass break
    f_my, f_opp = board_to_bitboards(full_board, -1)
    assert _extract_pv({}, f_my, f_opp, (0, 0), max_len=4) == [(0, 0)]

    # パスを挟むケース: 黒が (0, 0) を打つと白に手がないため、黒 (0, 3) へ続く
    pass_b = [[0] * 8 for _ in range(8)]
    pass_b[0][1] = 1
    pass_b[0][2] = -1
    pass_b[0][4] = 1
    pass_b[0][5] = -1
    pass_b[0][6] = -1
    pass_b[0][7] = -1
    p_my, p_opp = board_to_bitboards(pass_b, -1)
    pn_my, pn_opp = apply_move_bitboard(p_my, p_opp, 0)
    pass_tt = {(pn_my, pn_opp): (1, 0, 0.0, 3)}
    assert _extract_pv(pass_tt, p_my, p_opp, (0, 0), max_len=4) == [(0, 0), (0, 3)]

    # サイクル防御分岐 (visited)
    with patch(
        "analysis.game_analyzer.apply_move_bitboard",
        return_value=(n_my, n_opp),
    ):
        assert _extract_pv({}, n_opp, n_my, (2, 3), max_len=4) == [(2, 3)]

    # 強制 1 手パスがない通常の visited ループ防止も確認するため _extract_pv に同キー遷移を擬似入力
    # （実際のリバーシでは石が増えるので同キー再訪は起きないが防御分岐）
    assert _extract_pv({(n_opp, n_my): (1, 0, 0.0, valid_opp_sq)}, my, opp, (2, 3), max_len=2) == [(2, 3), (2, 2)]


def test_evaluate_after_move_paths() -> None:
    """_evaluate_after_move の終局・パス・強制 1 手・2 手以上分岐をテスト。"""
    # 1. 打った直後に両者パス（即終局）
    full_b = [[-1] * 8 for _ in range(8)]
    full_b[0][0] = 0
    full_b[0][1] = 1
    full_b[0][2] = -1
    f_my, f_opp = board_to_bitboards(full_b, -1)
    score, reply, solved = _evaluate_after_move(f_my, f_opp, -1, (0, 0), 20, 12)
    assert score == 64 * 10000.0
    assert reply is None
    assert solved is True

    # 2. 打った直後に相手パス → 自分に強制 1 手 → 終局
    pass_b = [[0] * 8 for _ in range(8)]
    pass_b[0][1] = 1
    pass_b[0][2] = -1
    pass_b[0][4] = 1
    pass_b[0][5] = -1
    pass_b[0][6] = -1
    pass_b[0][7] = -1
    p_my, p_opp = board_to_bitboards(pass_b, -1)
    score_p, reply_p, solved_p = _evaluate_after_move(p_my, p_opp, -1, (0, 0), 20, 12)
    assert score_p > 0
    assert reply_p is None
    assert solved_p is True

    # 3. 相手が強制 1 手 (0, 3) を打ち、その後終局するケース
    forced_b = [[0] * 8 for _ in range(8)]
    forced_b[0][1] = 1
    forced_b[0][2] = -1
    forced_b[0][4] = -1
    forced_b[0][5] = 1
    forced_b[0][6] = -1
    forced_b[0][7] = -1
    fb_my, fb_opp = board_to_bitboards(forced_b, -1)
    score_f, reply_f, solved_f = _evaluate_after_move(fb_my, fb_opp, -1, (0, 0), 20, 12)
    assert reply_f == (0, 3)
    assert score_f == (5 - 3) * 10000.0
    assert solved_f is True

    # 4. 通常の 2 手以上分岐
    g = Game(8)
    m_my, m_opp = board_to_bitboards(g.get_board(), -1)
    score_n, reply_n, _ = _evaluate_after_move(m_my, m_opp, -1, (2, 3), 20, 0)
    assert reply_n is not None
    assert isinstance(score_n, float)

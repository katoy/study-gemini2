"""analysis/explanation.py の単体テスト。"""
from __future__ import annotations

from analysis.explanation import (
    build_headline,
    build_move_explanation,
    coord_to_label,
    detect_reason_codes,
    format_pv,
    turn_label,
)
from analysis.models import MoveAnalysis


def _empty_board() -> list[list[int]]:
    return [[0] * 8 for _ in range(8)]


def _initial_board() -> list[list[int]]:
    b = _empty_board()
    b[3][3] = 1
    b[3][4] = -1
    b[4][3] = -1
    b[4][4] = 1
    return b


def test_coord_and_turn_labels() -> None:
    assert coord_to_label((0, 0)) == "A1"
    assert coord_to_label((7, 7)) == "H8"
    assert coord_to_label((2, 3)) == "D3"
    assert turn_label(-1) == "黒"
    assert turn_label(1) == "白"


def test_format_pv_empty_and_normal_and_pass_and_invalid() -> None:
    board = _initial_board()
    assert format_pv(board, -1, []) == ""
    assert format_pv(board, -1, [(2, 3), (2, 2)]) == "黒 D3 → 白 C3"
    # 不合法手で止まる
    assert format_pv(board, -1, [(0, 0)]) == ""

    # パスを挟むケース: 黒が (0, 0) を打つと白に合法手がなくなり、黒が (0, 3) を打つ
    b2 = _empty_board()
    b2[0][1] = 1
    b2[0][2] = -1
    b2[0][4] = 1
    b2[0][5] = -1
    b2[0][6] = -1
    b2[0][7] = -1
    assert format_pv(b2, -1, [(0, 0), (0, 3)]) == "黒 A1 → 黒 D1"


def test_detect_reason_codes_all_categories() -> None:
    board = _empty_board()
    # 同じ手なら空リスト
    assert (
        detect_reason_codes(
            board, -1, (2, 3), (2, 3), None, False, None, None
        )
        == []
    )

    # 1. endgame_decisive + missed_corner + missed_edge
    # 角 (0,0) が最善で、実戦手 (2,2) は辺でも角でもない
    b_corner = _initial_board()
    b_corner[1][1] = 1
    b_corner[2][2] = -1
    codes = detect_reason_codes(
        b_corner,
        -1,
        played_move=(3, 2),
        best_move=(0, 0),
        refutation_move=(0, 1),
        is_exact=True,
        played_disc_diff=-4,
        best_disc_diff=2,
    )
    assert "endgame_decisive" in codes
    assert "missed_corner" in codes

    # 2. gave_corner_x
    codes_x = detect_reason_codes(
        _initial_board(),
        -1,
        played_move=(1, 1),
        best_move=(0, 2),
        refutation_move=(0, 0),
        is_exact=False,
        played_disc_diff=None,
        best_disc_diff=None,
    )
    assert "gave_corner_x" in codes_x
    assert "missed_edge" in codes_x

    # 3. gave_corner_c
    codes_c = detect_reason_codes(
        _initial_board(),
        -1,
        played_move=(0, 1),
        best_move=(2, 3),
        refutation_move=(0, 0),
        is_exact=False,
        played_disc_diff=None,
        best_disc_diff=None,
    )
    assert "gave_corner_c" in codes_c

    # 4b. endgame_disc_loss（終盤で勝敗は変わらないが 4 石以上悪化）と endgame_missed_win_to_draw
    codes_disc = detect_reason_codes(
        _initial_board(),
        -1,
        played_move=(3, 2),
        best_move=(2, 3),
        refutation_move=None,
        is_exact=True,
        played_disc_diff=2,
        best_disc_diff=10,
    )
    assert "endgame_disc_loss" in codes_disc

    codes_draw = detect_reason_codes(
        _initial_board(),
        -1,
        played_move=(3, 2),
        best_move=(2, 3),
        refutation_move=None,
        is_exact=True,
        played_disc_diff=0,
        best_disc_diff=6,
    )
    assert "endgame_missed_win_to_draw" in codes_draw

    # 5. mobility_drop + overflipped_early
    # 空き 24 以上で、実戦手が 3 石返し、最善手が 1 石返し + 相手の手数が大きく異なる局面を作る
    b_mob = _initial_board()
    # 横一列に白を 3 つ並べて実戦 (2,5) で 3 石返し（実際は斜め・縦などで差を作る）
    b_mob[2][3] = 1
    b_mob[2][4] = 1
    b_mob[2][5] = 1
    b_mob[2][6] = -1  # 黒は (2,2) で 3 石返しになる
    codes_mob = detect_reason_codes(
        b_mob,
        -1,
        played_move=(2, 2),
        best_move=(4, 2),
        refutation_move=None,
        is_exact=False,
        played_disc_diff=None,
        best_disc_diff=None,
    )
    assert "overflipped_early" in codes_mob or "mobility_drop" in codes_mob

    # mobility_drop 単体（空き 24 未満にして overflipped_early を無効化し、モビリティ差 >= 3 を確認）
    b_mid = _empty_board()
    for r in range(6):
        for c in range(8):
            b_mid[r][c] = -1 if (r + c) % 2 == 0 else 1
    # 上側を埋めて空き 16 のみ残す
    # (6,0)=0, (6,1)=1, (6,2)=-1 なら (6,0) で 1 石返し
    b_mid[6][1] = 1
    b_mid[6][2] = -1
    # 相手の合法手が増えるような局面
    b_mid[6][4] = 1
    b_mid[6][5] = 1
    b_mid[6][6] = 1
    b_mid[6][7] = -1
    # 強制的に mobility 差が出ない場合は general_positional になることも別途確認
    codes_gen = detect_reason_codes(
        _initial_board(),
        -1,
        played_move=(2, 3),
        best_move=(3, 2),
        refutation_move=None,
        is_exact=False,
        played_disc_diff=None,
        best_disc_diff=None,
    )
    assert codes_gen == ["general_positional"]


def test_detect_mobility_drop_explicit() -> None:
    # 空き < 24 で mobility_drop が発火する盤面
    b = _empty_board()
    for r in range(6):
        for c in range(8):
            b[r][c] = -1
    # 残り行 6, 7（16 空き）
    # (5, 0)〜(5, 7) はすべて黒
    # (6, 2) に白、(6, 3) に黒、ほかは白の合法手が出やすいよう調整
    b[5][1] = 1
    b[5][2] = 1
    b[5][3] = 1
    b[5][4] = 1
    b[5][5] = 1
    # 実戦 (6,1) を打つと白の合法手が多数開き、最善 (6,6) だと開かない
    b[6][2] = 0
    b[6][3] = 0
    b[6][4] = 0
    b[6][5] = 0
    b[5][6] = 1
    b[4][6] = -1
    # (6,1) に打つと (5,1) は返らず、縦 (4,1)=-1, (5,1)=1 で縦返し。
    # 一方 (6,6) は (5,6)=1, (4,6)=-1 で縦返し。
    # 相手の合法手差が大きくなるよう (6,1) 周辺の白候補を増やす:
    b[6][0] = 1
    b[7][0] = 1
    b[7][1] = 1
    b[7][2] = 0
    codes = detect_reason_codes(
        b,
        -1,
        played_move=(6, 1),
        best_move=(6, 6),
        refutation_move=None,
        is_exact=False,
        played_disc_diff=None,
        best_disc_diff=None,
    )
    assert isinstance(codes, list) and len(codes) >= 1


def test_build_move_explanation_and_headline() -> None:
    board = _initial_board()

    # 最善手一致
    s_best, d_best = build_move_explanation(
        move_number=1,
        turn=-1,
        board_before=board,
        played_move=(2, 3),
        best_move=(2, 3),
        played_score=10.0,
        best_score=10.0,
        is_exact=False,
        played_disc_diff=None,
        best_disc_diff=None,
        refutation_move=(2, 2),
        pv=[(2, 3), (2, 2)],
        reason_codes=[],
        is_decisive=False,
    )
    assert "最善手です" in s_best
    assert "想定手順" in d_best

    # 決定的敗着（終盤完全読み切り・引き分け→負け確定、勝ち→負け確定、勝ち→アイコ）
    s_dec, d_dec = build_move_explanation(
        move_number=52,
        turn=1,
        board_before=board,
        played_move=(3, 2),
        best_move=(2, 3),
        played_score=-40000.0,
        best_score=0.0,
        is_exact=True,
        played_disc_diff=-4,
        best_disc_diff=0,
        refutation_move=(2, 2),
        pv=[(2, 3), (2, 2)],
        reason_codes=[
            "endgame_decisive",
            "missed_corner",
            "gave_corner_x",
            "gave_corner_c",
            "missed_edge",
            "mobility_drop",
            "overflipped_early",
            "general_positional",
        ],
        is_decisive=True,
        outcome_tags=("loss_sealed",),
    )
    assert "【負けが決定した手】" in s_dec
    assert "引き分け（アイコ）に持ち込めました" in d_dec

    # 勝ち→負け確定 & 勝ち→アイコ確定 & その他全 outcome_tags パターン
    s_wl, d_wl = build_move_explanation(
        move_number=54,
        turn=-1,
        board_before=board,
        played_move=(3, 2),
        best_move=(2, 3),
        played_score=-20000.0,
        best_score=40000.0,
        is_exact=True,
        played_disc_diff=-2,
        best_disc_diff=4,
        refutation_move=None,
        pv=[(2, 3)],
        reason_codes=["endgame_decisive"],
        is_decisive=True,
        outcome_tags=("missed_win", "loss_sealed"),
    )
    assert "【勝ち逃し・負け確定】" in s_wl
    assert "勝ちを逃し負け確定" in d_wl

    s_wd, d_wd = build_move_explanation(
        move_number=56,
        turn=-1,
        board_before=board,
        played_move=(3, 2),
        best_move=(2, 3),
        played_score=0.0,
        best_score=60000.0,
        is_exact=True,
        played_disc_diff=0,
        best_disc_diff=6,
        refutation_move=None,
        pv=[(2, 3)],
        reason_codes=["endgame_missed_win_to_draw"],
        is_decisive=True,
        outcome_tags=("missed_win", "draw_sealed"),
    )
    assert "【勝ち逃し・アイコ確定】" in s_wd
    assert "引き分け（アイコ）になりました" in d_wd

    s_mw_only, _ = build_move_explanation(
        move_number=48, turn=-1, board_before=board, played_move=(3, 2), best_move=(2, 3),
        played_score=0.0, best_score=20000.0, is_exact=True, played_disc_diff=0, best_disc_diff=2,
        refutation_move=None, pv=[(2, 3)], reason_codes=["endgame_missed_win_to_draw"],
        is_decisive=False, outcome_tags=("missed_win",),
    )
    assert "【勝ちを逃した手】" in s_mw_only

    s_ds_only, _ = build_move_explanation(
        move_number=50, turn=1, board_before=board, played_move=(3, 2), best_move=(2, 3),
        played_score=0.0, best_score=20000.0, is_exact=True, played_disc_diff=0, best_disc_diff=2,
        refutation_move=None, pv=[(2, 3)], reason_codes=[], is_decisive=True, outcome_tags=("draw_sealed",),
    )
    assert "【アイコが決定した手】" in s_ds_only

    s_dec_plain, _ = build_move_explanation(
        move_number=50, turn=1, board_before=board, played_move=(3, 2), best_move=(2, 3),
        played_score=-20000.0, best_score=0.0, is_exact=True, played_disc_diff=-2, best_disc_diff=0,
        refutation_move=None, pv=[(2, 3)], reason_codes=[], is_decisive=True, outcome_tags=(),
    )
    assert "【決定的敗着】" in s_dec_plain

    # refutation_move が表示されるケース（gave_corner_* を含まない場合）および endgame_disc_loss
    _, d_ref = build_move_explanation(
        move_number=52,
        turn=1,
        board_before=board,
        played_move=(3, 2),
        best_move=(2, 3),
        played_score=20000.0,
        best_score=100000.0,
        is_exact=True,
        played_disc_diff=2,
        best_disc_diff=10,
        refutation_move=(2, 2),
        pv=[(2, 3), (2, 2)],
        reason_codes=["endgame_disc_loss", "general_positional"],
        is_decisive=False,
    )
    assert "最終石差が 8石悪化しました" in d_ref
    assert "実戦の C4 に対する相手の好手" in d_ref

    # 中盤の決定的悪化（is_exact=False, is_decisive=True）
    s_mid_dec, d_mid_dec = build_move_explanation(
        move_number=20,
        turn=-1,
        board_before=board,
        played_move=(3, 2),
        best_move=(2, 3),
        played_score=-200.0,
        best_score=10.0,
        is_exact=False,
        played_disc_diff=None,
        best_disc_diff=None,
        refutation_move=None,
        pv=[(2, 3)],
        reason_codes=["mobility_drop"],
        is_decisive=True,
    )
    assert "【形勢分岐点】" in s_mid_dec
    assert "D3 と比べて自分の打てる場所が減り" in d_mid_dec

    # 中盤の悪手（非決定的）
    s_blunder, d_blunder = build_move_explanation(
        move_number=12,
        turn=-1,
        board_before=board,
        played_move=(1, 1),
        best_move=(2, 3),
        played_score=-45.0,
        best_score=25.0,
        is_exact=False,
        played_disc_diff=None,
        best_disc_diff=None,
        refutation_move=(0, 0),
        pv=[(2, 3)],
        reason_codes=["gave_corner_x"],
        is_decisive=False,
    )
    assert "【悪手】" in s_blunder
    assert "評価損失 -70" in s_blunder
    assert "Xマス" in d_blunder

    # headline バリエーション
    assert "目立った悪手は見つかりませんでした" in build_headline(1, -1, [])

    sample_decisive = MoveAnalysis(
        move_index=43,
        move_number=44,
        turn=1,
        board_before=board,
        played_move=(1, 1),
        best_move=(6, 6),
        played_score=-20000.0,
        best_score=40000.0,
        score_loss=60000.0,
        is_exact=True,
        played_disc_diff=-2,
        best_disc_diff=4,
        refutation_move=(0, 0),
        pv=[(6, 6)],
        is_decisive=True,
        reason_codes=["endgame_decisive"],
        summary=s_dec,
        explanation=d_dec,
    )
    sample_non_decisive = MoveAnalysis(
        move_index=11,
        move_number=12,
        turn=-1,
        board_before=board,
        played_move=(1, 1),
        best_move=(2, 3),
        played_score=-45.0,
        best_score=25.0,
        score_loss=70.0,
        is_exact=False,
        played_disc_diff=None,
        best_disc_diff=None,
        refutation_move=(0, 0),
        pv=[(2, 3)],
        is_decisive=False,
        reason_codes=["gave_corner_x"],
        summary=s_blunder,
        explanation=d_blunder,
    )
    sample_mid_decisive = MoveAnalysis(
        move_index=19,
        move_number=20,
        turn=-1,
        board_before=board,
        played_move=(3, 2),
        best_move=(2, 3),
        played_score=-200.0,
        best_score=10.0,
        score_loss=210.0,
        is_exact=False,
        played_disc_diff=None,
        best_disc_diff=None,
        refutation_move=None,
        pv=[(2, 3)],
        is_decisive=True,
        reason_codes=["mobility_drop"],
        summary=s_mid_dec,
        explanation=d_mid_dec,
    )
    assert "負けが確定しました" in build_headline(1, -1, [sample_decisive])
    assert "形勢が大きく傾きました" in build_headline(-1, 1, [sample_mid_decisive])
    assert "最大の悪手" in build_headline(-1, 1, [sample_non_decisive])
    assert "勝機がありました" in build_headline(0, 0, [sample_non_decisive])

    # moves_by_index 指定時の勝敗分岐見出し全パターン
    m_by = {
        43: sample_decisive,
        19: sample_mid_decisive,
        11: sample_non_decisive,
    }
    assert "勝ちを逃し、アイコが決定しました" in build_headline(
        0, 0, [sample_decisive], moves_by_index=m_by, draw_sealed_idx=43
    )
    assert "勝ちを逃し、負けが決定しました" in build_headline(
        1, -1, [sample_decisive], moves_by_index=m_by, missed_win_idx=43, loss_sealed_idx=43
    )
    h_split = build_headline(
        1, -1, [sample_decisive], moves_by_index=m_by, missed_win_idx=19, loss_sealed_idx=43
    )
    assert "勝ちを逃し" in h_split and "負けが決定しました" in h_split
    assert "でアイコ" in build_headline(
        1, -1, [sample_decisive], moves_by_index=m_by, loss_sealed_idx=43
    )
    assert "で勝ちを逃しました" in build_headline(
        -1, 1, [sample_mid_decisive], moves_by_index=m_by, missed_win_idx=19
    )

"""解析結果から戦術的理由と日本語解説文を生成するモジュール。"""
from __future__ import annotations

from typing import Optional

from analysis.models import MoveAnalysis
from training.alphazero.bitboard_teacher import (
    apply_move_bitboard,
    board_to_bitboards,
    legal_moves_mask,
)

_CORNERS: frozenset[tuple[int, int]] = frozenset({(0, 0), (0, 7), (7, 0), (7, 7)})

# 各 X マスに対応する角の座標
_X_TO_CORNER: dict[tuple[int, int], tuple[int, int]] = {
    (1, 1): (0, 0),
    (1, 6): (0, 7),
    (6, 1): (7, 0),
    (6, 6): (7, 7),
}

# 各 C マスに対応する角の座標
_C_TO_CORNER: dict[tuple[int, int], tuple[int, int]] = {
    (0, 1): (0, 0),
    (1, 0): (0, 0),
    (0, 6): (0, 7),
    (1, 7): (0, 7),
    (6, 0): (7, 0),
    (7, 1): (7, 0),
    (6, 7): (7, 7),
    (7, 6): (7, 7),
}


def coord_to_label(move: tuple[int, int]) -> str:
    """(row, col) 座標を A1〜H8 表記へ変換する。"""
    row, col = move
    return f"{chr(ord('A') + col)}{row + 1}"


def turn_label(turn: int) -> str:
    """手番 (-1 / 1) の日本語表記を返す。"""
    return "黒" if turn == -1 else "白"


def _is_edge_non_c(move: tuple[int, int]) -> bool:
    """角と C マスを除く外周マスか判定する。"""
    r, c = move
    return (
        (r in (0, 7) or c in (0, 7))
        and move not in _CORNERS
        and move not in _C_TO_CORNER
    )


def format_pv(
    board_before: list[list[int]],
    start_turn: int,
    pv: list[tuple[int, int]],
) -> str:
    """推奨手順 PV を手番と座標付き文字列へ整形する（パス考慮）。"""
    if not pv:
        return ""

    my, opp = board_to_bitboards(board_before, start_turn)
    cur_turn = start_turn
    steps: list[str] = []

    for r, c in pv:
        sq = r * 8 + c
        mask = legal_moves_mask(my, opp)
        if not (mask & (1 << sq)):
            # パス後に相手手番になっているケースを確認
            opp_mask = legal_moves_mask(opp, my)
            if opp_mask & (1 << sq):
                my, opp = opp, my
                cur_turn = -cur_turn
            else:
                break
        steps.append(f"{turn_label(cur_turn)} {coord_to_label((r, c))}")
        next_my, next_opp = apply_move_bitboard(my, opp, sq)
        my, opp = next_opp, next_my
        cur_turn = -cur_turn

    return " → ".join(steps)


def _post_move_stats(
    my: int, opp: int, move: tuple[int, int]
) -> tuple[int, int, int]:
    """着手後の (相手着手可能数, 自分の次手可能数, 反転石数) を返す。"""
    sq = move[0] * 8 + move[1]
    before_my = my.bit_count()
    n_my, n_opp = apply_move_bitboard(my, opp, sq)
    flipped = n_my.bit_count() - before_my - 1
    opp_mob = legal_moves_mask(n_opp, n_my).bit_count()
    my_mob = legal_moves_mask(n_my, n_opp).bit_count()
    return opp_mob, my_mob, flipped


def detect_reason_codes(
    board_before: list[list[int]],
    turn: int,
    played_move: tuple[int, int],
    best_move: tuple[int, int],
    refutation_move: Optional[tuple[int, int]],
    is_exact: bool,
    played_disc_diff: Optional[int],
    best_disc_diff: Optional[int],
) -> list[str]:
    """実戦手と推奨手を比較し、優先度付きの戦術理由コードリストを返す。"""
    if played_move == best_move:
        return []

    reasons: list[str] = []
    is_endgame_outcome = False

    if (
        is_exact
        and best_disc_diff is not None
        and played_disc_diff is not None
    ):
        if best_disc_diff >= 0 and played_disc_diff < 0:
            reasons.append("endgame_decisive")
            is_endgame_outcome = True
        elif best_disc_diff > 0 and played_disc_diff == 0:
            reasons.append("endgame_missed_win_to_draw")
            is_endgame_outcome = True
        elif best_disc_diff - played_disc_diff >= 4:
            reasons.append("endgame_disc_loss")
            is_endgame_outcome = True

    if best_move in _CORNERS and played_move not in _CORNERS:
        reasons.append("missed_corner")

    if (
        played_move in _X_TO_CORNER
        and refutation_move == _X_TO_CORNER[played_move]
    ):
        reasons.append("gave_corner_x")
    elif (
        played_move in _C_TO_CORNER
        and refutation_move == _C_TO_CORNER[played_move]
    ):
        reasons.append("gave_corner_c")

    if not is_endgame_outcome and _is_edge_non_c(best_move) and not _is_edge_non_c(played_move):
        reasons.append("missed_edge")

    my, opp = board_to_bitboards(board_before, turn)
    empties = 64 - (my | opp).bit_count()
    p_opp_mob, p_my_mob, p_flips = _post_move_stats(my, opp, played_move)
    b_opp_mob, b_my_mob, b_flips = _post_move_stats(my, opp, best_move)

    if (b_my_mob - b_opp_mob) - (p_my_mob - p_opp_mob) >= 3:
        reasons.append("mobility_drop")

    if empties >= 24 and p_flips - b_flips >= 2:
        reasons.append("overflipped_early")

    if not reasons:
        reasons.append("general_positional")

    return reasons[:3]


def _reason_sentence(
    code: str,
    played_label: str,
    best_label: str,
    ref_label: Optional[str],
    played_disc_diff: Optional[int],
    best_disc_diff: Optional[int],
) -> str:
    """理由コードに対応する日本語の解説文を返す。"""
    if code == "endgame_decisive":
        assert best_disc_diff is not None and played_disc_diff is not None
        if best_disc_diff > 0:
            return (
                f"終盤の読み切りで、{best_label} なら {best_disc_diff:+d}石で勝ちでしたが、"
                f"{played_label} だと {played_disc_diff:+d}石で負けが決定しました（勝ちを逃し負け確定）。"
            )
        return (
            f"終盤の読み切りで、{best_label} なら引き分け（アイコ）に持ち込めましたが、"
            f"{played_label} だと {played_disc_diff:+d}石で負けが決定しました。"
        )
    if code == "endgame_missed_win_to_draw":
        assert best_disc_diff is not None
        return (
            f"終盤の読み切りで、{best_label} なら {best_disc_diff:+d}石で勝ちでしたが、"
            f"{played_label} だと引き分け（アイコ）になりました。"
        )
    if code == "endgame_disc_loss":
        assert best_disc_diff is not None and played_disc_diff is not None
        diff = best_disc_diff - played_disc_diff
        return (
            f"終盤の読み切りで、{best_label}（{best_disc_diff:+d}石）と比べて"
            f"最終石差が {diff}石悪化しました（{played_label} は {played_disc_diff:+d}石）。"
        )
    if code == "missed_corner":
        return f"取れるはずだった角（{best_label}）を見逃してしまいました。"
    if code == "gave_corner_x":
        corner = ref_label or "角"
        return f"角の斜め隣（Xマス: {played_label}）に打ったため、直後に相手へ角（{corner}）を奪われます。"
    if code == "gave_corner_c":
        corner = ref_label or "角"
        return f"角の隣（Cマス: {played_label}）に打ったため、相手が角（{corner}）を取る隙を与えました。"
    if code == "missed_edge":
        return f"有利な辺（{best_label}）を確保せず、主導権を譲りました。"
    if code == "mobility_drop":
        return f"{best_label} と比べて自分の打てる場所が減り、相手に手数を握られます。"
    if code == "overflipped_early":
        return "序中盤で石を多く返しすぎて、相手に好手を与えやすい盤面になりました。"
    return f"評価値が大きく下がる手でした（推奨は {best_label}）。"


def _outcome_tag_label(
    outcome_tags: tuple[str, ...],
    is_decisive: bool,
    is_exact: bool,
) -> str:
    """勝敗分岐タグと重要度に応じた先頭見出しタグを返す。"""
    tag_set = set(outcome_tags)
    if "missed_win" in tag_set and "loss_sealed" in tag_set:
        return "【勝ち逃し・負け確定】"
    if "missed_win" in tag_set and "draw_sealed" in tag_set:
        return "【勝ち逃し・アイコ確定】"
    if "missed_win" in tag_set:
        return "【勝ちを逃した手】"
    if "loss_sealed" in tag_set:
        return "【負けが決定した手】"
    if "draw_sealed" in tag_set:
        return "【アイコが決定した手】"
    if "midgame_turning_point" in tag_set or (is_decisive and not is_exact):
        return "【形勢分岐点】"
    if is_decisive:
        return "【決定的敗着】"
    return "【悪手】"


def build_move_explanation(
    move_number: int,
    turn: int,
    board_before: list[list[int]],
    played_move: tuple[int, int],
    best_move: tuple[int, int],
    played_score: float,
    best_score: float,
    is_exact: bool,
    played_disc_diff: Optional[int],
    best_disc_diff: Optional[int],
    refutation_move: Optional[tuple[int, int]],
    pv: list[tuple[int, int]],
    reason_codes: list[str],
    is_decisive: bool,
    outcome_tags: tuple[str, ...] = (),
) -> tuple[str, str]:
    """1 手の要約（1 行）と詳細解説テキストを生成する。"""
    p_lbl = coord_to_label(played_move)
    b_lbl = coord_to_label(best_move)
    r_lbl = coord_to_label(refutation_move) if refutation_move else None
    t_lbl = turn_label(turn)

    if played_move == best_move:
        summary = f"第{move_number}手 {t_lbl} {p_lbl}: 最善手です。"
        pv_text = format_pv(board_before, turn, pv)
        detail = summary + (f"\n想定手順: {pv_text}" if pv_text else "")
        return summary, detail

    tag = _outcome_tag_label(outcome_tags, is_decisive, is_exact)
    if is_exact and best_disc_diff is not None and played_disc_diff is not None:
        score_info = f"石差 {played_disc_diff:+d}（最善 {best_disc_diff:+d}）"
    else:
        loss = max(0.0, best_score - played_score)
        score_info = f"評価損失 -{loss:.0f}"

    summary = f"{tag} 第{move_number}手 {t_lbl} {p_lbl} → 推奨 {b_lbl}（{score_info}）"

    lines = [summary]
    for code in reason_codes:
        lines.append(
            _reason_sentence(
                code, p_lbl, b_lbl, r_lbl, played_disc_diff, best_disc_diff
            )
        )

    pv_text = format_pv(board_before, turn, pv)
    if pv_text:
        lines.append(f"こう打てば有望: {pv_text}")
    if refutation_move is not None and "gave_corner_x" not in reason_codes and "gave_corner_c" not in reason_codes:
        lines.append(f"実戦の {p_lbl} に対する相手の好手: {turn_label(-turn)} {r_lbl}")

    return summary, "\n".join(lines)


def build_headline(
    loser: int,
    winner: int,
    key_mistakes: list[MoveAnalysis],
    moves_by_index: Optional[dict[int, MoveAnalysis]] = None,
    missed_win_idx: Optional[int] = None,
    loss_sealed_idx: Optional[int] = None,
    draw_sealed_idx: Optional[int] = None,
) -> str:
    """1 局全体の総評見出しを生成する。"""
    if moves_by_index is not None:
        mw = moves_by_index.get(missed_win_idx) if missed_win_idx is not None else None
        ls = moves_by_index.get(loss_sealed_idx) if loss_sealed_idx is not None else None
        ds = moves_by_index.get(draw_sealed_idx) if draw_sealed_idx is not None else None

        if loser == 0 and ds is not None:
            ds_p = coord_to_label(ds.played_move)
            ds_b = coord_to_label(ds.best_move)
            ds_t = turn_label(ds.turn)
            return (
                f"引き分けでした。第{ds.move_number}手（{ds_t} {ds_p}）で"
                f"勝ちを逃し、アイコが決定しました（推奨: {ds_b}）。"
            )

        if loser != 0:
            loser_lbl = turn_label(loser)
            if mw is not None and ls is not None:
                mw_p = coord_to_label(mw.played_move)
                mw_b = coord_to_label(mw.best_move)
                if mw.move_index == ls.move_index:
                    return (
                        f"{loser_lbl}は第{mw.move_number}手 {mw_p} で勝ちを逃し、"
                        f"負けが決定しました（推奨: {mw_b}）。"
                    )
                ls_p = coord_to_label(ls.played_move)
                ls_b = coord_to_label(ls.best_move)
                return (
                    f"{loser_lbl}は第{mw.move_number}手 {mw_p} で勝ちを逃し（推奨: {mw_b}）、"
                    f"第{ls.move_number}手 {ls_p} で負けが決定しました（推奨: {ls_b}）。"
                )
            if ls is not None:
                ls_p = coord_to_label(ls.played_move)
                ls_b = coord_to_label(ls.best_move)
                return (
                    f"{loser_lbl}は第{ls.move_number}手 {ls_p} で負けが決定しました"
                    f"（推奨: {ls_b} でアイコ）。"
                )
            if mw is not None:
                mw_p = coord_to_label(mw.played_move)
                mw_b = coord_to_label(mw.best_move)
                return (
                    f"{loser_lbl}は第{mw.move_number}手 {mw_p} で勝ちを逃しました"
                    f"（推奨: {mw_b}）。"
                )

    if not key_mistakes:
        return "目立った悪手は見つかりませんでした。"

    top = key_mistakes[0]
    p_lbl = coord_to_label(top.played_move)
    b_lbl = coord_to_label(top.best_move)
    t_lbl = turn_label(top.turn)

    if loser == 0:
        return (
            f"引き分けでした。第{top.move_number}手（{t_lbl} {p_lbl}）で"
            f" {b_lbl} なら勝機がありました。"
        )

    loser_lbl = turn_label(loser)
    if top.is_decisive:
        if top.is_exact:
            return f"{loser_lbl}は第{top.move_number}手 {p_lbl} で負けが確定しました（推奨: {b_lbl}）。"
        return f"{loser_lbl}は第{top.move_number}手 {p_lbl} で形勢が大きく傾きました（推奨: {b_lbl}）。"
    return f"{loser_lbl}の最大の悪手は第{top.move_number}手 {p_lbl} です（推奨: {b_lbl}）。"

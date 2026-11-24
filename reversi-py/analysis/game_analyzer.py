"""対局履歴をビットボード探索で解析し、敗着・勝機を特定するモジュール。"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Callable, Optional

from analysis.explanation import (
    build_headline,
    build_move_explanation,
    detect_reason_codes,
)
from analysis.models import GameAnalysis, MoveAnalysis
from training.alphazero.bitboard_teacher import (
    BitboardTeacherAgent,
    apply_move_bitboard,
    bitboards_to_board,
    board_to_bitboards,
    legal_moves_mask,
)


@dataclass
class _EvalBoard:
    """BitboardTeacherAgent.play_with_score へ渡す軽量盤面ラッパー。"""

    board: list[list[int]]


class _EvalGame:
    """Game クラスと同等の最小インターフェースを持つ解析用軽量ゲーム。"""

    def __init__(self, board_data: list[list[int]], turn: int) -> None:
        self.board = _EvalBoard([row[:] for row in board_data])
        self.turn = turn
        self._moves: Optional[list[tuple[int, int]]] = None

    def get_valid_moves(self) -> list[tuple[int, int]]:
        if self._moves is None:
            my, opp = board_to_bitboards(self.board.board, self.turn)
            mask = legal_moves_mask(my, opp)
            moves: list[tuple[int, int]] = []
            while mask:
                lsb = mask & -mask
                sq = lsb.bit_length() - 1
                moves.append(divmod(sq, 8))
                mask ^= lsb
            self._moves = moves
        return self._moves


def _initial_board(board_size: int = 8) -> list[list[int]]:
    """リバーシの初期盤面（8x8）を生成する。"""
    board = [[0] * board_size for _ in range(board_size)]
    mid = board_size // 2
    board[mid - 1][mid - 1] = 1
    board[mid - 1][mid] = -1
    board[mid][mid - 1] = -1
    board[mid][mid] = 1
    return board


def _extract_pv(
    tt: dict[tuple[int, int], tuple[int, int, float, int]],
    my: int,
    opp: int,
    first_move: tuple[int, int],
    max_len: int = 4,
) -> list[tuple[int, int]]:
    """トランスポジションテーブルから最善手以降の読み筋（最大 max_len 手）を復元する。"""
    pv: list[tuple[int, int]] = [first_move]
    first_sq = first_move[0] * 8 + first_move[1]
    cur_my, cur_opp = apply_move_bitboard(my, opp, first_sq)
    # 次の手番は相手
    cur_my, cur_opp = cur_opp, cur_my
    visited: set[tuple[int, int]] = {(my, opp)}

    while len(pv) < max_len:
        if (cur_my, cur_opp) in visited:
            break
        visited.add((cur_my, cur_opp))

        mask = legal_moves_mask(cur_my, cur_opp)
        if mask == 0:
            # パスして元の手番へ戻るか確認
            opp_mask = legal_moves_mask(cur_opp, cur_my)
            if opp_mask == 0:
                break
            cur_my, cur_opp = cur_opp, cur_my
            mask = opp_mask

        entry = tt.get((cur_my, cur_opp))
        if entry is None:
            break
        best_sq = entry[3]
        if best_sq < 0 or not (mask & (1 << best_sq)):
            break
        pv.append(divmod(best_sq, 8))
        n_my, n_opp = apply_move_bitboard(cur_my, cur_opp, best_sq)
        cur_my, cur_opp = n_opp, n_my

    return pv


def _evaluate_after_move(
    my: int,
    opp: int,
    turn: int,
    move: tuple[int, int],
    time_limit_ms: int,
    agent_endgame_empties: int,
) -> tuple[float, Optional[tuple[int, int]], bool]:
    """実戦手 move を適用後の局面を評価し、(手番視点スコア, 相手反撃手, 完全読み完了か) を返す。"""
    sq = move[0] * 8 + move[1]
    n_my, n_opp = apply_move_bitboard(my, opp, sq)
    cur_my, cur_opp = n_opp, n_my
    cur_turn = -turn
    first_opponent_reply: Optional[tuple[int, int]] = None
    first_reply_recorded = False

    # 終局・パス・強制 1 手（play_with_score が探索せず 0.0 を返す）を先に進める
    while True:
        mask = legal_moves_mask(cur_my, cur_opp)
        if mask == 0:
            opp_mask = legal_moves_mask(cur_opp, cur_my)
            if opp_mask == 0:
                # 終局（手番視点の石差 × 10000）
                my_stones = cur_my.bit_count() if cur_turn == turn else cur_opp.bit_count()
                opp_stones = cur_opp.bit_count() if cur_turn == turn else cur_my.bit_count()
                return float((my_stones - opp_stones) * 10000), first_opponent_reply, True
            # パス：相手手番に戻す
            cur_my, cur_opp = cur_opp, cur_my
            cur_turn = -cur_turn
            first_reply_recorded = True
            continue

        if mask.bit_count() == 1:
            only_sq = mask.bit_length() - 1
            if not first_reply_recorded and cur_turn == -turn:
                first_opponent_reply = divmod(only_sq, 8)
                first_reply_recorded = True
            next_my, next_opp = apply_move_bitboard(cur_my, cur_opp, only_sq)
            cur_my, cur_opp = next_opp, next_my
            cur_turn = -cur_turn
            continue

        break

    board_data = bitboards_to_board(cur_my, cur_opp, cur_turn)
    eval_agent = BitboardTeacherAgent(
        time_limit_ms=time_limit_ms,
        endgame_empties=agent_endgame_empties,
    )
    reply_move, raw_score = eval_agent.play_with_score(_EvalGame(board_data, cur_turn))  # type: ignore[arg-type]
    if not first_reply_recorded and cur_turn == -turn:
        first_opponent_reply = reply_move
    cur_empties = 64 - (cur_my | cur_opp).bit_count()
    tt_entry = eval_agent._tt.get((cur_my, cur_opp))
    solved = not (tt_entry is not None and tt_entry[0] < cur_empties)
    score_for_mover = raw_score if cur_turn == turn else -raw_score
    return score_for_mover, first_opponent_reply, solved


def _win_prob(score: float, is_exact: bool) -> float:
    """中盤評価値または終盤石差(×10000)を [0, 1] の期待勝率へ正規化する。"""
    scaled = (score / 10000.0) / 6.0 if is_exact else score / 180.0
    clamped = max(-50.0, min(50.0, scaled))
    return 1.0 / (1.0 + math.exp(-clamped))


def analyze_game(
    history: list[tuple[tuple[int, int], int, list[list[int]]]],
    board_size: int = 8,
    midgame_time_ms: int = 60,
    endgame_time_ms: int = 3000,
    endgame_empties: int = 12,
    max_mistakes: int = 3,
    min_blunder_loss: float = 40.0,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> GameAnalysis:
    """対局履歴から敗者の敗着・悪手と推奨手順を解析する。

    Args:
        history: Game.history と同じ [(move, turn, board_after), ...] のリスト。
        board_size: 盤面サイズ（現在は 8 のみ対応）。
        midgame_time_ms: 中盤 1 手あたりの探索時間（ミリ秒）。
        endgame_time_ms: 終盤（空き 12 マス以下）の完全読み切り安全上限（既定 3000ms = 最大 3 秒、読み切り完了時は即終了）。
        endgame_empties: 完全読み切りへ切り替える空きマス数（既定 12）。
        max_mistakes: key_mistakes に抽出する最大手数。
        min_blunder_loss: 悪手・決定的敗着とみなす最小評価損失。
        on_progress: 進捗通知コールバック (完了手数, 総対象手数)。

    Returns:
        GameAnalysis: 解析結果。
    """
    if board_size != 8 or not history:
        return GameAnalysis(
            loser=0,
            winner=0,
            final_black=0,
            final_white=0,
            total_moves=len(history),
            key_mistakes=[],
            moves_by_index={},
            headline="解析できる対局履歴がありません（8x8盤面のみ対応）。",
        )

    final_board = history[-1][2]
    final_black = sum(row.count(-1) for row in final_board)
    final_white = sum(row.count(1) for row in final_board)
    if final_black > final_white:
        winner, loser = -1, 1
    elif final_white > final_black:
        winner, loser = 1, -1
    else:
        winner, loser = 0, 0

    target_turns = {-1, 1} if loser == 0 else {loser}

    # 解析対象手（対象プレイヤーかつ合法手が 2 手以上の局面）を抽出
    candidates: list[tuple[int, tuple[int, int], int, list[list[int]]]] = []
    prev_board = _initial_board(board_size)
    for idx, (played_move, turn, board_after) in enumerate(history):
        if turn in target_turns:
            my, opp = board_to_bitboards(prev_board, turn)
            if legal_moves_mask(my, opp).bit_count() >= 2:
                candidates.append((idx, played_move, turn, [r[:] for r in prev_board]))
        prev_board = board_after

    total_targets = len(candidates)
    raw_results: list[dict] = []

    for done_idx, (move_index, played_move, turn, board_before) in enumerate(candidates, start=1):
        my, opp = board_to_bitboards(board_before, turn)
        empties = 64 - (my | opp).bit_count()
        in_endgame = empties <= endgame_empties
        time_limit = endgame_time_ms if in_endgame else midgame_time_ms
        # 比較のスケールを揃えるため、中盤領域では完全読み切り切替をオフにする
        agent_eg = endgame_empties if in_endgame else 0

        move_start = time.monotonic()
        agent = BitboardTeacherAgent(
            time_limit_ms=time_limit,
            endgame_empties=agent_eg,
        )
        best_move, best_score = agent.play_with_score(_EvalGame(board_before, turn))  # type: ignore[arg-type]
        assert best_move is not None
        best_tt = agent._tt.get((my, opp))
        best_solved = not (best_tt is not None and best_tt[0] < empties)
        pv = _extract_pv(agent._tt, my, opp, best_move, max_len=4)

        if played_move == best_move:
            played_score = best_score
            refutation_move: Optional[tuple[int, int]] = pv[1] if len(pv) >= 2 else None
            after_solved = best_solved
        else:
            elapsed_ms = int((time.monotonic() - move_start) * 1000)
            after_time_limit = (
                max(min(150, time_limit), time_limit - elapsed_ms)
                if in_endgame
                else time_limit
            )
            played_score, refutation_move, after_solved = _evaluate_after_move(
                my, opp, turn, played_move, after_time_limit, agent_eg
            )

        is_exact = in_endgame and best_solved and after_solved
        score_loss = max(0.0, best_score - played_score)
        wp_loss = max(0.0, _win_prob(best_score, is_exact) - _win_prob(played_score, is_exact))
        played_diff = round(played_score / 10000.0) if is_exact else None
        best_diff = round(best_score / 10000.0) if is_exact else None

        reason_codes = detect_reason_codes(
            board_before=board_before,
            turn=turn,
            played_move=played_move,
            best_move=best_move,
            refutation_move=refutation_move,
            is_exact=is_exact,
            played_disc_diff=played_diff,
            best_disc_diff=best_diff,
        )
        raw_results.append(
            {
                "move_index": move_index,
                "move_number": move_index + 1,
                "turn": turn,
                "board_before": board_before,
                "played_move": played_move,
                "best_move": best_move,
                "played_score": played_score,
                "best_score": best_score,
                "score_loss": score_loss,
                "wp_loss": wp_loss,
                "is_exact": is_exact,
                "played_disc_diff": played_diff,
                "best_disc_diff": best_diff,
                "refutation_move": refutation_move,
                "pv": pv,
                "reason_codes": reason_codes,
            }
        )
        if on_progress is not None:
            on_progress(done_idx, total_targets)

    # 決定的分岐手の特定:
    # 1. 終盤完全読み切り領域から「勝ち逃し」「負け決定」「アイコ決定」の最後の手を特定
    missed_win_idx: Optional[int] = None
    loss_sealed_idx: Optional[int] = None
    draw_sealed_idx: Optional[int] = None
    for item in raw_results:
        if not item["is_exact"]:
            continue
        b_diff = item["best_disc_diff"]
        p_diff = item["played_disc_diff"]
        assert b_diff is not None and p_diff is not None
        if b_diff > 0 and p_diff <= 0:
            missed_win_idx = item["move_index"]
        if loser != 0 and b_diff >= 0 and p_diff < 0:
            loss_sealed_idx = item["move_index"]
        if loser == 0 and b_diff > 0 and p_diff == 0:
            draw_sealed_idx = item["move_index"]

    # 2. 終盤に負け/アイコ決定手がなければ、中盤で互角以上から明確な劣勢へ落ちた最後の手を採用
    midgame_turning_idx: Optional[int] = None
    if loss_sealed_idx is None and draw_sealed_idx is None:
        mid_decisive_threshold = max(min_blunder_loss, 120.0)
        for item in raw_results:
            if (
                not item["is_exact"]
                and item["best_score"] >= -30.0
                and item["played_score"] <= -120.0
                and item["score_loss"] >= mid_decisive_threshold
            ):
                midgame_turning_idx = item["move_index"]

    decisive_indices = {
        idx
        for idx in (loss_sealed_idx, draw_sealed_idx, midgame_turning_idx)
        if idx is not None
    }

    moves_by_index: dict[int, MoveAnalysis] = {}
    all_analyses: list[MoveAnalysis] = []
    for item in raw_results:
        idx = item["move_index"]
        tags_list: list[str] = []
        if idx == missed_win_idx:
            tags_list.append("missed_win")
        if idx == loss_sealed_idx:
            tags_list.append("loss_sealed")
        if idx == draw_sealed_idx:
            tags_list.append("draw_sealed")
        if idx == midgame_turning_idx:
            tags_list.append("midgame_turning_point")
        outcome_tags = tuple(tags_list)
        is_decisive = idx in decisive_indices

        summary, explanation = build_move_explanation(
            move_number=item["move_number"],
            turn=item["turn"],
            board_before=item["board_before"],
            played_move=item["played_move"],
            best_move=item["best_move"],
            played_score=item["played_score"],
            best_score=item["best_score"],
            is_exact=item["is_exact"],
            played_disc_diff=item["played_disc_diff"],
            best_disc_diff=item["best_disc_diff"],
            refutation_move=item["refutation_move"],
            pv=item["pv"],
            reason_codes=item["reason_codes"],
            is_decisive=is_decisive,
            outcome_tags=outcome_tags,
        )
        ma = MoveAnalysis(
            move_index=idx,
            move_number=item["move_number"],
            turn=item["turn"],
            board_before=item["board_before"],
            played_move=item["played_move"],
            best_move=item["best_move"],
            played_score=item["played_score"],
            best_score=item["best_score"],
            score_loss=item["score_loss"],
            is_exact=item["is_exact"],
            played_disc_diff=item["played_disc_diff"],
            best_disc_diff=item["best_disc_diff"],
            refutation_move=item["refutation_move"],
            pv=item["pv"],
            is_decisive=is_decisive,
            reason_codes=item["reason_codes"],
            summary=summary,
            explanation=explanation,
            outcome_tags=outcome_tags,
        )
        moves_by_index[ma.move_index] = ma
        all_analyses.append(ma)

    # key_mistakes の構築：勝敗分岐手（負け決定/アイコ決定/勝ち逃し/中盤分岐）を優先収録し、
    # 以降は勝率損失（wp_loss）が大きい順で最大 max_mistakes 件まで追加
    key_mistakes: list[MoveAnalysis] = []
    priority_indices: list[int] = []
    for p_idx in (loss_sealed_idx, draw_sealed_idx, missed_win_idx, midgame_turning_idx):
        if p_idx is not None and p_idx not in priority_indices:
            priority_indices.append(p_idx)

    for p_idx in priority_indices:
        if len(key_mistakes) >= max_mistakes:
            break
        key_mistakes.append(moves_by_index[p_idx])

    selected_indices = {m.move_index for m in key_mistakes}
    wp_by_index = {item["move_index"]: item["wp_loss"] for item in raw_results}
    blunders = [
        m
        for m in all_analyses
        if m.move_index not in selected_indices
        and m.score_loss > 0
        and (
            (m.is_exact and wp_by_index[m.move_index] >= 0.03)
            or (
                not m.is_exact
                and (
                    min_blunder_loss == 0.0
                    or (
                        m.score_loss >= min_blunder_loss
                        and wp_by_index[m.move_index] >= 0.04
                    )
                )
            )
        )
    ]
    blunders.sort(key=lambda m: (wp_by_index[m.move_index], m.score_loss), reverse=True)
    for m in blunders:
        if len(key_mistakes) >= max_mistakes:
            break
        key_mistakes.append(m)

    if not key_mistakes and all_analyses:
        worst = max(all_analyses, key=lambda m: (wp_by_index[m.move_index], m.score_loss))
        if worst.score_loss > 0:
            key_mistakes.append(worst)

    headline = build_headline(
        loser,
        winner,
        key_mistakes,
        moves_by_index=moves_by_index,
        missed_win_idx=missed_win_idx,
        loss_sealed_idx=loss_sealed_idx,
        draw_sealed_idx=draw_sealed_idx,
    )
    return GameAnalysis(
        loser=loser,
        winner=winner,
        final_black=final_black,
        final_white=final_white,
        total_moves=len(history),
        key_mistakes=key_mistakes,
        moves_by_index=moves_by_index,
        headline=headline,
        missed_win_move_index=missed_win_idx,
        loss_sealed_move_index=loss_sealed_idx,
        draw_sealed_move_index=draw_sealed_idx,
    )

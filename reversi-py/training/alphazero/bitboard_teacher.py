"""高速 64-bit ビットボード探索を用いた Othello 教師エージェント。

Python リスト盤面コピーを排除し、ビット演算による合法手生成・着手・反転・
戦略評価（角・動的 C/X 打ち・安定辺・着手可能数・開放度・パリティ・終盤完全読み）
を行うことで、200ms 程度で MinimaxAgent(500ms) を大きく上回る強さを実現する。
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING, Optional

from agents.base_agent import Agent
from agents.negamax_agent import _NODES_PER_TIME_CHECK, _SearchTimeout

if TYPE_CHECKING:
    from game import Game

FULL: int = 0xFFFFFFFFFFFFFFFF
NOT_A_FILE: int = 0xFEFEFEFEFEFEFEFE
NOT_H_FILE: int = 0x7F7F7F7F7F7F7F7F
NOT_AB_EDGE: int = 0x7E7E7E7E7E7E7E7E
A_FILE: int = 0x0101010101010101
H_FILE: int = 0x8080808080808080
CORNERS_MASK: int = 0x8100000000000081

# 各角ごとの (角ビット, C マスビット群, X マスビット)
_CORNER_ADJ: tuple[tuple[int, int, int], ...] = (
    (1 << 0, (1 << 1) | (1 << 8), 1 << 9),
    (1 << 7, (1 << 6) | (1 << 15), 1 << 14),
    (1 << 56, (1 << 48) | (1 << 57), 1 << 49),
    (1 << 63, (1 << 55) | (1 << 62), 1 << 54),
)

_TT_EXACT = 0
_TT_LOWER = 1
_TT_UPPER = 2
_INF = float("inf")


def _build_masks() -> tuple[int, int, int, int, tuple[int, ...]]:
    """位置評価用ビットマスクと静的ムーブオーダリング重みを構築する。"""
    edges_ab = 0
    edges_cd = 0
    bad_ring = 0
    inner_4x4 = 0
    weights = [0] * 64

    base_table = (
        (100, -25, 15, 8, 8, 15, -25, 100),
        (-25, -50, -6, -4, -4, -6, -50, -25),
        (15, -6, 6, 3, 3, 6, -6, 15),
        (8, -4, 3, 2, 2, 3, -4, 8),
        (8, -4, 3, 2, 2, 3, -4, 8),
        (15, -6, 6, 3, 3, 6, -6, 15),
        (-25, -50, -6, -4, -4, -6, -50, -25),
        (100, -25, 15, 8, 8, 15, -25, 100),
    )

    for r in range(8):
        for c in range(8):
            sq = r * 8 + c
            bit = 1 << sq
            weights[sq] = base_table[r][c]
            if (r in (0, 7) and c in (2, 5)) or (c in (0, 7) and r in (2, 5)):
                edges_ab |= bit
            elif (r in (0, 7) and c in (3, 4)) or (c in (0, 7) and r in (3, 4)):
                edges_cd |= bit
            elif (r in (1, 6) and 2 <= c <= 5) or (c in (1, 6) and 2 <= r <= 5):
                bad_ring |= bit
            if 2 <= r <= 5 and 2 <= c <= 5:
                inner_4x4 |= bit

    return edges_ab, edges_cd, bad_ring, inner_4x4, tuple(weights)


_EDGES_AB, _EDGES_CD, _BAD_RING, _INNER_4X4, _SQ_ORDER_WEIGHT = _build_masks()


def _build_edge_stable_table() -> tuple[int, ...]:
    """8-bit の片側石配置から角起点の連続安定石数を返すテーブルを構築する。"""
    table = [0] * 256
    for byte in range(256):
        lsb = 0
        for i in range(8):
            if byte & (1 << i):
                lsb += 1
            else:
                break
        msb = 0
        for i in range(7, -1, -1):
            if byte & (1 << i):
                msb += 1
            else:
                break
        table[byte] = min(8, lsb + msb)
    return tuple(table)


_EDGE_STABLE_TABLE: tuple[int, ...] = _build_edge_stable_table()


def board_to_bitboards(board: list[list[int]], turn: int) -> tuple[int, int]:
    """8x8 の 2 次元盤面を手番視点の (my, opp) 64-bit 整数対へ変換する。"""
    my = 0
    opp = 0
    for r in range(8):
        row = board[r]
        base = r * 8
        for c in range(8):
            v = row[c]
            if v == turn:
                my |= 1 << (base + c)
            elif v == -turn:
                opp |= 1 << (base + c)
    return my, opp


def bitboards_to_board(my: int, opp: int, turn: int) -> list[list[int]]:
    """(my, opp) ビットボードを指定手番の 8x8 2 次元盤面へ戻す。"""
    board = [[0] * 8 for _ in range(8)]
    for sq in range(64):
        bit = 1 << sq
        r, c = divmod(sq, 8)
        if my & bit:
            board[r][c] = turn
        elif opp & bit:
            board[r][c] = -turn
    return board


def legal_moves_mask(my: int, opp: int) -> int:
    """手番 my の全合法手を表す 64-bit ビットマスクを返す。"""
    empty = ~(my | opp) & FULL
    if empty == 0:
        return 0
    m = opp & NOT_AB_EDGE
    moves = 0

    # East (+1)
    t = m & (my << 1)
    t |= m & (t << 1)
    t |= m & (t << 1)
    t |= m & (t << 1)
    t |= m & (t << 1)
    t |= m & (t << 1)
    moves |= empty & (t << 1)

    # West (-1)
    t = m & (my >> 1)
    t |= m & (t >> 1)
    t |= m & (t >> 1)
    t |= m & (t >> 1)
    t |= m & (t >> 1)
    t |= m & (t >> 1)
    moves |= empty & (t >> 1)

    # South (+8)
    t = opp & (my << 8)
    t |= opp & (t << 8)
    t |= opp & (t << 8)
    t |= opp & (t << 8)
    t |= opp & (t << 8)
    t |= opp & (t << 8)
    moves |= empty & (t << 8)

    # North (-8)
    t = opp & (my >> 8)
    t |= opp & (t >> 8)
    t |= opp & (t >> 8)
    t |= opp & (t >> 8)
    t |= opp & (t >> 8)
    t |= opp & (t >> 8)
    moves |= empty & (t >> 8)

    # South-East (+9)
    t = m & (my << 9)
    t |= m & (t << 9)
    t |= m & (t << 9)
    t |= m & (t << 9)
    t |= m & (t << 9)
    t |= m & (t << 9)
    moves |= empty & (t << 9)

    # North-West (-9)
    t = m & (my >> 9)
    t |= m & (t >> 9)
    t |= m & (t >> 9)
    t |= m & (t >> 9)
    t |= m & (t >> 9)
    t |= m & (t >> 9)
    moves |= empty & (t >> 9)

    # South-West (+7)
    t = m & (my << 7)
    t |= m & (t << 7)
    t |= m & (t << 7)
    t |= m & (t << 7)
    t |= m & (t << 7)
    t |= m & (t << 7)
    moves |= empty & (t << 7)

    # North-East (-7)
    t = m & (my >> 7)
    t |= m & (t >> 7)
    t |= m & (t >> 7)
    t |= m & (t >> 7)
    t |= m & (t >> 7)
    t |= m & (t >> 7)
    moves |= empty & (t >> 7)

    return moves


def apply_move_bitboard(my: int, opp: int, sq: int) -> tuple[int, int]:
    """マス sq (0..63) への着手を適用し、更新後の (next_my, next_opp) を返す。"""
    pos = 1 << sq
    m = opp & NOT_AB_EDGE
    flips = 0

    # East (+1)
    t = m & (pos << 1)
    if t:
        t |= m & (t << 1)
        t |= m & (t << 1)
        t |= m & (t << 1)
        t |= m & (t << 1)
        t |= m & (t << 1)
        if (t << 1) & my:
            flips |= t

    # West (-1)
    t = m & (pos >> 1)
    if t:
        t |= m & (t >> 1)
        t |= m & (t >> 1)
        t |= m & (t >> 1)
        t |= m & (t >> 1)
        t |= m & (t >> 1)
        if (t >> 1) & my:
            flips |= t

    # South (+8)
    t = opp & (pos << 8)
    if t:
        t |= opp & (t << 8)
        t |= opp & (t << 8)
        t |= opp & (t << 8)
        t |= opp & (t << 8)
        t |= opp & (t << 8)
        if (t << 8) & my:
            flips |= t

    # North (-8)
    t = opp & (pos >> 8)
    if t:
        t |= opp & (t >> 8)
        t |= opp & (t >> 8)
        t |= opp & (t >> 8)
        t |= opp & (t >> 8)
        t |= opp & (t >> 8)
        if (t >> 8) & my:
            flips |= t

    # South-East (+9)
    t = m & (pos << 9)
    if t:
        t |= m & (t << 9)
        t |= m & (t << 9)
        t |= m & (t << 9)
        t |= m & (t << 9)
        t |= m & (t << 9)
        if (t << 9) & my:
            flips |= t

    # North-West (-9)
    t = m & (pos >> 9)
    if t:
        t |= m & (t >> 9)
        t |= m & (t >> 9)
        t |= m & (t >> 9)
        t |= m & (t >> 9)
        t |= m & (t >> 9)
        if (t >> 9) & my:
            flips |= t

    # South-West (+7)
    t = m & (pos << 7)
    if t:
        t |= m & (t << 7)
        t |= m & (t << 7)
        t |= m & (t << 7)
        t |= m & (t << 7)
        t |= m & (t << 7)
        if (t << 7) & my:
            flips |= t

    # North-East (-7)
    t = m & (pos >> 7)
    if t:
        t |= m & (t >> 7)
        t |= m & (t >> 7)
        t |= m & (t >> 7)
        t |= m & (t >> 7)
        t |= m & (t >> 7)
        if (t >> 7) & my:
            flips |= t

    return my | pos | flips, opp & ~flips


def _edge_stability_score(my: int, opp: int) -> int:
    """4 辺上の角起点安定石数差（my - opp）を計算する。"""
    tbl = _EDGE_STABLE_TABLE
    top_m = my & 0xFF
    top_o = opp & 0xFF
    bot_m = (my >> 56) & 0xFF
    bot_o = (opp >> 56) & 0xFF
    left_m = (((my & A_FILE) * 0x0102040810204080) >> 56) & 0xFF
    left_o = (((opp & A_FILE) * 0x0102040810204080) >> 56) & 0xFF
    right_m = ((((my & H_FILE) >> 7) * 0x0102040810204080) >> 56) & 0xFF
    right_o = ((((opp & H_FILE) >> 7) * 0x0102040810204080) >> 56) & 0xFF

    return (
        (tbl[top_m] - tbl[top_o])
        + (tbl[bot_m] - tbl[bot_o])
        + (tbl[left_m] - tbl[left_o])
        + (tbl[right_m] - tbl[right_o])
    )


def evaluate_bitboard(my: int, opp: int) -> float:
    """ビットボード盤面を戦略的に評価する（整数ベーススコアを float で返す）。"""
    my_cnt = my.bit_count()
    opp_cnt = opp.bit_count()
    stones = my_cnt + opp_cnt
    empties = 64 - stones
    occ = my | opp

    # 1. 角
    corner_diff = (my & CORNERS_MASK).bit_count() - (opp & CORNERS_MASK).bit_count()
    score = corner_diff * 85

    # 2. 角状態に応じた動的 C / X マス評価
    for c_bit, c_mask, x_bit in _CORNER_ADJ:
        if (occ & c_bit) == 0:
            # 角が空: X / C 打ちは危険
            if my & x_bit:
                score -= 36
            if opp & x_bit:
                score += 36
            score -= (my & c_mask).bit_count() * 16
            score += (opp & c_mask).bit_count() * 16
        elif my & c_bit:
            # 自角確保済み: 隣接地は安定加算
            if my & x_bit:
                score += 6
            score += (my & c_mask).bit_count() * 8
        else:
            # 相手角確保済み
            if opp & x_bit:
                score -= 6
            score -= (opp & c_mask).bit_count() * 8

    # 3. 安定辺石差
    score += _edge_stability_score(my, opp) * 18

    # 4. 着手可能数（モビリティ）
    my_mob = legal_moves_mask(my, opp).bit_count()
    opp_mob = legal_moves_mask(opp, my).bit_count()
    mob_w = 11 if stones < 46 else 6
    score += (my_mob - opp_mob) * mob_w
    if my_mob == 0 and opp_mob > 0:
        score -= 24
    elif opp_mob == 0 and my_mob > 0:
        score += 24

    # 5. フロンティア石数（空きに隣接する石は少ない方が有利）
    empty = ~occ & FULL
    e_h = ((empty << 1) & NOT_A_FILE) | ((empty >> 1) & NOT_H_FILE)
    e_adj = e_h | (((empty | e_h) << 8) & FULL) | ((empty | e_h) >> 8)
    my_front = (my & e_adj).bit_count()
    opp_front = (opp & e_adj).bit_count()
    front_w = 6 if stones < 48 else 3
    score += (opp_front - my_front) * front_w

    # 6. 静的配置バランス（良辺・中央・内側リング）
    score += ((my & _EDGES_AB).bit_count() - (opp & _EDGES_AB).bit_count()) * 10
    score += ((my & _EDGES_CD).bit_count() - (opp & _EDGES_CD).bit_count()) * 5
    score += ((my & _INNER_4X4).bit_count() - (opp & _INNER_4X4).bit_count()) * 3
    score -= ((my & _BAD_RING).bit_count() - (opp & _BAD_RING).bit_count()) * 4

    # 7. パリティ（残り手数が奇数のとき先手が最後を取りやすい）
    if empties <= 24:
        score += 10 if (empties & 1) == 1 else -4

    # 8. 石数差（序盤は少なく、終盤前は多めに加点）
    disc_diff = my_cnt - opp_cnt
    if stones < 28:
        score -= disc_diff
    elif stones > 44:
        score += disc_diff * 3

    return float(score)


class BitboardTeacherAgent(Agent):
    """64-bit ビットボード + PVS + TT + Killer/History による教師用強探索エージェント。"""

    def __init__(
        self,
        time_limit_ms: int = 200,
        max_depth: int = 60,
        endgame_empties: int = 14,
    ) -> None:
        self._time_limit_ms = time_limit_ms
        self._max_depth = max_depth
        self._endgame_empties = endgame_empties
        self._start_time = 0.0
        self._nodes_checked = 0
        # key: (my, opp) -> (depth, flag, value, best_sq)
        self._tt: dict[tuple[int, int], tuple[int, int, float, int]] = {}
        self._killers: list[list[int]] = [[-1, -1] for _ in range(80)]
        self._history: dict[tuple[int, int], int] = {}

    def _time_exceeded(self) -> bool:
        return (time.monotonic() - self._start_time) * 1000.0 >= self._time_limit_ms

    def _order_moves(
        self,
        my: int,
        opp: int,
        moves_mask: int,
        tt_sq: int,
        depth: int,
        ply: int,
        side: int,
    ) -> list[int]:
        """PV/TT -> Killer + 最少相手合法手 / 静的スコア順にソートした候補手を返す。"""
        sqs: list[int] = []
        rem = moves_mask
        while rem:
            lsb = rem & -rem
            sq = lsb.bit_length() - 1
            sqs.append(sq)
            rem ^= lsb

        if len(sqs) <= 1:
            return sqs

        killer_slot = self._killers[min(ply, 79)]
        k0, k1 = killer_slot[0], killer_slot[1]
        use_mob_order = depth >= 4 and len(sqs) > 2

        scored: list[tuple[int, int]] = []
        hist = self._history
        sq_w = _SQ_ORDER_WEIGHT
        for sq in sqs:
            if sq == tt_sq:
                scored.append((10_000_000, sq))
                continue
            prio = 0
            if sq == k0:
                prio += 200_000
            elif sq == k1:
                prio += 100_000
            prio += min(hist.get((side, sq), 0), 50_000)
            prio += sq_w[sq] * 10
            if use_mob_order:
                n_my, n_opp = apply_move_bitboard(my, opp, sq)
                opp_mob = legal_moves_mask(n_opp, n_my).bit_count()
                prio -= opp_mob * 600
            scored.append((prio, sq))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [sq for _, sq in scored]

    def _record_killer(self, ply: int, sq: int) -> None:
        slot = self._killers[min(ply, 79)]
        if slot[0] != sq:
            slot[1] = slot[0]
            slot[0] = sq

    def _negamax(
        self,
        my: int,
        opp: int,
        depth: int,
        alpha: float,
        beta: float,
        ply: int,
        side: int,
        endgame: bool,
    ) -> float:
        """ビットボード上の PVS + Alpha-Beta 探索。"""
        self._nodes_checked += 1
        if (self._nodes_checked & (_NODES_PER_TIME_CHECK - 1)) == 0:
            if self._time_exceeded():
                raise _SearchTimeout()

        key = (my, opp)
        entry = self._tt.get(key)
        tt_sq = -1
        if entry is not None:
            e_depth, e_flag, e_val, tt_sq = entry
            if ply > 0 and e_depth >= depth:
                if e_flag == _TT_EXACT:
                    return e_val
                if e_flag == _TT_LOWER and e_val >= beta:
                    return e_val
                if e_flag == _TT_UPPER and e_val <= alpha:
                    return e_val

        moves_mask = legal_moves_mask(my, opp)
        if moves_mask == 0:
            opp_moves = legal_moves_mask(opp, my)
            if opp_moves == 0:
                val = float((my.bit_count() - opp.bit_count()) * 10000)
                self._tt[key] = (depth, _TT_EXACT, val, -1)
                return val
            val = -self._negamax(
                opp, my, depth, -beta, -alpha, ply + 1, side ^ 1, endgame
            )
            self._tt[key] = (depth, _TT_EXACT, val, -1)
            return val

        if depth <= 0:
            if endgame:
                val = float((my.bit_count() - opp.bit_count()) * 10000)
            else:
                val = evaluate_bitboard(my, opp)
            self._tt[key] = (0, _TT_EXACT, val, -1)
            return val

        ordered = self._order_moves(my, opp, moves_mask, tt_sq, depth, ply, side)
        orig_alpha = alpha
        best_val = -_INF
        best_sq = ordered[0]

        for idx, sq in enumerate(ordered):
            next_my, next_opp = apply_move_bitboard(my, opp, sq)
            if idx == 0 or alpha == -_INF:
                val = -self._negamax(
                    next_opp, next_my, depth - 1, -beta, -alpha, ply + 1, side ^ 1, endgame
                )
            else:
                val = -self._negamax(
                    next_opp,
                    next_my,
                    depth - 1,
                    -alpha - 1.0,
                    -alpha,
                    ply + 1,
                    side ^ 1,
                    endgame,
                )
                if alpha < val < beta:
                    val = -self._negamax(
                        next_opp,
                        next_my,
                        depth - 1,
                        -beta,
                        -alpha,
                        ply + 1,
                        side ^ 1,
                        endgame,
                    )

            if val > best_val:
                best_val = val
                best_sq = sq
            if val > alpha:
                alpha = val
                if alpha >= beta:
                    self._record_killer(ply, sq)
                    self._history[(side, sq)] = self._history.get((side, sq), 0) + (
                        1 << min(depth, 16)
                    )
                    break

        if best_val >= beta:
            flag = _TT_LOWER
        elif best_val <= orig_alpha:
            flag = _TT_UPPER
        else:
            flag = _TT_EXACT
        self._tt[key] = (depth, flag, best_val, best_sq)
        return best_val

    def play_with_score(
        self, game: "Game"
    ) -> tuple[Optional[tuple[int, int]], float]:
        """最善手とその探索評価値を返す。"""
        valid_moves: list[tuple[int, int]] = game.get_valid_moves()
        if not valid_moves:
            return None, 0.0
        if len(valid_moves) == 1:
            return valid_moves[0], 0.0

        my, opp = board_to_bitboards(game.board.board, game.turn)
        empties = 64 - (my | opp).bit_count()
        endgame = empties <= self._endgame_empties
        depth_cap = min(self._max_depth, empties)

        self._start_time = time.monotonic()
        self._nodes_checked = 0
        self._tt.clear()
        self._killers = [[-1, -1] for _ in range(80)]
        self._history = {}

        best_move: tuple[int, int] = valid_moves[0]
        best_value = 0.0
        pv_sq = best_move[0] * 8 + best_move[1]

        for d in range(1, depth_cap + 1):
            if d >= 2 and self._time_exceeded():
                break
            try:
                moves_mask = legal_moves_mask(my, opp)
                ordered = self._order_moves(my, opp, moves_mask, pv_sq, d, 0, 0)
                alpha = -_INF
                beta = _INF
                iter_best_val = -_INF
                iter_best_sq = ordered[0]

                for idx, sq in enumerate(ordered):
                    next_my, next_opp = apply_move_bitboard(my, opp, sq)
                    if idx == 0 or alpha == -_INF:
                        val = -self._negamax(
                            next_opp, next_my, d - 1, -beta, -alpha, 1, 1, endgame
                        )
                    else:
                        val = -self._negamax(
                            next_opp,
                            next_my,
                            d - 1,
                            -alpha - 1.0,
                            -alpha,
                            1,
                            1,
                            endgame,
                        )
                        if alpha < val < beta:
                            val = -self._negamax(
                                next_opp,
                                next_my,
                                d - 1,
                                -beta,
                                -alpha,
                                1,
                                1,
                                endgame,
                            )
                    if val > iter_best_val:
                        iter_best_val = val
                        iter_best_sq = sq
                    if val > alpha:
                        alpha = val

                best_value = float(iter_best_val)
                pv_sq = iter_best_sq
                best_move = divmod(iter_best_sq, 8)
                self._tt[(my, opp)] = (d, _TT_EXACT, best_value, iter_best_sq)
            except _SearchTimeout:
                break

            if not endgame and abs(best_value) >= 10000:
                break
            if d >= empties:
                break

        return best_move, best_value

    def play(self, game: "Game") -> Optional[tuple[int, int]]:
        """与えられたゲーム状態で最善手を返す。"""
        return self.play_with_score(game)[0]

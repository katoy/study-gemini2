"""AlphaZero の評価モジュール（真のペア設計・開口ランダム化・任意エージェント対応）。"""
from __future__ import annotations

import math
import random
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.alpha_zero_agent import AlphaZeroAgent
from agents.base_agent import Agent
from agents.negamax_agent import NegamaxAgent
from agents.networks.othello_net import OthelloNNet
from game import Game


@dataclass
class EvalResult:
    """評価結果を格納する dataclass。

    Attributes:
        win_rate: 勝率（0.0 〜 1.0）。
        mean_stone_diff: 平均石差（AlphaZero 視点、-64 〜 +64）。
        results: ゲームごとの結果辞書リスト。各要素は
            {"opening_index", "az_is_white", "az_wins", "stone_diff"}。
    """

    win_rate: float
    mean_stone_diff: float
    results: list[dict[str, int | bool]]

    @property
    def wins(self) -> int:
        """勝ち局数（stone_diff > 0）。"""
        return sum(1 for r in self.results if int(r["stone_diff"]) > 0)

    @property
    def draws(self) -> int:
        """引き分け局数（stone_diff == 0）。"""
        return sum(1 for r in self.results if int(r["stone_diff"]) == 0)

    @property
    def losses(self) -> int:
        """負け局数（stone_diff < 0）。"""
        return sum(1 for r in self.results if int(r["stone_diff"]) < 0)

    def wilson_ci(self, z: float = 1.96) -> tuple[float, float]:
        """Wilson スコア区間による勝率の信頼区間 (lower, upper) を返す。"""
        n = len(self.results)
        if n == 0:
            return (0.0, 0.0)
        p = self.win_rate
        denom = 1.0 + z * z / n
        center = (p + z * z / (2.0 * n)) / denom
        half = (z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * n)) / n)) / denom
        return max(0.0, center - half), min(1.0, center + half)


def _generate_opening_board(
    board_size: int,
    opening_random_plies: int,
    rng: random.Random,
) -> tuple[list[list[int]], int, bool]:
    """指定手数のランダム開口盤面を 1 回だけ生成してスナップショットを返す。"""
    game = Game(board_size=board_size)
    for _ in range(opening_random_plies):
        if game.game_over:
            break

        valid_moves = game.get_valid_moves()
        if not valid_moves:
            game.switch_turn()
            valid_moves = game.get_valid_moves()

        if not valid_moves:
            break

        move = rng.choice(valid_moves)
        game.place_stone(move[0], move[1])
        game.switch_turn()
        game.check_game_over()

    return [row[:] for row in game.board.board], game.turn, game.game_over


def evaluate_against_agent(
    net: OthelloNNet,
    opponent_factory: Callable[[], Agent],
    *,
    n_games: int,
    n_simulations: int = 200,
    endgame_empties: int = 0,
    endgame_time_limit_ms: int = 10000,
    opening_random_plies: int = 4,
    seed: int | None = None,
    board_size: int = 8,
    show_progress: bool = True,
) -> EvalResult:
    """AlphaZero エージェントを任意エージェントに対してペア設計で評価する。

    各開口を 1 回だけ生成し、その同一開口盤面から AlphaZero 白番・黒番の
    2 局を実施する真のペア設計により、評価分散を抑制する。
    """
    if n_games % 2 != 0:
        raise ValueError(f"n_games must be even, got {n_games}")

    rng = random.Random(seed)
    alpha_zero = AlphaZeroAgent.from_net(
        net,
        n_simulations=n_simulations,
        endgame_empties=endgame_empties,
        endgame_time_limit_ms=endgame_time_limit_ms,
        board_size=board_size,
    )

    n_openings = n_games // 2
    results: list[dict[str, int | bool]] = []
    wins = 0.0
    stone_diffs: list[int] = []

    for opening_idx in range(n_openings):
        opening_board, opening_turn, opening_over = _generate_opening_board(
            board_size, opening_random_plies, rng
        )
        for az_is_white in [True, False]:
            game = Game(board_size=board_size)
            game.board.board = [row[:] for row in opening_board]
            game.turn = opening_turn
            game.game_over = opening_over
            game._invalidate_valid_moves_cache()

            opponent = opponent_factory()
            while not game.game_over:
                if (game.turn == 1) == az_is_white:
                    move = alpha_zero.play(game)
                else:
                    move = opponent.play(game)

                if move is not None:
                    game.place_stone(move[0], move[1])
                game.switch_turn()
                game.check_game_over()

            black, white = game.board.count_stones()
            stone_diff = (white - black) if az_is_white else (black - white)
            az_wins = stone_diff > 0
            if az_wins:
                wins += 1.0

            stone_diffs.append(stone_diff)
            results.append({
                "opening_index": opening_idx,
                "az_is_white": az_is_white,
                "az_wins": az_wins,
                "stone_diff": stone_diff,
            })

            if show_progress:
                game_num = opening_idx * 2 + (0 if az_is_white else 1) + 1
                sys.stdout.write("." if game_num % 10 else f"{game_num}")
                sys.stdout.flush()

    if show_progress:
        sys.stdout.write("\n")
        sys.stdout.flush()

    win_rate = wins / n_games
    mean_stone_diff = sum(stone_diffs) / len(stone_diffs) if stone_diffs else 0.0

    return EvalResult(
        win_rate=win_rate,
        mean_stone_diff=mean_stone_diff,
        results=results,
    )


def evaluate_against_negamax(
    net: OthelloNNet,
    *,
    n_games: int,
    time_limit_ms: int,
    n_simulations: int = 200,
    endgame_empties: int = 0,
    endgame_time_limit_ms: int = 10000,
    opening_random_plies: int = 4,
    seed: int | None = None,
    board_size: int = 8,
) -> EvalResult:
    """AlphaZero エージェントを Negamax に対して評価する。"""
    return evaluate_against_agent(
        net,
        lambda: NegamaxAgent(time_limit_ms=time_limit_ms),
        n_games=n_games,
        n_simulations=n_simulations,
        endgame_empties=endgame_empties,
        endgame_time_limit_ms=endgame_time_limit_ms,
        opening_random_plies=opening_random_plies,
        seed=seed,
        board_size=board_size,
    )

"""AlphaZero の評価モジュール（開口ランダム化・ペア設計対応）。"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from agents.alpha_zero_agent import AlphaZeroAgent
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
    results: list[dict]


def evaluate_against_negamax(
    net: OthelloNNet,
    *,
    n_games: int,
    time_limit_ms: int,
    n_simulations: int = 200,
    opening_random_plies: int = 4,
    seed: int | None = None,
    board_size: int = 8,
) -> EvalResult:
    """AlphaZero エージェントを Negamax に対して評価する。

    ペア設計（同一開口で先手/後手を交互）と開口ランダム化により、
    統計的に信頼性の高い勝率測定を実現。

    Args:
        net: AlphaZero のニューラルネットワーク。
        n_games: 実施するゲーム数（必ず偶数）。
        time_limit_ms: Negamax の思考時間制限（ミリ秒）。
        n_simulations: AlphaZero の MCTS シミュレーション数。デフォルト 200。
        opening_random_plies: 開口ランダム化の手数。デフォルト 4。
        seed: 乱数シード（None なら非決定的）。
        board_size: ボードサイズ（デフォルト 8）。

    Returns:
        EvalResult オブジェクト（win_rate, mean_stone_diff, per-game 記録）。

    Raises:
        ValueError: n_games が偶数でない場合。
    """
    if n_games % 2 != 0:
        raise ValueError(f"n_games must be even, got {n_games}")

    # 乱数ジェネレータ初期化
    if seed is not None:
        torch.manual_seed(seed)

    alpha_zero = AlphaZeroAgent.from_net(net, n_simulations=n_simulations)
    negamax = NegamaxAgent(time_limit_ms=time_limit_ms)

    n_openings = n_games // 2
    results = []
    wins = 0.0
    stone_diffs = []

    for opening_idx in range(n_openings):
        for az_is_white in [True, False]:
            game = Game(board_size=board_size)

            # 開口ランダム化：最初の opening_random_plies 手をランダムに選択
            for _ in range(opening_random_plies):
                if game.game_over:
                    break

                valid_moves = game.get_valid_moves()
                if not valid_moves:
                    game.switch_turn()
                    valid_moves = game.get_valid_moves()

                if not valid_moves:
                    break

                # ランダムに合法手を選択
                move = valid_moves[torch.randint(len(valid_moves), (1,)).item()]
                game.place_stone(move[0], move[1])
                game.switch_turn()
                game.check_game_over()

            # 本局：AlphaZero と Negamax で対局
            while not game.game_over:
                if (game.turn == 1) == az_is_white:
                    move = alpha_zero.play(game)
                else:
                    move = negamax.play(game)

                if move is not None:
                    game.place_stone(move[0], move[1])
                game.switch_turn()
                game.check_game_over()

            # 勝敗と石差を計算
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

            # 進捗表示
            game_num = opening_idx * 2 + (0 if az_is_white else 1) + 1
            sys.stdout.write("." if game_num % 10 else f"{game_num}")
            sys.stdout.flush()

    sys.stdout.write("\n")
    sys.stdout.flush()

    win_rate = wins / n_games
    mean_stone_diff = sum(stone_diffs) / len(stone_diffs) if stone_diffs else 0.0

    return EvalResult(
        win_rate=win_rate,
        mean_stone_diff=mean_stone_diff,
        results=results,
    )

#!/usr/bin/env python3
"""NegamaxAgent 強さベンチマーク（Tier 2 / ローカル詳細版）。

使い方:
    uv run python scripts/benchmark_agents.py
    uv run python scripts/benchmark_agents.py --opponent gain --games 5
    uv run python scripts/benchmark_agents.py --mcts-iterations 100 --time-limit-ms 1000

受け入れ基準: --opponent mcts 時に Negamax が 80% 以上の勝率。
"""
import argparse
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.alpha_zero_agent import AlphaZeroAgent  # noqa: E402
from agents.gain_agent import GainAgent  # noqa: E402
from agents.mcts_agent import MonteCarloTreeSearchAgent  # noqa: E402
from agents.negamax_agent import NegamaxAgent  # noqa: E402
from agents.random_agent import RandomAgent  # noqa: E402
from agents.transposition_negamax_agent import TranspositionNegamaxAgent  # noqa: E402
from game import Game  # noqa: E402


def play_one_game(black_agent, white_agent, board_size: int) -> int:
    """1 局対戦し、石差（黒 - 白）を返す。"""
    game = Game(board_size=board_size)
    while not game.game_over:
        agent = black_agent if game.turn == -1 else white_agent
        move = agent.play(game)
        if move is not None:
            game.place_stone(move[0], move[1])
        game.switch_turn()
        game.check_game_over()
    black, white = game.board.count_stones()
    return black - white


def make_opponent(args: argparse.Namespace):
    """--opponent 引数からエージェントインスタンスを生成する。"""
    if args.opponent == "mcts":
        return MonteCarloTreeSearchAgent(
            iterations=args.mcts_iterations,
            time_limit_ms=args.time_limit_ms,
        )
    if args.opponent == "gain":
        return GainAgent()
    return RandomAgent()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=int, default=10,
                        help="対戦ゲーム数（デフォルト: 10）")
    parser.add_argument("--time-limit-ms", type=int, default=200,
                        help="Negamax の思考時間上限 ms（デフォルト: 200）")
    parser.add_argument("--board-size", type=int, default=8)
    parser.add_argument("--mcts-iterations", type=int, default=20,
                        help="MCTS の反復回数（デフォルト: 20）")
    parser.add_argument("--agent", choices=["negamax", "transposition"],
                        default="negamax",
                        help="テスト対象エージェント（デフォルト: negamax）")
    parser.add_argument("--opponent", choices=["mcts", "gain", "random", "alphazero_n6k", "alphazero_n6k_v2"],
                        default="mcts",
                        help="対戦相手（デフォルト: mcts）")
    args = parser.parse_args()

    # テスト対象エージェントを生成
    if args.agent == "transposition":
        agent: object = TranspositionNegamaxAgent(time_limit_ms=args.time_limit_ms)
        agent_name = f"Transposition({args.time_limit_ms}ms)"
    else:
        agent = NegamaxAgent(time_limit_ms=args.time_limit_ms)  # type: ignore[assignment]
        agent_name = f"Negamax({args.time_limit_ms}ms)"

    # 対戦相手を生成
    if args.opponent == "mcts":
        opponent_name = f"mcts(iterations={args.mcts_iterations})"
        win_threshold = 0.80
    elif args.opponent == "gain":
        opponent_name = "gain"
        win_threshold = 0.60
    elif args.opponent == "random":
        opponent_name = "random"
        win_threshold = 0.60
    elif args.opponent == "alphazero_n6k":
        opponent_name = "AlphaZero-N6K(sim=200)"
        win_threshold = 0.40
    elif args.opponent == "alphazero_n6k_v2":
        opponent_name = "AlphaZero-N6Kv2(sim=200)"
        win_threshold = 0.40
    else:
        opponent_name = args.opponent
        win_threshold = 0.50

    print(f"{agent_name} vs {opponent_name}  board={args.board_size}x{args.board_size}  games={args.games}")
    print("-" * 50)

    wins = losses = draws = 0
    start = time.monotonic()

    for i in range(args.games):
        random.seed(i)
        if args.opponent == "alphazero_n6k":
            opponent = AlphaZeroAgent(
                n_simulations=200,
                model_path="models/alpha_zero_nega6000.pth",
            )
        elif args.opponent == "alphazero_n6k_v2":
            opponent = AlphaZeroAgent(
                n_simulations=200,
                model_path="models/alpha_zero_nega6000_v2.pth",
            )
        else:
            opponent = make_opponent(args)
        t0 = time.monotonic()
        if i % 2 == 0:
            diff = play_one_game(agent, opponent, args.board_size)
        else:
            diff = -play_one_game(opponent, agent, args.board_size)
        elapsed_game = time.monotonic() - t0
        if diff > 0:
            wins += 1
        elif diff < 0:
            losses += 1
        else:
            draws += 1
        print(f"game {i + 1:3d}: 石差 {diff:+4d}  {elapsed_game:.1f}s  "
              f"(W{wins} / L{losses} / D{draws})")

    elapsed = time.monotonic() - start
    rate = wins / args.games * 100
    print("-" * 50)
    print(f"勝率 {rate:.0f}%  (W{wins} / L{losses} / D{draws})  "
          f"合計 {elapsed:.0f}s  平均 {elapsed / args.games:.1f}s/game")
    print(f"受け入れ基準 (>= {win_threshold * 100:.0f}%): {'PASS' if rate >= win_threshold * 100 else 'FAIL'}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""NegamaxAgent vs MonteCarloTreeSearchAgent の自動対戦ベンチマーク。

使い方:
    uv run python scripts/benchmark_agents.py --games 20 --time-limit-ms 1000

受け入れ基準: Negamax (time_limit_ms=1000) が既定 MCTS に勝率 80% 以上。
"""
import argparse
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.mcts_agent import MonteCarloTreeSearchAgent  # noqa: E402
from agents.negamax_agent import NegamaxAgent  # noqa: E402
from game import Game  # noqa: E402


def play_one_game(black_agent, white_agent, board_size: int) -> int:
    """1 局対戦し、石差（黒 - 白）を返す。

    game.py の公開 API（place_stone / switch_turn / check_game_over）を使う。
    place_stone はキャッシュ無効化と履歴管理を行うため、内部状態を直接
    触らない。両者が着手不能になると check_game_over が game_over を立てる。
    """
    game = Game(board_size=board_size)   # game.turn は -1（黒）で開始
    while not game.game_over:
        agent = black_agent if game.turn == -1 else white_agent
        move = agent.play(game)
        if move is not None:
            game.place_stone(move[0], move[1])
        game.switch_turn()
        game.check_game_over()
    black, white = game.board.count_stones()
    return black - white


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=int, default=20)
    parser.add_argument("--time-limit-ms", type=int, default=1000)
    parser.add_argument("--board-size", type=int, default=8)
    args = parser.parse_args()

    wins = losses = draws = 0
    start = time.monotonic()
    for i in range(args.games):
        random.seed(i)  # MCTS 側の乱数を再現可能にする
        negamax = NegamaxAgent(time_limit_ms=args.time_limit_ms)
        mcts = MonteCarloTreeSearchAgent()
        if i % 2 == 0:   # 先手/後手を交互に入れ替える
            diff = play_one_game(negamax, mcts, args.board_size)
        else:
            diff = -play_one_game(mcts, negamax, args.board_size)
        if diff > 0:
            wins += 1
        elif diff < 0:
            losses += 1
        else:
            draws += 1
        print(f"game {i + 1:3d}: negamax 石差 {diff:+d} "
              f"(W{wins} / L{losses} / D{draws})")

    elapsed = time.monotonic() - start
    rate = wins / args.games * 100
    print("-" * 50)
    print(f"games={args.games} 勝率 {rate:.0f}% "
          f"(W{wins} / L{losses} / D{draws}) 所要 {elapsed:.0f}s")
    print("受け入れ基準 (>= 80%):", "PASS" if rate >= 80 else "FAIL")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""PatternAgent の重みを TD 学習で訓練。

使い方:
    uv run python scripts/train_pattern_weights.py --episodes 1000 --output data/pattern_weights.json

TD(0) アルゴリズムでエッジ・コーナー・対角線パターンの重みを学習する。
"""
import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.random_agent import RandomAgent
from agents.pattern_evaluator import PatternEvaluator
from agents.negamax_agent import _apply, _flips_for_move, _undo, _valid_moves
from game import Game


def play_self_play_game(board_size: int = 8) -> list[tuple[list[list[int]], int]]:
    """ランダム対戦で 1 ゲームを実施し、(盤面, 手番) のリストを返す。

    Args:
        board_size: 盤面サイズ。

    Returns:
        各手の (盤面コピー, 手番) のリスト。
    """
    game = Game(board_size=board_size)
    black_agent = RandomAgent()
    white_agent = RandomAgent()

    states = []
    while not game.game_over:
        board_copy = [row[:] for row in game.board.board]
        states.append((board_copy, game.turn))

        agent = black_agent if game.turn == -1 else white_agent
        move = agent.play(game)

        if move is not None:
            game.place_stone(move[0], move[1])
        game.switch_turn()
        game.check_game_over()

    return states


def get_final_value(game: Game) -> float:
    """ゲーム終了時の最終値を返す（黒視点）。

    Args:
        game: ゲーム状態（game_over=True）。

    Returns:
        +1.0（黒勝ち）、-1.0（白勝ち）、0.0（引き分け）。
    """
    black, white = game.board.count_stones()
    if black > white:
        return 1.0
    elif white > black:
        return -1.0
    else:
        return 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=int, default=1000,
                        help="訓練エピソード数（デフォルト: 1000）")
    parser.add_argument("--output", type=str, default="data/pattern_weights.json",
                        help="出力パス（デフォルト: data/pattern_weights.json）")
    parser.add_argument("--alpha", type=float, default=0.001,
                        help="学習率（デフォルト: 0.001）")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    evaluator = PatternEvaluator(board_size=8)
    alpha = args.alpha

    print(f"TD(0) 学習を開始します（{args.episodes} エピソード）")
    print(f"学習率: {alpha}")
    print(f"出力: {output_path}")

    for episode in range(args.episodes):
        # 1 ゲーム実施（ランダム対戦）
        game = Game(board_size=8)
        black_agent = RandomAgent()
        white_agent = RandomAgent()

        states = []
        while not game.game_over:
            board_copy = [row[:] for row in game.board.board]
            states.append((board_copy, game.turn))

            agent = black_agent if game.turn == -1 else white_agent
            move = agent.play(game)

            if move is not None:
                game.place_stone(move[0], move[1])
            game.switch_turn()
            game.check_game_over()

        # 最終値（黒視点）
        black, white = game.board.count_stones()
        if black > white:
            final_value = 1.0
        elif white > black:
            final_value = -1.0
        else:
            final_value = 0.0

        # TD(0) 更新
        for t in range(len(states) - 1):
            board_t, turn_t = states[t]
            board_t1, turn_t1 = states[t + 1]

            v_t = evaluator.evaluate(board_t, turn_t)
            v_t1 = evaluator.evaluate(board_t1, turn_t1) if t + 1 < len(states) else final_value
            error = v_t1 - v_t

            # 各パターンの重みを更新
            for pattern_name, squares in evaluator.patterns.items():
                idx = evaluator.pattern_index(board_t, squares, turn_t)
                evaluator.weights[pattern_name][idx] += alpha * error

        if (episode + 1) % 100 == 0:
            print(f"エピソード {episode + 1}/{args.episodes} 完了")

    # 重みを保存
    evaluator.save_weights(str(output_path))
    print(f"\n重みを保存しました: {output_path}")


if __name__ == "__main__":
    main()

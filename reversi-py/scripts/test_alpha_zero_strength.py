"""AlphaZero の強さテスト。

学習済みモデルで GainAgent と対戦。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
from agents.alpha_zero_agent import AlphaZeroAgent
from agents.gain_agent import GainAgent
from game import Game


def play_one_game(black_agent, white_agent) -> int:
    """1 局対戦し、石差を返す。"""
    game = Game(board_size=8)
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
    """AlphaZero の強さテスト。"""
    model_path = "models/alpha_zero_latest.pth"

    if not Path(model_path).exists():
        print(f"❌ Model not found: {model_path}")
        return

    print(f"🎮 AlphaZero Strength Test (model: {model_path})")
    print("  Playing 3 games vs GainAgent on 8x8 board\n")

    # AlphaZero と GainAgent を初期化
    alpha_zero = AlphaZeroAgent(n_simulations=20, model_path=model_path)
    gain = GainAgent()

    results = []

    # ゲーム1: AlphaZero (黒) vs GainAgent (白)
    print("Game 1: AlphaZero (black) vs GainAgent (white)")
    diff1 = play_one_game(alpha_zero, gain)
    result1 = "✅ WIN" if diff1 > 0 else f"❌ LOSS ({diff1})"
    print(f"  Stone diff: {diff1} {result1}\n")
    results.append(diff1)

    # ゲーム2: GainAgent (黒) vs AlphaZero (白)
    print("Game 2: GainAgent (black) vs AlphaZero (white)")
    diff2 = play_one_game(gain, alpha_zero)
    result2 = "✅ WIN" if diff2 < 0 else f"❌ LOSS ({diff2})"
    print(f"  Stone diff: {diff2} {result2}\n")
    results.append(diff2)

    # ゲーム3: AlphaZero (黒) vs GainAgent (白)
    print("Game 3: AlphaZero (black) vs GainAgent (white)")
    diff3 = play_one_game(alpha_zero, gain)
    result3 = "✅ WIN" if diff3 > 0 else f"❌ LOSS ({diff3})"
    print(f"  Stone diff: {diff3} {result3}\n")
    results.append(diff3)

    # 成績集計
    wins = sum(1 for d in results if (d > 0 and results.index(d) % 2 == 0) or (d < 0 and results.index(d) % 2 == 1))
    print(f"📊 Results: {wins}/3 wins")
    print(f"   Stone differences: {results}")

    if wins >= 2:
        print("\n✅ AlphaZero is stronger than GainAgent!")
    else:
        print("\n⚠️  AlphaZero needs more training.")


if __name__ == "__main__":
    main()

"""AlphaZero モデルの対 Minimax / Negamax 公式認定評価スクリプト。

純粋な NN + MCTS（終盤ソルバー無効 endgame_empties=0）での勝率を測定し、
指定目標勝率を厳密に上回るか（win_rate > target）を判定する。
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import torch
from agents.base_agent import Agent
from agents.minimax_agent import MinimaxAgent
from agents.negamax_agent import NegamaxAgent
from agents.networks.othello_net import OthelloNNet
from training.alphazero.checkpoint import load_checkpoint
from training.alphazero.evaluation import EvalResult, evaluate_against_agent


def build_opponent_factory(
    opponent_name: str, time_limit_ms: int
) -> Callable[[], Agent]:
    """対戦相手名に応じたファクトリを返す。"""
    if opponent_name == "minimax":
        return lambda: MinimaxAgent(time_limit_ms=time_limit_ms)
    if opponent_name == "negamax":
        return lambda: NegamaxAgent(time_limit_ms=time_limit_ms)
    raise ValueError(f"Unsupported opponent: {opponent_name}")


def evaluate_model_for_target(
    model_path: Path,
    opponent_names: list[str],
    *,
    time_limit_ms: int,
    n_games: int,
    n_simulations: int,
    opening_plies: int,
    seed: int,
    target: float,
) -> tuple[bool, dict[str, EvalResult]]:
    """指定モデルを各対戦相手に対して評価し、全相手で勝率 > target かを返す。"""
    net = OthelloNNet(board_size=8)
    load_checkpoint(net, model_path)
    net.eval()

    results: dict[str, EvalResult] = {}
    all_passed = True

    for name in opponent_names:
        print(
            f"\n[評価開始] model={model_path} vs {name}({time_limit_ms}ms) "
            f"| games={n_games}, sims={n_simulations}, endgame_empties=0, seed={seed}",
            flush=True,
        )
        t0 = time.perf_counter()
        res = evaluate_against_agent(
            net,
            build_opponent_factory(name, time_limit_ms),
            n_games=n_games,
            n_simulations=n_simulations,
            endgame_empties=0,
            opening_random_plies=opening_plies,
            seed=seed,
        )
        elapsed = time.perf_counter() - t0
        ci_lo, ci_hi = res.wilson_ci()
        passed = res.win_rate > target
        all_passed = all_passed and passed
        results[name] = res

        status = "PASS" if passed else "FAIL"
        print(
            f"[結果: {status}] vs {name}: win_rate={res.win_rate * 100:.1f}% "
            f"({res.wins}W-{res.draws}D-{res.losses}L / {n_games}), "
            f"mean_stone_diff={res.mean_stone_diff:+.2f}, "
            f"95%CI=[{ci_lo * 100:.1f}%, {ci_hi * 100:.1f}%], "
            f"elapsed={elapsed:.1f}s",
            flush=True,
        )

    return all_passed, results


def main() -> int:
    """CLI エントリーポイント。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=str, required=True, help="評価するモデルのパス")
    parser.add_argument(
        "--opponent",
        choices=["minimax", "negamax", "both"],
        default="minimax",
        help="対戦相手（デフォルト: minimax）",
    )
    parser.add_argument("--time-limit-ms", type=int, default=500)
    parser.add_argument("--games", type=int, default=50)
    parser.add_argument("--sims", type=int, default=200)
    parser.add_argument("--opening-plies", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--target", type=float, default=0.80)
    args = parser.parse_args()

    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    torch.set_num_threads(1)

    model_path = Path(args.model)
    if not model_path.exists():
        raise FileNotFoundError(f"モデルが見つかりません: {model_path}")

    opponents = ["minimax", "negamax"] if args.opponent == "both" else [args.opponent]
    passed, _ = evaluate_model_for_target(
        model_path,
        opponents,
        time_limit_ms=args.time_limit_ms,
        n_games=args.games,
        n_simulations=args.sims,
        opening_plies=args.opening_plies,
        seed=args.seed,
        target=args.target,
    )
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())

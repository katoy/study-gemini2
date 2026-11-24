"""AlphaZero モデルを外部エンジン Edax と対戦させ、世間的な強さの目安を測るスクリプト。

AlphaZero は GUI（API サーバー）と同じ設定で動かす。
既定では MCTS 800 回探索、空き 14 マス以下で終盤を読み切る。
Edax のレベルごとに、同じ開口から先後を入れ替えて対局し、勝率を表示する。
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import torch
from agents.edax_agent import EdaxAgent
from agents.networks.othello_net import OthelloNNet
from training.alphazero.checkpoint import load_checkpoint
from training.alphazero.evaluation import EvalResult, evaluate_against_agent

# GUI（server/api_server.py）の AlphaZero-Minimax80 と同じ既定値
_DEFAULT_SIMS = 800
_DEFAULT_ENDGAME_EMPTIES = 14
_DEFAULT_ENDGAME_TIME_LIMIT_MS = 10000


def evaluate_level(
    net: OthelloNNet,
    edax_path: Path,
    level: int,
    *,
    n_games: int,
    n_simulations: int,
    endgame_empties: int,
    endgame_time_limit_ms: int,
    opening_plies: int,
    seed: int,
) -> EvalResult:
    """Edax の 1 つのレベルに対して評価する。

    Edax は局面を毎手渡すので、1 つのプロセスを全対局で使い回す。
    """
    with EdaxAgent(edax_path, level=level) as edax:
        return evaluate_against_agent(
            net,
            lambda: edax,
            n_games=n_games,
            n_simulations=n_simulations,
            endgame_empties=endgame_empties,
            endgame_time_limit_ms=endgame_time_limit_ms,
            opening_random_plies=opening_plies,
            seed=seed,
        )


def main() -> int:
    """CLI エントリーポイント。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=Path("models/alpha_zero_minimax80_best.pth"))
    parser.add_argument("--edax", type=Path, required=True, help="Edax の実行ファイルのパス")
    parser.add_argument("--levels", type=int, nargs="+", default=[1, 2, 3, 4, 6, 8])
    parser.add_argument("--games", type=int, default=20, help="レベルごとの対局数（偶数）")
    parser.add_argument("--sims", type=int, default=_DEFAULT_SIMS)
    parser.add_argument("--endgame-empties", type=int, default=_DEFAULT_ENDGAME_EMPTIES)
    parser.add_argument("--endgame-time-limit-ms", type=int, default=_DEFAULT_ENDGAME_TIME_LIMIT_MS)
    parser.add_argument("--opening-plies", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    torch.set_num_threads(1)

    if not args.model.exists():
        raise FileNotFoundError(f"モデルが見つかりません: {args.model}")
    if not args.edax.exists():
        raise FileNotFoundError(f"Edax が見つかりません: {args.edax}")

    net = OthelloNNet(board_size=8)
    load_checkpoint(net, args.model)
    net.eval()

    print(
        f"model={args.model} | sims={args.sims}, endgame_empties={args.endgame_empties}, "
        f"games/level={args.games}, seed={args.seed}",
        flush=True,
    )
    for level in args.levels:
        print(f"\n[評価開始] vs Edax level {level}", flush=True)
        t0 = time.perf_counter()
        res = evaluate_level(
            net,
            args.edax,
            level,
            n_games=args.games,
            n_simulations=args.sims,
            endgame_empties=args.endgame_empties,
            endgame_time_limit_ms=args.endgame_time_limit_ms,
            opening_plies=args.opening_plies,
            seed=args.seed,
        )
        ci_lo, ci_hi = res.wilson_ci()
        print(
            f"[結果] vs Edax level {level}: win_rate={res.win_rate * 100:.1f}% "
            f"({res.wins}W-{res.draws}D-{res.losses}L / {args.games}), "
            f"mean_stone_diff={res.mean_stone_diff:+.2f}, "
            f"95%CI=[{ci_lo * 100:.1f}%, {ci_hi * 100:.1f}%], "
            f"elapsed={time.perf_counter() - t0:.1f}s",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

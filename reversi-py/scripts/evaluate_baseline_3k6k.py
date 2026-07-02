"""既存モデルのベースライン評価スクリプト（Negamax-3000ms / 6000ms）。

指定モデルを Negamax-3K / 6K それぞれに対して 50 ゲーム評価し、
統計的に信頼できる勝率を確定する。

評価プロトコル：
- 評価中は他の訓練・評価プロセスを走らせない（CPU 負荷で Negamax の強さが変わるため）
- 3K → 6K の逐次実行（並列禁止）
- 評価用 MCTS は n_simulations=150 固定
- 先手後手を交互に割り当て
"""
from __future__ import annotations

import os
import argparse
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
from agents.networks.othello_net import OthelloNNet
from training.alphazero.checkpoint import load_checkpoint
from training.alphazero.evaluation import evaluate_against_negamax

os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
torch.backends.mps.is_available = lambda: False
n_threads = int(os.cpu_count() or 4)
torch.set_num_threads(n_threads)
torch.set_num_interop_threads(1)
torch.set_float32_matmul_precision("high")
torch.backends.mkldnn.enabled = True

NEGAMAX_VARIANTS = {
    "negamax_3k": 3000,
    "negamax_6k": 6000,
}

EVAL_SIMULATIONS = 200
OPENING_RANDOM_PLIES = 4
DEFAULT_GAMES = 50
BOARD_SIZE = 8


def log_time(message: str) -> str:
    """メッセージに時刻を付与して返す。"""
    time_str = datetime.now().strftime("%H:%M:%S")
    return f"[{time_str}] {message}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="既存モデルの Negamax-3K/6K ベースライン評価"
    )
    parser.add_argument("--model", type=str, required=True, help="評価するモデルのパス")
    parser.add_argument("--games", type=int, default=DEFAULT_GAMES)
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.exists():
        raise FileNotFoundError(f"モデルが見つかりません: {model_path}")

    import io

    if isinstance(sys.stdout, io.TextIOBase):
        sys.stdout.reconfigure(line_buffering=True)

    print(f"\n{'=' * 70}", flush=True)
    print(log_time(f"ベースライン評価: {model_path.name}"), flush=True)
    print(f"評価設定: games={args.games}, eval_sims={EVAL_SIMULATIONS}", flush=True)
    print(f"{'=' * 70}\n", flush=True)

    net = OthelloNNet(board_size=BOARD_SIZE)
    load_checkpoint(net, model_path)
    net.eval()
    print(log_time("モデルロード完了"), flush=True)

    results: dict[str, float] = {}
    for name, time_limit_ms in NEGAMAX_VARIANTS.items():
        print(log_time(f"vs {name} ({time_limit_ms}ms) 評価開始"), flush=True)
        start = time.monotonic()
        evaluation_result = evaluate_against_negamax(
            net,
            n_games=args.games,
            time_limit_ms=time_limit_ms,
            n_simulations=EVAL_SIMULATIONS,
            opening_random_plies=OPENING_RANDOM_PLIES,
            board_size=BOARD_SIZE,
        )
        elapsed = time.monotonic() - start
        results[name] = evaluation_result.win_rate
        print(
            log_time(
                f"vs {name}: {evaluation_result.win_rate * 100:.1f}% "
                f"({int(evaluation_result.win_rate * args.games)}/{args.games} 勝, "
                f"平均石差 {evaluation_result.mean_stone_diff:.1f}, "
                f"所要 {elapsed / 60:.1f} 分)"
            ),
            flush=True,
        )

    print(f"\n{'=' * 70}", flush=True)
    print(log_time(f"最終結果: {model_path.name}"), flush=True)
    for name, rate in results.items():
        mark = "✅" if rate >= 0.95 else "❌"
        print(f"  {mark} vs {name}: {rate * 100:.1f}%", flush=True)
    min_rate = min(results.values())
    print(f"  min 勝率: {min_rate * 100:.1f}% (目標 95.0%)", flush=True)
    print(f"{'=' * 70}\n", flush=True)


if __name__ == "__main__":
    main()

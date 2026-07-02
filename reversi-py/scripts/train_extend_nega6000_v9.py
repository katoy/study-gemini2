"""AlphaZero-N6K v9 訓練スクリプト（リプレイバッファ・4エポック版）。

IT10 まで完了後、リプレイバッファを導入して過去のゲームサンプルを活用：
games=16, sims=125, eval_games=20（拡充）
リプレイバッファサイズ: 10 * games_per_iter
各イテレーション 4 エポック実行で学習を深化
negamax_3k と negamax_6k の両方に対して勝率 95 パーセント以上を目指す。
"""
from __future__ import annotations

import os
import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from collections import deque

sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from agents.alphazero.encoding import board_to_tensor
from agents.alphazero.mcts import MCTS, PASS_ACTION
from agents.networks.othello_net import OthelloNNet
from agents.negamax_agent import _apply, _flips_for_move, _valid_moves
from training.alphazero.checkpoint import load_checkpoint, save_best
from training.alphazero.losses import alphazero_loss
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


def log_time(message: str) -> str:
    """メッセージに時刻を付与して返す。"""
    time_str = datetime.now().strftime("%H:%M:%S")
    return f"[{time_str}] {message}"


@dataclass
class TrainConfig:
    n_iters: int = 200
    games_per_iter: int = 16
    n_simulations: int = 125
    c_puct: float = 1.5
    temp_moves: int = 6
    dirichlet_alpha: float = 0.3
    dirichlet_eps: float = 0.25
    batch_size: int = 256
    lr: float = 5e-5
    eval_games: int = 20
    eval_interval: int = 5
    board_size: int = 8
    warm_start: str = "models/alpha_zero_nega6000_v9_latest.pth"
    latest_model: str = "models/alpha_zero_nega6000_v9_latest.pth"
    best_model: str = "models/alpha_zero_nega6000_v9.pth"
    win_rate_target: float = 0.95


def _initial_board(board_size: int = 8) -> list[list[int]]:
    board = [[0] * board_size for _ in range(board_size)]
    mid = board_size // 2
    board[mid - 1][mid - 1] = 1
    board[mid][mid] = 1
    board[mid - 1][mid] = -1
    board[mid][mid - 1] = -1
    return board


def play_one_selfplay_game(
    net: OthelloNNet, cfg: TrainConfig
) -> list[tuple[torch.Tensor, torch.Tensor, float]]:
    mcts = MCTS(
        net=net,
        n_simulations=cfg.n_simulations,
        c_puct=cfg.c_puct,
        board_size=cfg.board_size,
        dirichlet_alpha=cfg.dirichlet_alpha,
        dirichlet_eps=cfg.dirichlet_eps,
    )
    board = _initial_board(cfg.board_size)
    turn = -1
    samples = []
    move_no = 0

    while True:
        moves = _valid_moves(board, cfg.board_size, turn)
        if not moves:
            if not _valid_moves(board, cfg.board_size, -turn):
                break
            turn = -turn
            continue

        sys.stdout.write(".")
        sys.stdout.flush()
        counts = mcts.run(board, turn)
        pi_arr = [0.0] * 65
        total = sum(counts.values()) or 1
        for action, visits in counts.items():
            pi_arr[action] = visits / total

        pi_tensor = torch.tensor(pi_arr, dtype=torch.float32)
        board_tensor = board_to_tensor(board, turn)
        samples.append((board_tensor, pi_tensor, turn))

        if move_no < cfg.temp_moves:
            import random

            actions = list(counts.keys())
            weights = [counts[action] for action in actions]
            best_action = random.choices(actions, weights=weights, k=1)[0]
        else:
            best_action = max(counts, key=lambda action: counts[action])

        if best_action != PASS_ACTION:
            row, col = divmod(best_action, cfg.board_size)
            flips = _flips_for_move(board, cfg.board_size, row, col, turn)
            _apply(board, (row, col), flips, turn)

        turn = -turn
        move_no += 1

    black = sum(cell == -1 for row in board for cell in row)
    white = sum(cell == 1 for row in board for cell in row)
    disc_diff = black - white

    result = []
    for board_t, pi, t in samples:
        z = float(t * disc_diff) / 32.0
        z = max(-1.0, min(1.0, z))
        result.append((board_t, pi, z))

    return result


def evaluate_vs_dual_negamax(
    net: OthelloNNet, n_games: int, cfg: TrainConfig
) -> dict[str, float]:
    return {
        name: evaluate_against_negamax(
            net,
            n_games=n_games,
            time_limit_ms=time_limit_ms,
            n_simulations=200,
            opening_random_plies=4,
            board_size=cfg.board_size,
        ).win_rate
        for name, time_limit_ms in NEGAMAX_VARIANTS.items()
    }


def dual_negamax_score(rates: dict[str, float]) -> float:
    return min(rates.values()) if rates else 0.0


def dual_negamax_target_met(
    rates: dict[str, float], target: float
) -> bool:
    return all(rate >= target for rate in rates.values())


def validate_training_config(cfg: TrainConfig) -> None:
    if cfg.batch_size < 2:
        raise ValueError("batch_size >= 2 required")


def resolve_resume_path(cfg: TrainConfig) -> Path:
    warm_start = Path(cfg.warm_start)
    latest_model = Path(cfg.latest_model)
    # コマンドラインで明示的に warm_start が指定されて、デフォルト値と異なる場合は優先
    if str(warm_start) != "models/alpha_zero_nega6000_v9_latest.pth" and warm_start.exists():
        return warm_start
    if latest_model.exists():
        return latest_model
    if warm_start.exists():
        return warm_start
    return warm_start


def analyze_dual_negamax_progress(
    rates: dict[str, float], target: float
) -> str:
    if not rates:
        return "analysis: no evaluation results"

    min_name, min_rate = min(rates.items(), key=lambda item: item[1])
    max_name, max_rate = max(rates.items(), key=lambda item: item[1])
    gap = max(0.0, target - min_rate)
    spread = max_rate - min_rate
    status = "target met" if dual_negamax_target_met(rates, target) else "below target"

    return (
        f"analysis: {status}, "
        f"worst={min_name}({min_rate * 100:.1f}%), "
        f"best={max_name}({max_rate * 100:.1f}%), "
        f"gap_to_target={gap * 100:.1f}%, "
        f"spread={spread * 100:.1f}%"
    )


def should_evaluate_iteration(iteration_index: int, cfg: TrainConfig) -> bool:
    return (
        ((iteration_index + 1) % cfg.eval_interval) == 0
        or (iteration_index + 1) == cfg.n_iters
    )


def main(cfg: TrainConfig) -> None:
    validate_training_config(cfg)

    print(f"\n{'=' * 70}", flush=True)
    print(log_time("AlphaZero-N6K v9 訓練（リプレイバッファ・4エポック版）"), flush=True)
    print("目標: Negamax-3K / Negamax-6K 95% 以上", flush=True)
    print(f"改善: games={cfg.games_per_iter}, sims={cfg.n_simulations}, lr={cfg.lr}, replay_buffer=4epochs", flush=True)
    print(f"{'=' * 70}\n", flush=True)

    import io

    if isinstance(sys.stdout, io.TextIOBase):
        sys.stdout.reconfigure(line_buffering=True)

    device = "cpu"
    net = OthelloNNet(board_size=cfg.board_size).to(device)

    warm_start = resolve_resume_path(cfg)
    if warm_start.exists():
        print(log_time(f"warm-start: {warm_start.name}"), flush=True)
        load_checkpoint(net, warm_start)
    else:
        print(log_time("warm-start not found"), flush=True)

    # warm-start モデルのロード後にベースライン測定
    if warm_start.exists():
        print(log_time("評価: warm-start モデルのベースライン測定"), flush=True)
        net.eval()
        rates = evaluate_vs_dual_negamax(net, cfg.eval_games, cfg)
        best_score = dual_negamax_score(rates)
        print(log_time(f"  ベースライン min勝率: {best_score * 100:.1f}%"), flush=True)
    else:
        best_score = 0.0

    optimizer = optim.Adam(net.parameters(), lr=cfg.lr)
    last_eval_rates = None
    last_eval_iter = 0

    # リプレイバッファを初期化
    replay_buffer: deque[tuple[torch.Tensor, torch.Tensor, float]] = deque(
        maxlen=10 * cfg.games_per_iter
    )

    for it in range(cfg.n_iters):
        print(log_time(f"イテレーション {it + 1}/{cfg.n_iters}"), flush=True)

        net.eval()
        buffer = []
        for game_idx in range(cfg.games_per_iter):
            samples = play_one_selfplay_game(net, cfg)
            buffer.extend(samples)
            if (game_idx + 1) % 4 == 0:
                print(log_time(f"  [進捗] {game_idx + 1}/{cfg.games_per_iter} ゲーム完了"), flush=True)

        # リプレイバッファに新規サンプルを追加
        replay_buffer.extend(buffer)
        print(log_time(f"  サンプル: {len(buffer)} (バッファ内: {len(replay_buffer)})"), flush=True)

        if len(replay_buffer) < cfg.batch_size:
            continue

        # リプレイバッファからデータセットを構築
        boards = torch.cat([sample[0] for sample in replay_buffer])
        pis = torch.stack([sample[1] for sample in replay_buffer])
        zs = torch.tensor([sample[2] for sample in replay_buffer], dtype=torch.float32)
        dataset = TensorDataset(boards, pis, zs)
        loader = DataLoader(dataset, batch_size=cfg.batch_size, shuffle=True, drop_last=True)

        net.train()
        total_loss_sum = 0.0
        total_batches = 0

        # 4 エポック実行
        for epoch in range(4):
            for boards_b, pis_b, zs_b in loader:
                optimizer.zero_grad()
                logits, v = net(boards_b)
                _, policy_loss, value_loss = alphazero_loss(logits, v, pis_b, zs_b)
                loss = policy_loss + 2.0 * value_loss
                loss.backward()
                optimizer.step()
                total_loss_sum += float(loss.item())
                total_batches += 1

        avg_loss = total_loss_sum / total_batches if total_batches > 0 else 0.0
        print(log_time(f"  loss: {avg_loss:.4f}"), flush=True)
        save_best(net, cfg.latest_model)
        print(log_time(f"  💾 latest 保存: {Path(cfg.latest_model).name}"), flush=True)

        should_eval = should_evaluate_iteration(it, cfg)

        if should_eval:
            net.eval()
            rates = evaluate_vs_dual_negamax(net, cfg.eval_games, cfg)
            last_eval_rates = rates
            last_eval_iter = it + 1
            print(
                log_time(
                    "  vs Negamax-3K: "
                    f"{rates['negamax_3k'] * 100:.1f}%"
                ),
                flush=True
            )
            print(
                log_time(
                    "  vs Negamax-6K: "
                    f"{rates['negamax_6k'] * 100:.1f}%"
                ),
                flush=True
            )
            print(log_time(f"  {analyze_dual_negamax_progress(rates, cfg.win_rate_target)}"), flush=True)

            score = dual_negamax_score(rates)
            if score > best_score:
                best_score = score
                save_best(net, cfg.best_model)
                print(log_time(f"  ✅ モデル保存 (min勝率: {best_score * 100:.1f}%)"), flush=True)

            if dual_negamax_target_met(rates, cfg.win_rate_target):
                print(
                    log_time(
                        "\n🎉 目標達成: "
                        f"3K={rates['negamax_3k'] * 100:.1f}% "
                        f"6K={rates['negamax_6k'] * 100:.1f}%"
                    ),
                    flush=True
                )
                break
        elif last_eval_rates is not None:
            print(
                log_time(
                    "  last eval @ iter "
                    f"{last_eval_iter}: {analyze_dual_negamax_progress(last_eval_rates, cfg.win_rate_target)}"
                ),
                flush=True
            )
        else:
            print(log_time("  evaluation deferred"), flush=True)

    print(f"{'=' * 70}\n", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AlphaZero-N6K v9 訓練（リプレイバッファ・4エポック版）"
    )
    parser.add_argument("--iters", type=int, default=TrainConfig.n_iters)
    parser.add_argument("--games", type=int, default=TrainConfig.games_per_iter)
    parser.add_argument("--sims", type=int, default=TrainConfig.n_simulations)
    parser.add_argument("--cpuct", type=float, default=TrainConfig.c_puct)
    parser.add_argument("--temp-moves", type=int, default=TrainConfig.temp_moves)
    parser.add_argument("--batch-size", type=int, default=TrainConfig.batch_size)
    parser.add_argument("--lr", type=float, default=TrainConfig.lr)
    parser.add_argument("--eval-games", type=int, default=TrainConfig.eval_games)
    parser.add_argument("--eval-interval", type=int, default=TrainConfig.eval_interval)
    parser.add_argument("--warm-start", type=str, default=TrainConfig.warm_start)
    parser.add_argument("--best-model", type=str, default=TrainConfig.best_model)
    parser.add_argument("--target", type=float, default=TrainConfig.win_rate_target)
    args = parser.parse_args()

    config = TrainConfig(
        n_iters=args.iters,
        games_per_iter=args.games,
        n_simulations=args.sims,
        c_puct=args.cpuct,
        temp_moves=args.temp_moves,
        batch_size=args.batch_size,
        lr=args.lr,
        eval_games=args.eval_games,
        eval_interval=args.eval_interval,
        warm_start=args.warm_start,
        best_model=args.best_model,
        win_rate_target=args.target,
    )
    main(config)

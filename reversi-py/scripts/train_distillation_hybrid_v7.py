"""AlphaZero-N6K v7→Hybrid ハイブリッド蒸留訓練スクリプト。

v7 モデル（min勝率 40%）から Negamax-6K（教師）への蒸留訓練で
60% 達成を目指す。

特徴：
- v7 モデルから warm-start で開始
- 共通評価モジュール（開口ランダム化・ペア設計対応）を使用
- Negamax-3K と Negamax-6K の両方で評価（デュアル評価）
- min勝率 ≥ 60% 達成時点で訓練終了・最良モデル保存
- ゲート条件達成時に「Route B → Phase 3-A に接続可能」メッセージを出力

目標：Route B（v7 からの蒸留） → Phase 3-A へ接続
"""
from __future__ import annotations

import os
import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from agents.alphazero.encoding import board_to_tensor
from agents.networks.othello_net import OthelloNNet
from agents.negamax_agent import NegamaxAgent, _apply, _flips_for_move, _valid_moves
from game import Game
from training.alphazero.checkpoint import save_best
from training.alphazero.losses import alphazero_loss
from training.alphazero.evaluation import evaluate_against_negamax

os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
torch.backends.mps.is_available = lambda: False
n_threads = int(os.cpu_count() or 4)
torch.set_num_threads(n_threads)
torch.set_num_interop_threads(1)
torch.set_float32_matmul_precision("high")
torch.backends.mkldnn.enabled = True


def log_time(message: str) -> str:
    """メッセージに時刻を付与して返す。"""
    time_str = datetime.now().strftime("%H:%M:%S")
    return f"[{time_str}] {message}"


@dataclass
class DistillationConfig:
    n_iters: int = 200
    games_per_iter: int = 20
    teacher_time_limit_ms: int = 6000
    n_simulations: int = 200
    batch_size: int = 128
    lr: float = 5e-5
    eval_games: int = 50
    eval_interval: int = 5
    board_size: int = 8
    warm_start: str = "models/alpha_zero_nega6000_v7_dual_negamax.pth"
    latest_model: str = "models/alpha_zero_nega6000_hybrid_latest.pth"
    best_model: str = "models/alpha_zero_nega6000_hybrid.pth"
    win_rate_target: float = 0.60


def _initial_board(board_size: int = 8) -> list[list[int]]:
    board = [[0] * board_size for _ in range(board_size)]
    mid = board_size // 2
    board[mid - 1][mid - 1] = 1
    board[mid][mid] = 1
    board[mid - 1][mid] = -1
    board[mid][mid - 1] = -1
    return board


def play_distillation_game(
    net: OthelloNNet,
    teacher_agent: NegamaxAgent,
    cfg: DistillationConfig,
) -> list[tuple[torch.Tensor, torch.Tensor, float]]:
    """蒸留訓練用のゲームをプレイ。教師の policy を学習データとして収集。"""
    board = _initial_board(cfg.board_size)
    turn = -1
    samples = []

    while True:
        moves = _valid_moves(board, cfg.board_size, turn)
        if not moves:
            if not _valid_moves(board, cfg.board_size, -turn):
                break
            turn = -turn
            continue

        game = Game(board_size=cfg.board_size)
        game.board._board = [row[:] for row in board]
        game.turn = 1 if turn == 1 else -1
        game.check_game_over()

        teacher_move = teacher_agent.play(game)

        board_tensor = board_to_tensor(board, turn)

        pi_arr = [0.0] * 65
        if teacher_move is not None:
            action = teacher_move[0] * cfg.board_size + teacher_move[1]
            pi_arr[action] = 1.0

        pi_tensor = torch.tensor(pi_arr, dtype=torch.float32)
        samples.append((board_tensor, pi_tensor, turn))

        if teacher_move is not None:
            row, col = teacher_move
            flips = _flips_for_move(board, cfg.board_size, row, col, turn)
            _apply(board, (row, col), flips, turn)
            sys.stdout.write(".")
        else:
            sys.stdout.write("P")
        sys.stdout.flush()

        turn = -turn

    black = sum(cell == -1 for row in board for cell in row)
    white = sum(cell == 1 for row in board for cell in row)
    disc_diff = black - white

    result = []
    for board_t, pi, t in samples:
        z = float(t * disc_diff) / 32.0
        z = max(-1.0, min(1.0, z))
        result.append((board_t, pi, z))

    return result


def evaluate_dual(
    net: OthelloNNet,
    cfg: DistillationConfig,
) -> tuple[float, float, float]:
    """Negamax-3K と Negamax-6K に対して評価。min勝率を返す。"""
    print(log_time("  [評価] Negamax-3K に対して..."), flush=True)
    result_3k = evaluate_against_negamax(
        net,
        n_games=cfg.eval_games,
        time_limit_ms=3000,
        n_simulations=cfg.n_simulations,
        opening_random_plies=4,
        board_size=cfg.board_size,
    )
    rate_3k = result_3k.win_rate

    print(log_time("  [評価] Negamax-6K に対して..."), flush=True)
    result_6k = evaluate_against_negamax(
        net,
        n_games=cfg.eval_games,
        time_limit_ms=6000,
        n_simulations=cfg.n_simulations,
        opening_random_plies=4,
        board_size=cfg.board_size,
    )
    rate_6k = result_6k.win_rate

    min_rate = min(rate_3k, rate_6k)
    print(log_time(f"  vs Negamax-3K: {rate_3k * 100:.1f}% / vs Negamax-6K: {rate_6k * 100:.1f}% (min: {min_rate * 100:.1f}%)"), flush=True)

    return rate_3k, rate_6k, min_rate


def main(cfg: DistillationConfig) -> None:
    print(f"\n{'=' * 70}", flush=True)
    print(log_time("AlphaZero-N6K v7→Hybrid ハイブリッド蒸留訓練"), flush=True)
    print("教師: Negamax-6K で v7 から 60% 達成を目指す", flush=True)
    print(f"Warm-start: {cfg.warm_start}", flush=True)
    print(f"{'=' * 70}\n", flush=True)

    import io
    if isinstance(sys.stdout, io.TextIOBase):
        sys.stdout.reconfigure(line_buffering=True)

    device = "cpu"
    net = OthelloNNet(board_size=cfg.board_size).to(device)

    # warm-start: v7 モデルをロード
    if Path(cfg.warm_start).exists():
        print(log_time(f"v7 モデルをロード: {cfg.warm_start}"), flush=True)
        checkpoint = torch.load(cfg.warm_start, map_location=device)
        if isinstance(checkpoint, dict):
            if "model_state_dict" in checkpoint:
                net.load_state_dict(checkpoint["model_state_dict"])
            elif "state_dict" in checkpoint:
                net.load_state_dict(checkpoint["state_dict"])
            else:
                net.load_state_dict(checkpoint)
        else:
            net.load_state_dict(checkpoint)
        print(log_time("  ✅ ロード完了"), flush=True)
    else:
        print(log_time(f"⚠️  {cfg.warm_start} が見つかりません。ランダム初期化で開始"), flush=True)

    optimizer = optim.Adam(net.parameters(), lr=cfg.lr)
    teacher_agent = NegamaxAgent(time_limit_ms=cfg.teacher_time_limit_ms)
    best_score = 0.0

    # 初期評価
    print(log_time("初期評価を実施..."), flush=True)
    net.eval()
    rate_3k, rate_6k, min_rate = evaluate_dual(net, cfg)
    best_score = min_rate

    for it in range(cfg.n_iters):
        print(log_time(f"イテレーション {it + 1}/{cfg.n_iters}"), flush=True)

        net.eval()
        buffer = []
        for game_idx in range(cfg.games_per_iter):
            samples = play_distillation_game(net, teacher_agent, cfg)
            buffer.extend(samples)
            if (game_idx + 1) % 5 == 0:
                print(log_time(f"  [進捗] {game_idx + 1}/{cfg.games_per_iter} ゲーム完了"), flush=True)

        print(log_time(f"  サンプル: {len(buffer)}"), flush=True)

        if len(buffer) < cfg.batch_size:
            print(log_time(f"  警告: サンプル数 {len(buffer)} < batch_size {cfg.batch_size}"), flush=True)
            continue

        boards = torch.cat([sample[0] for sample in buffer])
        pis = torch.stack([sample[1] for sample in buffer])
        zs = torch.tensor([sample[2] for sample in buffer], dtype=torch.float32)
        dataset = TensorDataset(boards, pis, zs)
        loader = DataLoader(dataset, batch_size=cfg.batch_size, shuffle=True, drop_last=True)

        net.train()
        total_loss_sum = 0.0
        for boards_b, pis_b, zs_b in loader:
            optimizer.zero_grad()
            logits, v = net(boards_b)
            _, policy_loss, value_loss = alphazero_loss(logits, v, pis_b, zs_b)
            loss = policy_loss + 2.0 * value_loss
            loss.backward()
            optimizer.step()
            total_loss_sum += float(loss.item())

        avg_loss = total_loss_sum / len(loader)
        print(log_time(f"  loss: {avg_loss:.4f}"), flush=True)
        save_best(net, cfg.latest_model)
        print(log_time(f"  💾 latest 保存: {Path(cfg.latest_model).name}"), flush=True)

        should_eval = ((it + 1) % cfg.eval_interval) == 0 or (it + 1) == cfg.n_iters

        if should_eval:
            net.eval()
            rate_3k, rate_6k, min_rate = evaluate_dual(net, cfg)

            if min_rate > best_score:
                best_score = min_rate
                save_best(net, cfg.best_model)
                print(log_time(f"  ✅ モデル保存 (min勝率: {best_score * 100:.1f}%)"), flush=True)

            if min_rate >= cfg.win_rate_target:
                print(
                    log_time(
                        f"\n🎉 ゲート条件達成: min勝率 {min_rate * 100:.1f}% "
                        f"(目標: {cfg.win_rate_target * 100:.1f}%)"
                    ),
                    flush=True
                )
                print(log_time("📍 Route B → Phase 3-A に接続可能"), flush=True)
                break

    print(f"{'=' * 70}\n", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AlphaZero-N6K v7→Hybrid ハイブリッド蒸留訓練")
    parser.add_argument("--iters", type=int, default=DistillationConfig.n_iters)
    parser.add_argument("--games", type=int, default=DistillationConfig.games_per_iter)
    parser.add_argument("--sims", type=int, default=DistillationConfig.n_simulations)
    parser.add_argument("--batch-size", type=int, default=DistillationConfig.batch_size)
    parser.add_argument("--lr", type=float, default=DistillationConfig.lr)
    parser.add_argument("--eval-games", type=int, default=DistillationConfig.eval_games)
    parser.add_argument("--eval-interval", type=int, default=DistillationConfig.eval_interval)
    parser.add_argument("--warm-start", type=str, default=DistillationConfig.warm_start)
    parser.add_argument("--target", type=float, default=DistillationConfig.win_rate_target)
    args = parser.parse_args()

    config = DistillationConfig(
        n_iters=args.iters,
        games_per_iter=args.games,
        n_simulations=args.sims,
        batch_size=args.batch_size,
        lr=args.lr,
        eval_games=args.eval_games,
        eval_interval=args.eval_interval,
        warm_start=args.warm_start,
        win_rate_target=args.target,
    )
    main(config)

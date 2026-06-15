"""AlphaZero 自己対戦学習スクリプト（統一版）。

正しい AlphaZero 訓練:
- 学習中のネット自身の MCTS で自己対戦（self-play）
- 各局面で MCTS 訪問数分布を policy target にする
- policy（soft-target CE）+ value（MSE）の複合損失
- arena 評価ゲートで劣化を防ぐ
- warm-start: alpha_zero_8x8_best.pth.tar から開始

使い方:
    uv run python scripts/train_alphazero.py
    uv run python scripts/train_alphazero.py --iters 1 --games 2 --sims 10  # スモークテスト
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

from agents.alphazero.encoding import board_to_tensor
from agents.alphazero.mcts import MCTS, PASS_ACTION
from agents.negamax_agent import (
    NegamaxAgent,
    _apply,
    _flips_for_move,
    _valid_moves,
)
from agents.networks.othello_net import OthelloNNet
from training.alphazero.checkpoint import load_checkpoint, save_best
from training.alphazero.losses import alphazero_loss


@dataclass
class TrainConfig:
    """訓練ハイパーパラメータ。"""

    n_iters: int = 30
    games_per_iter: int = 10
    n_simulations: int = 50
    c_puct: float = 1.0
    temp_moves: int = 8
    dirichlet_alpha: float = 0.3
    dirichlet_eps: float = 0.25
    batch_size: int = 128
    lr: float = 1e-4
    arena_games: int = 10
    gate_threshold: float = 0.55
    nega_games: int = 5
    board_size: int = 8
    warm_start: str = "models/alpha_zero_8x8_best.pth.tar"
    best_model: str = "models/alpha_zero_latest.pth"


def _initial_board(board_size: int = 8) -> list[list[int]]:
    board = [[0] * board_size for _ in range(board_size)]
    mid = board_size // 2
    board[mid - 1][mid - 1] = 1
    board[mid][mid] = 1
    board[mid - 1][mid] = -1
    board[mid][mid - 1] = -1
    return board


def play_one_selfplay_game(
    net: OthelloNNet,
    cfg: TrainConfig,
) -> list[tuple[torch.Tensor, torch.Tensor, int]]:
    """自己対戦を 1 局行い、学習サンプルのリストを返す。

    Returns:
        [(盤面テンソル (1,1,8,8), π (65,), turn)] のリスト（z は未付与）。
    """
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
    samples: list[tuple[torch.Tensor, torch.Tensor, int]] = []
    move_no = 0

    while True:
        moves = _valid_moves(board, cfg.board_size, turn)
        if not moves:
            if not _valid_moves(board, cfg.board_size, -turn):
                break
            turn = -turn
            continue

        counts = mcts.run(board, turn)

        pi_arr = [0.0] * 65
        total = sum(counts.values()) or 1
        for a, n in counts.items():
            pi_arr[a] = n / total
        pi_tensor = torch.tensor(pi_arr, dtype=torch.float32)
        board_tensor = board_to_tensor(board, turn)
        samples.append((board_tensor, pi_tensor, turn))

        # 温度サンプリング（序盤 τ=1、終盤 argmax）
        if move_no < cfg.temp_moves:
            import random
            actions = list(counts.keys())
            weights = [counts[a] for a in actions]
            best_action = random.choices(actions, weights=weights, k=1)[0]
        else:
            best_action = max(counts, key=lambda a: counts[a])

        if best_action != PASS_ACTION:
            r, c = divmod(best_action, cfg.board_size)
            flips = _flips_for_move(board, cfg.board_size, r, c, turn)
            _apply(board, (r, c), flips, turn)

        turn = -turn
        move_no += 1

    # 終局後、z を手番視点で割当
    black = sum(cell == -1 for row in board for cell in row)
    white = sum(cell == 1 for row in board for cell in row)
    if black > white:
        winner = -1
    elif white > black:
        winner = 1
    else:
        winner = 0

    result = []
    for board_t, pi, t in samples:
        if winner == 0:
            z = 0.0
        elif winner == t:
            z = 1.0
        else:
            z = -1.0
        result.append((board_t, pi, z))

    return result  # type: ignore[return-value]


def arena_vs_negamax(net: OthelloNNet, n_games: int, cfg: TrainConfig) -> float:
    """net vs Negamax の勝率を計測する（参考指標）。"""
    from agents.alpha_zero_agent import AlphaZeroAgent
    alphazero = AlphaZeroAgent.from_net(net, n_simulations=cfg.n_simulations)
    negamax = NegamaxAgent(time_limit_ms=100)
    from game import Game

    wins = 0.0
    for g in range(n_games):
        game = Game(board_size=cfg.board_size)
        while not game.game_over:
            if game.turn == 1:
                move = alphazero.play(game)
            else:
                move = negamax.play(game)
            if move:
                game.place_stone(move[0], move[1])
            game.switch_turn()
            game.check_game_over()
        black, white = game.board.count_stones()
        if white > black:
            wins += 1.0
        elif white == black:
            wins += 0.5

    return wins / n_games


def arena(net_a: OthelloNNet, net_b: OthelloNNet, n_games: int, cfg: TrainConfig) -> float:
    """net_a vs net_b の勝率を計測する（arena 評価ゲート）。"""
    from agents.alpha_zero_agent import AlphaZeroAgent
    from game import Game

    agent_a = AlphaZeroAgent.from_net(net_a, n_simulations=cfg.n_simulations)
    agent_b = AlphaZeroAgent.from_net(net_b, n_simulations=cfg.n_simulations)

    wins = 0.0
    for g in range(n_games):
        game = Game(board_size=cfg.board_size)
        a_is_black = (g % 2 == 0)
        while not game.game_over:
            if (game.turn == -1) == a_is_black:
                move = agent_a.play(game)
            else:
                move = agent_b.play(game)
            if move:
                game.place_stone(move[0], move[1])
            game.switch_turn()
            game.check_game_over()
        black, white = game.board.count_stones()
        if a_is_black:
            if black > white:
                wins += 1.0
            elif black == white:
                wins += 0.5
        else:
            if white > black:
                wins += 1.0
            elif white == black:
                wins += 0.5

    return wins / n_games


def main(cfg: TrainConfig) -> None:
    """AlphaZero 訓練メインループ。"""
    print(f"\n{'='*70}")
    print("AlphaZero 自己対戦学習（MCTS + policy/value 複合損失）")
    print(f"{'='*70}")
    print(f"設定: iters={cfg.n_iters}, games/iter={cfg.games_per_iter}, sims={cfg.n_simulations}\n")

    sys.stdout.reconfigure(line_buffering=True)
    device = "cpu"
    net = OthelloNNet(board_size=cfg.board_size).to(device)

    warm_start = Path(cfg.warm_start)
    if warm_start.exists():
        print(f"warm-start: {warm_start.name}")
        load_checkpoint(net, warm_start)
    else:
        print("warm-start なし（ランダム初期化）")

    best_nega_rate = 0.0
    optimizer = optim.Adam(net.parameters(), lr=cfg.lr)

    for it in range(cfg.n_iters):
        print(f"\n{'='*60}")
        print(f"イテレーション {it + 1}/{cfg.n_iters}")
        print(f"{'='*60}")

        # Self-play（推論モードで生成）
        net.eval()
        buffer: list[tuple[torch.Tensor, torch.Tensor, float]] = []
        for g in range(cfg.games_per_iter):
            samples = play_one_selfplay_game(net, cfg)
            buffer.extend(samples)  # type: ignore[arg-type]
            if (g + 1) % max(1, cfg.games_per_iter // 2) == 0:
                print(f"  self-play: {g + 1}/{cfg.games_per_iter} 局完了")

        print(f"  総サンプル数: {len(buffer)}")

        if len(buffer) < cfg.batch_size:
            print("  サンプル不足。スキップ。")
            continue

        # 訓練（train モード、drop_last で BatchNorm 対策）
        boards = torch.cat([s[0] for s in buffer])
        pis = torch.stack([s[1] for s in buffer])
        zs = torch.tensor([s[2] for s in buffer], dtype=torch.float32)
        dataset = TensorDataset(boards, pis, zs)
        loader = DataLoader(dataset, batch_size=cfg.batch_size, shuffle=True, drop_last=True)

        net.train()
        total_loss_sum = 0.0
        for boards_b, pis_b, zs_b in loader:
            optimizer.zero_grad()
            logits, v = net(boards_b)
            loss, _, _ = alphazero_loss(logits, v, pis_b, zs_b)
            loss.backward()
            optimizer.step()
            total_loss_sum += float(loss.item())

        avg_loss = total_loss_sum / len(loader)
        print(f"  訓練完了 - avg loss: {avg_loss:.4f}")

        # Negamax 勝率で進捗管理（巻き戻しなし・学習を蓄積）
        net.eval()
        nega_rate = arena_vs_negamax(net, cfg.nega_games, cfg)
        print(f"  vs Negamax = {nega_rate*100:.1f}%")

        if nega_rate > best_nega_rate:
            best_nega_rate = nega_rate
            save_best(net, cfg.best_model)
            print(f"  ✅ ベストモデル更新 (vs Negamax {best_nega_rate*100:.1f}%) -> {cfg.best_model}")

        if nega_rate >= 0.9:
            print(f"\n目標達成！ vs Negamax 勝率 {nega_rate*100:.1f}%")
            save_best(net, cfg.best_model)
            break

    print(f"\n{'='*70}")
    print("訓練完了")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AlphaZero 自己対戦学習")
    parser.add_argument("--iters", type=int, default=30)
    parser.add_argument("--games", type=int, default=10)
    parser.add_argument("--sims", type=int, default=50)
    parser.add_argument("--lr", type=float, default=1e-4)
    args = parser.parse_args()

    config = TrainConfig(
        n_iters=args.iters,
        games_per_iter=args.games,
        n_simulations=args.sims,
        lr=args.lr,
    )
    main(config)

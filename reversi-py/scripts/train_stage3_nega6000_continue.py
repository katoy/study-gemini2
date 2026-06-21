"""AlphaZero-N6K 継続訓練スクリプト（石差最大化版）。

alpha_zero_nega6000.pth から継続訓練し、石差をより大きく勝てるモデルを目指す。
n_simulations=50, c_puct=1.5, temp_moves=5, games_per_iter=16 で最適化。
結果は models/alpha_zero_nega6000_v2.pth に保存される。
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

from agents.alphazero.encoding import board_to_tensor
from agents.alphazero.mcts import MCTS, PASS_ACTION
from agents.negamax_agent import NegamaxAgent, _apply, _flips_for_move, _valid_moves
from agents.networks.othello_net import OthelloNNet
from training.alphazero.checkpoint import load_checkpoint, save_best
from training.alphazero.losses import alphazero_loss


@dataclass
class TrainConfig:
    n_iters: int = 100           # 80 → 100
    games_per_iter: int = 16     # 8 → 16（サンプル倍増）
    n_simulations: int = 50      # 30 → 50（読みを深く）
    c_puct: float = 1.5          # 1.0 → 1.5（広い探索）
    temp_moves: int = 5          # 8 → 5（確定的な手を早める）
    dirichlet_alpha: float = 0.3
    dirichlet_eps: float = 0.25
    batch_size: int = 256        # 128 → 256
    lr: float = 5e-5             # 1e-4 → 5e-5（継続訓練用）
    eval_games: int = 15
    board_size: int = 8
    warm_start: str = "models/alpha_zero_nega6000.pth"      # 現在の最良モデルから継続
    best_model: str = "models/alpha_zero_nega6000_v2.pth"   # 新しい保存先


def _initial_board(board_size: int = 8) -> list[list[int]]:
    board = [[0] * board_size for _ in range(board_size)]
    mid = board_size // 2
    board[mid - 1][mid - 1] = 1
    board[mid][mid] = 1
    board[mid - 1][mid] = -1
    board[mid][mid - 1] = -1
    return board


def play_one_selfplay_game(net: OthelloNNet, cfg: TrainConfig) -> list[tuple[torch.Tensor, torch.Tensor, float]]:
    mcts = MCTS(net=net, n_simulations=cfg.n_simulations, c_puct=cfg.c_puct, board_size=cfg.board_size, dirichlet_alpha=cfg.dirichlet_alpha, dirichlet_eps=cfg.dirichlet_eps)
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

    return result


def evaluate_vs_negamax(net: OthelloNNet, n_games: int, cfg: TrainConfig) -> float:
    from agents.alpha_zero_agent import AlphaZeroAgent
    from game import Game

    alpha_zero = AlphaZeroAgent.from_net(net, n_simulations=cfg.n_simulations)
    negamax = NegamaxAgent(time_limit_ms=6000)

    wins = 0.0
    for g in range(n_games):
        game = Game(board_size=cfg.board_size)
        az_is_white = (g % 2 == 0)

        while not game.game_over:
            if (game.turn == 1) == az_is_white:
                move = alpha_zero.play(game)
            else:
                move = negamax.play(game)

            if move:
                game.place_stone(move[0], move[1])
            game.switch_turn()
            game.check_game_over()

        black, white = game.board.count_stones()
        if az_is_white:
            if white > black:
                wins += 1.0
        else:
            if black > white:
                wins += 1.0

    return wins / n_games


def main(cfg: TrainConfig) -> None:
    print(f"\n{'='*70}")
    print("フェーズ 2: Negamax(6000ms) で fine-tune")
    print(f"{'='*70}\n")

    import io
    if isinstance(sys.stdout, io.TextIOBase):
        sys.stdout.reconfigure(line_buffering=True)  # type: ignore
    device = "cpu"
    net = OthelloNNet(board_size=cfg.board_size).to(device)

    warm_start = Path(cfg.warm_start)
    if warm_start.exists():
        print(f"warm-start: {warm_start.name}")
        load_checkpoint(net, warm_start)
    else:
        print("warm-start パスが見つかりません")

    optimizer = optim.Adam(net.parameters(), lr=cfg.lr)
    best_rate = 0.0

    for it in range(cfg.n_iters):
        print(f"\nイテレーション {it + 1}/{cfg.n_iters}")

        net.eval()
        buffer: list[tuple[torch.Tensor, torch.Tensor, float]] = []
        for g in range(cfg.games_per_iter):
            samples = play_one_selfplay_game(net, cfg)
            buffer.extend(samples)

        print(f"  サンプル: {len(buffer)}")

        if len(buffer) < cfg.batch_size:
            continue

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
        print(f"  loss: {avg_loss:.4f}")

        net.eval()
        rate = evaluate_vs_negamax(net, cfg.eval_games, cfg)
        print(f"  vs Negamax(6000ms): {rate*100:.1f}%")

        if rate > best_rate:
            best_rate = rate
            save_best(net, cfg.best_model)
            print("  ✅ モデル保存")

        if rate >= 0.95:
            print(f"\n🎉 目標達成: {rate*100:.1f}%")
            break

    print(f"{'='*70}\n")


if __name__ == "__main__":
    config = TrainConfig()
    main(config)

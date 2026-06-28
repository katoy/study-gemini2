"""AlphaZero-N6K 追加訓練スクリプト（Negamax-3K / 6K 両対応版）。

alpha_zero_nega6000_v6_improved_loss.pth を warm start にして継続訓練し、
Negamax-3K と Negamax-6K の両方に対して勝率 95% 以上を目指す。

このスクリプトは「片方だけ強い」モデルを避けるため、評価時は
3K/6K のどちらも測定し、両方が目標を超えたときだけ終了する。
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# PyTorch パフォーマンス最適化
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
torch.backends.mps.is_available = lambda: False
n_threads = int(os.cpu_count() or 4)
torch.set_num_threads(n_threads)
torch.set_num_interop_threads(1)
torch.set_float32_matmul_precision("high")
torch.backends.mkldnn.enabled = True

from agents.alphazero.encoding import board_to_tensor  # noqa: E402
from agents.alphazero.mcts import MCTS, PASS_ACTION  # noqa: E402
from agents.networks.othello_net import OthelloNNet  # noqa: E402
from agents.negamax_agent import NegamaxAgent, _apply, _flips_for_move, _valid_moves  # noqa: E402
from agents.alpha_zero_agent import AlphaZeroAgent  # noqa: E402
from game import Game  # noqa: E402
from training.alphazero.checkpoint import load_checkpoint, save_best  # noqa: E402
from training.alphazero.losses import alphazero_loss  # noqa: E402

NEGAMAX_VARIANTS = {
    "negamax_3k": 3000,
    "negamax_6k": 6000,
}


@dataclass
class TrainConfig:
    n_iters: int = 200
    games_per_iter: int = 16
    n_simulations: int = 100
    c_puct: float = 1.5
    temp_moves: int = 3
    dirichlet_alpha: float = 0.3
    dirichlet_eps: float = 0.25
    batch_size: int = 256
    lr: float = 1e-4
    eval_games: int = 15
    board_size: int = 8
    warm_start: str = "models/alpha_zero_nega6000_v6_improved_loss.pth"
    best_model: str = "models/alpha_zero_nega6000_v7_dual_negamax.pth"
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


def evaluate_against_negamax(
    net: OthelloNNet,
    n_games: int,
    cfg: TrainConfig,
    time_limit_ms: int,
) -> float:
    alpha_zero = AlphaZeroAgent.from_net(net, n_simulations=cfg.n_simulations)
    negamax = NegamaxAgent(time_limit_ms=time_limit_ms)

    wins = 0.0
    for game_index in range(n_games):
        game = Game(board_size=cfg.board_size)
        az_is_white = game_index % 2 == 0

        while not game.game_over:
            if (game.turn == 1) == az_is_white:
                move = alpha_zero.play(game)
            else:
                move = negamax.play(game)

            if move is not None:
                game.place_stone(move[0], move[1])
            game.switch_turn()
            game.check_game_over()

        black, white = game.board.count_stones()
        if az_is_white and white > black:
            wins += 1.0
        if not az_is_white and black > white:
            wins += 1.0

    return wins / n_games


def evaluate_vs_dual_negamax(
    net: OthelloNNet, n_games: int, cfg: TrainConfig
) -> dict[str, float]:
    return {
        name: evaluate_against_negamax(net, n_games, cfg, time_limit_ms)
        for name, time_limit_ms in NEGAMAX_VARIANTS.items()
    }


def dual_negamax_score(rates: dict[str, float]) -> float:
    return min(rates.values()) if rates else 0.0


def dual_negamax_target_met(
    rates: dict[str, float], target: float
) -> bool:
    return all(rate >= target for rate in rates.values())


def main(cfg: TrainConfig) -> None:
    print(f"\n{'=' * 70}")
    print("AlphaZero-N6K 追加訓練")
    print("目標: Negamax-3K / Negamax-6K の両方に対して 95% 以上")
    print(f"{'=' * 70}\n")

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
    best_score = 0.0

    for it in range(cfg.n_iters):
        print(f"\nイテレーション {it + 1}/{cfg.n_iters}")

        net.eval()
        buffer: list[tuple[torch.Tensor, torch.Tensor, float]] = []
        for _ in range(cfg.games_per_iter):
            buffer.extend(play_one_selfplay_game(net, cfg))

        print(f"  サンプル: {len(buffer)}")

        if len(buffer) < cfg.batch_size:
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
        print(f"  loss: {avg_loss:.4f}")

        net.eval()
        rates = evaluate_vs_dual_negamax(net, cfg.eval_games, cfg)
        print(
            "  vs Negamax-3K: "
            f"{rates['negamax_3k'] * 100:.1f}%"
        )
        print(
            "  vs Negamax-6K: "
            f"{rates['negamax_6k'] * 100:.1f}%"
        )

        score = dual_negamax_score(rates)
        if score > best_score:
            best_score = score
            save_best(net, cfg.best_model)
            print(f"  ✅ モデル保存 (min勝率: {best_score * 100:.1f}%)")

        if dual_negamax_target_met(rates, cfg.win_rate_target):
            print(
                "\n🎉 目標達成: "
                f"3K={rates['negamax_3k'] * 100:.1f}% "
                f"6K={rates['negamax_6k'] * 100:.1f}%"
            )
            break

    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    config = TrainConfig()
    main(config)

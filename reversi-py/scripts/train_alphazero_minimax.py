"""AlphaZero を Minimax/Negamax エージェントに対し勝率 80% 超まで訓練するスクリプト。

Stage 0: ベースライン選定（既定は alpha_zero_nega6000_v8.pth）
Stage 1A: 大規模オフライン教師事前学習（64-bit BitboardTeacher + 対 Minimax 混合対局 + D4 拡張）
Stage 1B: 対 Minimax/Negamax 標的型 DAgger（敗着/訪問局面の集中的矯正）
Stage 2: 安定化並列自己対戦 AlphaZero RL（適正バッファ + 低温探索 + MPS GPU 学習）
Stage 3: 50 局ペア評価（sims=200, endgame_empties=0）による公式認定
"""
from __future__ import annotations

import argparse
import io
import math
import multiprocessing
import os
import random
import sys
import time
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import torch
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from agents.alphazero.mcts import MCTS, PASS_ACTION
from agents.base_agent import Agent
from agents.minimax_agent import MinimaxAgent
from agents.negamax_agent import (
    NegamaxAgent,
    _apply,
    _flips_for_move,
    _valid_moves,
)
from agents.networks.othello_net import OthelloNNet
from agents.transposition_negamax_agent import TranspositionNegamaxAgent
from game import Game
from training.alphazero.augmentation import augment_batch_d4
from training.alphazero.bitboard_teacher import BitboardTeacherAgent
from training.alphazero.checkpoint import load_checkpoint, save_best
from training.alphazero.evaluation import EvalResult, evaluate_against_agent
from training.alphazero.losses import alphazero_loss
from training.alphazero.replay_buffer import ReplayBuffer

DEFAULT_WARM_START_CANDIDATES = (
    "models/alpha_zero_all90plus.pth",
    "models/alpha_zero_nega6000_v7_dual_negamax.pth",
    "models/alpha_zero_nega6000_v8.pth",
)


@dataclass
class HybridTrainConfig:
    """3 段階ハイブリッド訓練（Stage 1A 事前蒸留 → Stage 1B 標的 DAgger → Stage 2 RL）設定。"""

    dropout: float = 0.1
    label_smoothing: float = 0.05
    pretrain_games: int = 400
    pretrain_teacher_ms: int = 120
    pretrain_epochs: int = 30
    pretrain_lr: float = 5e-4
    pretrain_min_lr: float = 5e-5
    pretrain_cache: str = "data/bitboard_pretrain_400g.npz"
    rebuild_pretrain: bool = False
    stage1_iters: int = 8
    dagger_games: int = 40
    dagger_sims: int = 80
    dagger_temp_moves: int = 6
    teacher_time_limit_ms: int = 250
    stage1_lr: float = 1.5e-4
    stage1_min_lr: float = 3e-5
    stage1_epochs: int = 6
    stage2_iters: int = 10
    selfplay_games: int = 32
    selfplay_sims: int = 150
    c_puct: float = 1.5
    selfplay_temp_moves: int = 4
    dirichlet_alpha: float = 0.3
    dirichlet_eps: float = 0.20
    stage2_lr: float = 2e-5
    stage2_min_lr: float = 5e-6
    stage2_epochs: int = 5
    batch_size: int = 256
    value_loss_weight: float = 1.0
    buffer_capacity: int = 45_000
    stage2_keep_distill: int = 25_000
    eval_games: int = 20
    eval_sims: int = 200
    eval_interval: int = 2
    cert_games: int = 50
    eval_seed: int = 42
    opening_random_plies: int = 4
    opponent: str = "minimax"
    opponent_time_limit_ms: int = 500
    stage1_promote_rate: float = 0.85
    screen_cert_trigger: float = 0.85
    win_rate_target: float = 0.80
    patience: int = 4
    workers: int = 8
    device: str = "auto"
    board_size: int = 8
    warm_start: str = "models/alpha_zero_nega6000_v8.pth"
    best_model: str = "models/alpha_zero_minimax80_best.pth"
    latest_model: str = "models/alpha_zero_minimax80_latest.pth"
    force_train: bool = False
    log_file: str = ""


class DualLogger:
    """標準出力とログファイル（指定時）の双方へ出力するロガー。"""

    def __init__(self, log_path: str = "") -> None:
        self._file = None
        if log_path:
            path = Path(log_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            self._file = open(path, "a", encoding="utf-8", buffering=1)

    def log(self, message: str) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        line = f"[{now}] {message}"
        print(line, flush=True)
        if self._file is not None:
            self._file.write(line + "\n")
            self._file.flush()

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None


def _initial_board(board_size: int = 8) -> list[list[int]]:
    board = [[0] * board_size for _ in range(board_size)]
    mid = board_size // 2
    board[mid - 1][mid - 1] = 1
    board[mid][mid] = 1
    board[mid - 1][mid] = -1
    board[mid][mid - 1] = -1
    return board


def board_to_perspective_int8(board: list[list[int]], turn: int) -> np.ndarray:
    """盤面を手番視点の (H, W) int8 配列（自分=+1, 相手=-1, 空=0）に変換する。"""
    arr = np.asarray(board, dtype=np.int8)
    return (arr * turn).astype(np.int8)


def make_smoothed_policy(
    moves: list[tuple[int, int]],
    best_move: tuple[int, int],
    board_size: int = 8,
    label_smoothing: float = 0.05,
) -> np.ndarray:
    """教師の最善手に対しラベル平滑化を施した正規化済み方策ベクトルを返す。"""
    if not moves:
        raise ValueError("moves must not be empty")
    pi = np.zeros(board_size * board_size + 1, dtype=np.float32)
    if len(moves) == 1 or best_move not in moves:
        target = best_move if best_move in moves else moves[0]
        pi[target[0] * board_size + target[1]] = 1.0
        return pi

    best_idx = best_move[0] * board_size + best_move[1]
    other_prob = label_smoothing / (len(moves) - 1)
    for r, c in moves:
        idx = r * board_size + c
        pi[idx] = (1.0 - label_smoothing) if idx == best_idx else other_prob
    return pi


def score_to_value(score: float, z_game: float) -> float:
    """教師の探索評価値と終局勝敗から低分散の Value ターゲット [-1, +1] を生成する。"""
    if abs(score) >= 10000.0:
        return 1.0 if score > 0 else -1.0
    if score != 0.0:
        return 0.5 * z_game + 0.5 * math.tanh(score / 150.0)
    return z_game


def _query_teacher(
    teacher: Agent, game: Game
) -> tuple[tuple[int, int] | None, float]:
    """教師から (最善手, 評価値) を取得する（play_with_score 非実装時は 0.0）。"""
    if isinstance(teacher, (BitboardTeacherAgent, TranspositionNegamaxAgent)):
        return teacher.play_with_score(game)
    return teacher.play(game), 0.0


def play_teacher_pretrain_game(
    cfg: HybridTrainConfig,
    seed: int | None = None,
    vs_opponent: bool = False,
    teacher_agent: Agent | None = None,
    opponent_agent: Agent | None = None,
) -> list[tuple[np.ndarray, np.ndarray, float]]:
    """教師対局（自己対戦または対目標相手混合・4〜6手ランダム開口）から教師データを生成する。"""
    rng = random.Random(seed)
    game = Game(board_size=cfg.board_size)
    opening_plies = rng.randint(4, 6)

    for _ in range(opening_plies):
        if game.game_over:
            break
        valid = game.get_valid_moves()
        if not valid:
            game.switch_turn()
            valid = game.get_valid_moves()
        if not valid:
            break
        mv = rng.choice(valid)
        game.place_stone(mv[0], mv[1])
        game.switch_turn()
        game.check_game_over()

    teacher: Agent = (
        teacher_agent
        if teacher_agent is not None
        else BitboardTeacherAgent(time_limit_ms=cfg.pretrain_teacher_ms)
    )
    opponent: Agent | None = None
    teacher_turn = 1 if (seed is not None and seed % 2 == 0) else -1
    if vs_opponent:
        opponent = (
            opponent_agent
            if opponent_agent is not None
            else build_opponent_factory(cfg)()
        )

    records: list[tuple[np.ndarray, np.ndarray, int, float]] = []
    move_no = 0

    while not game.game_over:
        valid = game.get_valid_moves()
        if not valid:
            game.switch_turn()
            game.check_game_over()
            continue

        if vs_opponent and opponent is not None:
            board_persp = board_to_perspective_int8(game.board.board, game.turn)
            teacher_mv, score = _query_teacher(teacher, game)
            if teacher_mv is not None:
                pi_arr = make_smoothed_policy(
                    valid, teacher_mv, cfg.board_size, cfg.label_smoothing
                )
                records.append((board_persp, pi_arr, game.turn, score))
            if game.turn == teacher_turn:
                chosen = teacher_mv if teacher_mv is not None else valid[0]
            else:
                opp_mv = opponent.play(game)
                chosen = opp_mv if (opp_mv is not None and opp_mv in valid) else valid[0]
        elif move_no < 12 and rng.random() < 0.12:
            chosen = rng.choice(valid)
        else:
            board_persp = board_to_perspective_int8(game.board.board, game.turn)
            chosen_mv, score = _query_teacher(teacher, game)
            if chosen_mv is None:
                chosen = valid[0]
            else:
                chosen = chosen_mv
                pi_arr = make_smoothed_policy(
                    valid, chosen, cfg.board_size, cfg.label_smoothing
                )
                records.append((board_persp, pi_arr, game.turn, score))

        game.place_stone(chosen[0], chosen[1])
        game.switch_turn()
        game.check_game_over()
        move_no += 1

    winner = game.get_winner()
    result: list[tuple[np.ndarray, np.ndarray, float]] = []
    for board_p, pi_arr, turn, score in records:
        z_game = 0.0 if winner == 0 else (1.0 if winner == turn else -1.0)
        result.append((board_p, pi_arr, score_to_value(score, z_game)))
    return result


def play_dagger_game(
    net: OthelloNNet,
    cfg: HybridTrainConfig,
    az_is_white: bool,
    seed: int | None = None,
    teacher_agent: Agent | None = None,
    opponent_agent: Agent | None = None,
) -> list[tuple[np.ndarray, np.ndarray, float]]:
    """対目標相手（Minimax/Negamax）の標的型 DAgger 1 局を実行する。

    AlphaZero 手番は常に教師ラベルを記録し、敗戦・引き分け時は相手手番の局面も含めて
    教師ラベルを回収することで、弱点局面を集中的に補強する。
    """
    rng = random.Random(seed)
    game = Game(board_size=cfg.board_size)

    for _ in range(cfg.opening_random_plies):
        if game.game_over:
            break
        valid = game.get_valid_moves()
        if not valid:
            game.switch_turn()
            valid = game.get_valid_moves()
        if not valid:
            break
        mv = rng.choice(valid)
        game.place_stone(mv[0], mv[1])
        game.switch_turn()
        game.check_game_over()

    teacher: Agent = (
        teacher_agent
        if teacher_agent is not None
        else BitboardTeacherAgent(time_limit_ms=cfg.teacher_time_limit_ms)
    )
    opponent: Agent = (
        opponent_agent
        if opponent_agent is not None
        else build_opponent_factory(cfg)()
    )
    mcts = MCTS(
        net=net,
        n_simulations=cfg.dagger_sims,
        c_puct=1.25,
        board_size=cfg.board_size,
    )

    az_records: list[tuple[np.ndarray, np.ndarray, int, float]] = []
    opp_records: list[tuple[np.ndarray, np.ndarray, int, float]] = []
    move_no = 0

    while not game.game_over:
        valid = game.get_valid_moves()
        if not valid:
            game.switch_turn()
            game.check_game_over()
            continue

        board_persp = board_to_perspective_int8(game.board.board, game.turn)
        az_turn = (game.turn == 1) == az_is_white

        if az_turn:
            counts = mcts.run(game.board.board, game.turn)
            legal_actions = [r * cfg.board_size + c for r, c in valid]
            weights = [max(0, counts.get(a, 0)) for a in legal_actions]
            if move_no < cfg.dagger_temp_moves and sum(weights) > 0:
                best_action = rng.choices(legal_actions, weights=weights, k=1)[0]
            else:
                best_action = max(legal_actions, key=lambda a: counts.get(a, 0))
            chosen_move: tuple[int, int] | None = divmod(best_action, cfg.board_size)
            teacher_move, score = _query_teacher(teacher, game)
            if teacher_move is not None:
                pi_arr = make_smoothed_policy(
                    valid, teacher_move, cfg.board_size, cfg.label_smoothing
                )
                az_records.append((board_persp, pi_arr, game.turn, score))
        else:
            chosen_move = opponent.play(game)
            teacher_move, score = _query_teacher(teacher, game)
            if teacher_move is not None:
                pi_arr = make_smoothed_policy(
                    valid, teacher_move, cfg.board_size, cfg.label_smoothing
                )
                opp_records.append((board_persp, pi_arr, game.turn, score))

        if chosen_move is not None:
            game.place_stone(chosen_move[0], chosen_move[1])
        game.switch_turn()
        game.check_game_over()
        move_no += 1

    winner = game.get_winner()
    az_color = 1 if az_is_white else -1
    az_won = winner == az_color
    selected = az_records if az_won else (az_records + opp_records)

    result: list[tuple[np.ndarray, np.ndarray, float]] = []
    for board_p, pi_arr, turn, score in selected:
        z_game = 0.0 if winner == 0 else (1.0 if winner == turn else -1.0)
        result.append((board_p, pi_arr, score_to_value(score, z_game)))
    return result


def play_selfplay_game(
    net: OthelloNNet,
    cfg: HybridTrainConfig,
    seed: int | None = None,
) -> list[tuple[np.ndarray, np.ndarray, float]]:
    """MCTS 自己対戦 1 局を実行し、サンプル列（z ∈ {-1, 0, +1}）を返す。"""
    rng = random.Random(seed)
    if seed is not None:
        np.random.seed(seed % (2**31 - 1))

    mcts = MCTS(
        net=net,
        n_simulations=cfg.selfplay_sims,
        c_puct=cfg.c_puct,
        board_size=cfg.board_size,
        dirichlet_alpha=cfg.dirichlet_alpha,
        dirichlet_eps=cfg.dirichlet_eps,
    )

    board = _initial_board(cfg.board_size)
    turn = -1
    records: list[tuple[np.ndarray, np.ndarray, int]] = []
    move_no = 0
    action_size = cfg.board_size * cfg.board_size + 1

    while True:
        moves = _valid_moves(board, cfg.board_size, turn)
        if not moves:
            if not _valid_moves(board, cfg.board_size, -turn):
                break
            turn = -turn
            continue

        counts = mcts.run(board, turn)
        pi_arr = np.zeros(action_size, dtype=np.float32)
        total = sum(counts.values()) or 1
        for action, visits in counts.items():
            if 0 <= action < action_size:
                pi_arr[action] = visits / total

        records.append((board_to_perspective_int8(board, turn), pi_arr, turn))

        actions = list(counts.keys())
        if move_no < cfg.selfplay_temp_moves:
            weights = [max(0, counts[a]) for a in actions]
            if sum(weights) > 0:
                best_action = rng.choices(actions, weights=weights, k=1)[0]
            else:
                best_action = rng.choice(actions)
        else:
            best_action = max(actions, key=lambda a: counts[a])

        if best_action != PASS_ACTION:
            row, col = divmod(best_action, cfg.board_size)
            flips = _flips_for_move(board, cfg.board_size, row, col, turn)
            _apply(board, (row, col), flips, turn)

        turn = -turn
        move_no += 1

    black = sum(cell == -1 for row in board for cell in row)
    white = sum(cell == 1 for row in board for cell in row)
    winner = -1 if black > white else (1 if white > black else 0)

    result: list[tuple[np.ndarray, np.ndarray, float]] = []
    for board_p, pi_arr, t in records:
        z = 0.0 if winner == 0 else (1.0 if winner == t else -1.0)
        result.append((board_p, pi_arr, z))
    return result


def _worker_init() -> None:
    """並列ワーカー起動時の初期化（各ワーカーは CPU 1 スレッド固定）。"""
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    torch.set_num_threads(1)


def _pretrain_game_worker(
    task: tuple[HybridTrainConfig, int, bool],
) -> list[tuple[np.ndarray, np.ndarray, float]]:
    cfg, seed, vs_opponent = task
    if vs_opponent and cfg.pretrain_teacher_ms >= 100:
        worker_cfg = replace(cfg, pretrain_teacher_ms=max(cfg.pretrain_teacher_ms, 150))
    else:
        worker_cfg = cfg
    return play_teacher_pretrain_game(worker_cfg, seed=seed, vs_opponent=vs_opponent)


def _dagger_game_worker(
    task: tuple[dict[str, torch.Tensor], HybridTrainConfig, bool, int],
) -> list[tuple[np.ndarray, np.ndarray, float]]:
    state_dict, cfg, az_is_white, seed = task
    net = OthelloNNet(board_size=cfg.board_size, dropout=cfg.dropout)
    net.load_state_dict(state_dict)
    net.eval()
    return play_dagger_game(net, cfg, az_is_white=az_is_white, seed=seed)


def _selfplay_game_worker(
    task: tuple[dict[str, torch.Tensor], HybridTrainConfig, int],
) -> list[tuple[np.ndarray, np.ndarray, float]]:
    state_dict, cfg, seed = task
    net = OthelloNNet(board_size=cfg.board_size, dropout=cfg.dropout)
    net.load_state_dict(state_dict)
    net.eval()
    return play_selfplay_game(net, cfg, seed=seed)


def collect_pretrain_samples(
    cfg: HybridTrainConfig,
    logger: DualLogger,
) -> list[tuple[np.ndarray, np.ndarray, float]]:
    """事前蒸留用の教師対局データを生成またはキャッシュから読み込む。"""
    cache_path = Path(cfg.pretrain_cache) if cfg.pretrain_cache else None
    if cache_path is not None and not cfg.rebuild_pretrain and cache_path.exists():
        data = np.load(cache_path)
        boards = data["boards"]
        pis = data["pis"]
        zs = data["zs"]
        samples = [
            (boards[i], pis[i], float(zs[i])) for i in range(boards.shape[0])
        ]
        logger.log(f"Stage 1A: キャッシュ読込 {cache_path} ({len(samples)} 局面)")
        return samples

    t0 = time.perf_counter()
    half = cfg.pretrain_games // 2
    tasks = [(cfg, 70_000 + i, i >= half) for i in range(cfg.pretrain_games)]
    all_samples: list[tuple[np.ndarray, np.ndarray, float]] = []
    if cfg.workers <= 1:
        for task in tasks:
            all_samples.extend(_pretrain_game_worker(task))
    else:
        ctx = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(
            max_workers=cfg.workers, mp_context=ctx, initializer=_worker_init
        ) as pool:
            for game_samples in pool.map(_pretrain_game_worker, tasks):
                all_samples.extend(game_samples)

    if cache_path is not None and all_samples:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            cache_path,
            boards=np.stack([s[0] for s in all_samples], axis=0),
            pis=np.stack([s[1] for s in all_samples], axis=0),
            zs=np.asarray([s[2] for s in all_samples], dtype=np.float32),
        )
        logger.log(
            f"Stage 1A: 教師データ {cfg.pretrain_games} 局 / {len(all_samples)} 局面生成・保存 "
            f"-> {cache_path} ({time.perf_counter() - t0:.1f}s)"
        )
    return all_samples


def collect_dagger_games(
    net: OthelloNNet,
    cfg: HybridTrainConfig,
    seed_base: int,
) -> list[tuple[np.ndarray, np.ndarray, float]]:
    """DAgger 対局群を並列（workers <= 1 時は逐次）で収集する。"""
    cpu_state = {k: v.detach().cpu() for k, v in net.state_dict().items()}
    tasks = [
        (cpu_state, cfg, (i % 2 == 0), seed_base + i)
        for i in range(cfg.dagger_games)
    ]
    all_samples: list[tuple[np.ndarray, np.ndarray, float]] = []
    if cfg.workers <= 1:
        for task in tasks:
            all_samples.extend(_dagger_game_worker(task))
        return all_samples

    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(
        max_workers=cfg.workers, mp_context=ctx, initializer=_worker_init
    ) as pool:
        for game_samples in pool.map(_dagger_game_worker, tasks):
            all_samples.extend(game_samples)
    return all_samples


def collect_selfplay_games(
    net: OthelloNNet,
    cfg: HybridTrainConfig,
    seed_base: int,
) -> list[tuple[np.ndarray, np.ndarray, float]]:
    """自己対戦群を並列（workers <= 1 時は逐次）で収集する。"""
    cpu_state = {k: v.detach().cpu() for k, v in net.state_dict().items()}
    tasks = [(cpu_state, cfg, seed_base + i) for i in range(cfg.selfplay_games)]
    all_samples: list[tuple[np.ndarray, np.ndarray, float]] = []
    if cfg.workers <= 1:
        for task in tasks:
            all_samples.extend(_selfplay_game_worker(task))
        return all_samples

    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(
        max_workers=cfg.workers, mp_context=ctx, initializer=_worker_init
    ) as pool:
        for game_samples in pool.map(_selfplay_game_worker, tasks):
            all_samples.extend(game_samples)
    return all_samples


def select_device(requested: str) -> str:
    """学習用デバイスを決定する。"""
    if requested != "auto":
        return requested
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def evaluate_policy_top1(
    net: OthelloNNet,
    boards: torch.Tensor,
    pis: torch.Tensor,
    device: str,
    max_samples: int = 2048,
) -> float:
    """バッファ標本に対する合法手マスク済み top-1 一致率（eval モード）を返す。"""
    n = min(boards.size(0), max_samples)
    if n == 0:
        return 0.0
    net.to(device)
    net.eval()
    bx = boards[:n].to(device)
    px = pis[:n].to(device)
    legal_mask = (px > 0.0)
    with torch.no_grad():
        logits, _ = net(bx)
        masked_logits = logits.masked_fill(~legal_mask, -1e9)
        pred = masked_logits.argmax(dim=1)
        target = px.argmax(dim=1)
        acc = float((pred == target).float().mean().item())
    net.to("cpu")
    return acc


def train_on_buffer(
    net: OthelloNNet,
    optimizer: optim.Optimizer,
    replay_buffer: ReplayBuffer,
    *,
    batch_size: int,
    epochs: int,
    device: str,
    value_loss_weight: float = 1.0,
) -> tuple[float, float, float]:
    """ReplayBuffer から D4 拡張ミニバッチを生成し勾配更新する。"""
    boards, pis, zs = replay_buffer.to_tensors()
    if boards.size(0) < batch_size:
        return 0.0, 0.0, 0.0

    dataset = TensorDataset(boards, pis, zs)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, drop_last=True)

    net.to(device)
    net.train()
    total_loss_sum = 0.0
    policy_loss_sum = 0.0
    value_loss_sum = 0.0
    steps = 0

    for _ in range(epochs):
        for boards_b, pis_b, zs_b in loader:
            boards_b, pis_b = augment_batch_d4(boards_b, pis_b)
            boards_b = boards_b.to(device)
            pis_b = pis_b.to(device)
            zs_b = zs_b.to(device)

            optimizer.zero_grad()
            logits, v = net(boards_b)
            _, p_loss, v_loss = alphazero_loss(logits, v, pis_b, zs_b)
            loss = p_loss + value_loss_weight * v_loss

            if not math.isfinite(float(loss.item())):
                net.to("cpu")
                net.eval()
                raise RuntimeError(f"Non-finite loss encountered on device={device}")

            loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), max_norm=1.0)
            optimizer.step()

            total_loss_sum += float(loss.item())
            policy_loss_sum += float(p_loss.item())
            value_loss_sum += float(v_loss.item())
            steps += 1

    net.to("cpu")
    net.eval()
    denom = max(1, steps)
    return total_loss_sum / denom, policy_loss_sum / denom, value_loss_sum / denom


def build_opponent_factory(cfg: HybridTrainConfig) -> Callable[[], Agent]:
    """評価対戦相手ファクトリを構築する。"""
    if cfg.opponent == "minimax":
        return lambda: MinimaxAgent(time_limit_ms=cfg.opponent_time_limit_ms)
    if cfg.opponent == "negamax":
        return lambda: NegamaxAgent(time_limit_ms=cfg.opponent_time_limit_ms)
    raise ValueError(f"Unsupported opponent: {cfg.opponent}")


def is_better_eval(
    cand_rate: float, cand_diff: float, best_rate: float, best_diff: float
) -> bool:
    """勝率優先・同率時は平均石差で改善を判定する。"""
    return (cand_rate > best_rate) or (cand_rate == best_rate and cand_diff > best_diff)


def should_trigger_certification(eval_res: EvalResult, cfg: HybridTrainConfig) -> bool:
    """スクリーニング結果から 50 局公式認定を実行すべきか判定する。"""
    return eval_res.win_rate >= cfg.screen_cert_trigger or (
        eval_res.win_rate > cfg.win_rate_target and eval_res.mean_stone_diff > 0.0
    )


def certification_passed(eval_res: EvalResult, target: float) -> bool:
    """目標勝率（厳密超過 > target）を達成したか判定する。"""
    return eval_res.win_rate > target


def _evaluate_model(
    net: OthelloNNet, cfg: HybridTrainConfig, n_games: int, seed: int
) -> EvalResult:
    """メインプロセス単独で純粋 NN+MCTS（endgame_empties=0）評価を実行する。"""
    net.to("cpu")
    net.eval()
    return evaluate_against_agent(
        net,
        build_opponent_factory(cfg),
        n_games=n_games,
        n_simulations=cfg.eval_sims,
        endgame_empties=0,
        opening_random_plies=cfg.opening_random_plies,
        seed=seed,
        board_size=cfg.board_size,
    )


def _format_eval(res: EvalResult) -> str:
    lo, hi = res.wilson_ci()
    return (
        f"win_rate={res.win_rate * 100:.1f}% ({res.wins}W-{res.draws}D-{res.losses}L), "
        f"stone_diff={res.mean_stone_diff:+.2f}, 95%CI=[{lo * 100:.1f}%, {hi * 100:.1f}%]"
    )


def _run_stage0_baseline(
    net: OthelloNNet, cfg: HybridTrainConfig, logger: DualLogger
) -> tuple[float, float, EvalResult | None]:
    """Stage 0: 候補モデルを比較（または単一指定を評価）し初期ベースラインを返す。"""
    if cfg.warm_start == "auto":
        candidates = [Path(p) for p in DEFAULT_WARM_START_CANDIDATES if Path(p).exists()]
    else:
        path = Path(cfg.warm_start)
        candidates = [path] if path.exists() else []

    if not candidates:
        logger.log("Stage 0: warm-start モデルが見つからないためランダム初期化から開始します")
        res = _evaluate_model(net, cfg, cfg.eval_games, cfg.eval_seed)
        logger.log(f"Stage 0 初期評価: {_format_eval(res)}")
        save_best(net, cfg.best_model)
        return res.win_rate, res.mean_stone_diff, res

    best_path = candidates[0]
    best_rate = -1.0
    best_diff = -1e9
    best_res: EvalResult | None = None

    for cand in candidates:
        cand_net = OthelloNNet(board_size=cfg.board_size, dropout=cfg.dropout)
        load_checkpoint(cand_net, cand)
        res = _evaluate_model(cand_net, cfg, cfg.eval_games, cfg.eval_seed)
        logger.log(f"Stage 0 候補 {cand.name}: {_format_eval(res)}")
        if is_better_eval(res.win_rate, res.mean_stone_diff, best_rate, best_diff):
            best_rate = res.win_rate
            best_diff = res.mean_stone_diff
            best_path = cand
            best_res = res

    load_checkpoint(net, best_path)
    save_best(net, cfg.best_model)
    logger.log(
        f"Stage 0 選定 warm-start={best_path.name} ({best_rate * 100:.1f}%, stone_diff={best_diff:+.2f})"
    )
    return best_rate, best_diff, best_res


def _train_step_with_fallback(
    net: OthelloNNet,
    optimizer_factory: Callable[[OthelloNNet], optim.Optimizer],
    optimizer: optim.Optimizer,
    replay_buffer: ReplayBuffer,
    cfg: HybridTrainConfig,
    epochs: int,
    device: str,
    logger: DualLogger,
) -> tuple[float, float, float, str, optim.Optimizer]:
    """MPS 上で数値異常が出た場合は CPU へ安全フォールバックする。"""
    try:
        total_l, pol_l, val_l = train_on_buffer(
            net,
            optimizer,
            replay_buffer,
            batch_size=cfg.batch_size,
            epochs=epochs,
            device=device,
            value_loss_weight=cfg.value_loss_weight,
        )
        return total_l, pol_l, val_l, device, optimizer
    except RuntimeError as exc:
        if device == "cpu":
            raise
        logger.log(f"⚠️ device={device} で例外 ({exc}); CPU へフォールバックします")
        load_checkpoint(net, cfg.best_model)
        new_opt = optimizer_factory(net)
        total_l, pol_l, val_l = train_on_buffer(
            net,
            new_opt,
            replay_buffer,
            batch_size=cfg.batch_size,
            epochs=epochs,
            device="cpu",
            value_loss_weight=cfg.value_loss_weight,
        )
        return total_l, pol_l, val_l, "cpu", new_opt


def main(cfg: HybridTrainConfig) -> bool:
    """3 段階ハイブリッド訓練を実行し、最終公式認定の合否を返す。"""
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    torch.set_num_threads(1)
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(line_buffering=True)

    Path(cfg.best_model).parent.mkdir(parents=True, exist_ok=True)
    Path(cfg.latest_model).parent.mkdir(parents=True, exist_ok=True)

    logger = DualLogger(cfg.log_file)
    try:
        device = select_device(cfg.device)
        logger.log("=" * 70)
        logger.log(
            f"AlphaZero ハイブリッド訓練 v2 | opponent={cfg.opponent}({cfg.opponent_time_limit_ms}ms), "
            f"target>{cfg.win_rate_target * 100:.0f}%, eval_sims={cfg.eval_sims}, "
            f"dropout={cfg.dropout}, workers={cfg.workers}, train_device={device}"
        )
        logger.log("=" * 70)

        net = OthelloNNet(board_size=cfg.board_size, dropout=cfg.dropout)
        best_rate, best_diff, stage0_res = _run_stage0_baseline(net, cfg, logger)

        if not cfg.force_train and stage0_res is not None and should_trigger_certification(stage0_res, cfg):
            logger.log(f"Stage 0 で認定トリガー到達 -> 公式 {cfg.cert_games} 局評価を実行")
            cert_res = _evaluate_model(net, cfg, cfg.cert_games, cfg.eval_seed)
            logger.log(f"[Stage 0 公式認定] {_format_eval(cert_res)}")
            if certification_passed(cert_res, cfg.win_rate_target):
                logger.log("🎉 Stage 0 時点で目標達成")
                return True

        replay_buffer = ReplayBuffer(max_positions=cfg.buffer_capacity)

        # === Stage 1A: 大規模オフライン教師事前学習 ===
        if cfg.pretrain_games > 0 and cfg.pretrain_epochs > 0:
            logger.log(
                f"--- Stage 1A: 教師事前蒸留 (games={cfg.pretrain_games}, "
                f"epochs={cfg.pretrain_epochs}, lr={cfg.pretrain_lr}) ---"
            )
            pre_samples = collect_pretrain_samples(cfg, logger)
            replay_buffer.add_samples(pre_samples, source="pretrain")
            boards_t, pis_t, _ = replay_buffer.to_tensors()

            opt_pre: optim.Optimizer = optim.AdamW(
                net.parameters(), lr=cfg.pretrain_lr, weight_decay=1e-4
            )
            sched_pre = optim.lr_scheduler.CosineAnnealingLR(
                opt_pre, T_max=max(1, cfg.pretrain_epochs), eta_min=cfg.pretrain_min_lr
            )
            for ep in range(cfg.pretrain_epochs):
                total_l, pol_l, val_l, device, opt_pre = _train_step_with_fallback(
                    net,
                    lambda m: optim.AdamW(m.parameters(), lr=cfg.pretrain_lr, weight_decay=1e-4),
                    opt_pre,
                    replay_buffer,
                    cfg,
                    1,
                    device,
                    logger,
                )
                if total_l > 0.0:
                    sched_pre.step()
                if ((ep + 1) % 5 == 0) or ((ep + 1) == cfg.pretrain_epochs):
                    top1 = evaluate_policy_top1(net, boards_t, pis_t, device)
                    logger.log(
                        f"  [Stage1A Epoch {ep + 1}/{cfg.pretrain_epochs}] "
                        f"loss={total_l:.4f} (pi={pol_l:.4f}, v={val_l:.4f}), top1={top1 * 100:.1f}%"
                    )
            save_best(net, cfg.latest_model)
            ev = _evaluate_model(net, cfg, cfg.eval_games, cfg.eval_seed)
            logger.log(f"  [Stage1A 評価] {_format_eval(ev)}")
            improved = is_better_eval(ev.win_rate, ev.mean_stone_diff, best_rate, best_diff)
            if improved:
                best_rate, best_diff = ev.win_rate, ev.mean_stone_diff
                save_best(net, cfg.best_model)
                logger.log(f"  ✅ ベスト更新 -> {Path(cfg.best_model).name}")
            if improved and should_trigger_certification(ev, cfg):
                cert_net = OthelloNNet(board_size=cfg.board_size, dropout=cfg.dropout)
                load_checkpoint(cert_net, cfg.best_model)
                cert_res = _evaluate_model(cert_net, cfg, cfg.cert_games, cfg.eval_seed)
                logger.log(f"  [公式 {cfg.cert_games} 局認定] {_format_eval(cert_res)}")
                if certification_passed(cert_res, cfg.win_rate_target) and not cfg.force_train:
                    logger.log("🎉 Stage 1A で目標達成！")
                    return True

        # === Stage 1B: 対 Minimax/Negamax 標的型 DAgger ===
        if cfg.stage1_iters > 0:
            load_checkpoint(net, cfg.best_model)
            logger.log(
                f"--- Stage 1B: 標的型 DAgger (max {cfg.stage1_iters} iters, "
                f"games={cfg.dagger_games}, sims={cfg.dagger_sims}, lr={cfg.stage1_lr}) ---"
            )
            opt_s1: optim.Optimizer = optim.AdamW(
                net.parameters(), lr=cfg.stage1_lr, weight_decay=1e-4
            )
            sched_s1 = optim.lr_scheduler.CosineAnnealingLR(
                opt_s1, T_max=max(1, cfg.stage1_iters), eta_min=cfg.stage1_min_lr
            )
            for it in range(cfg.stage1_iters):
                t0 = time.perf_counter()
                samples = collect_dagger_games(net, cfg, seed_base=10_000 + it * 1000)
                replay_buffer.add_samples(samples, source="dagger")
                total_l, pol_l, val_l, device, opt_s1 = _train_step_with_fallback(
                    net,
                    lambda m: optim.AdamW(m.parameters(), lr=cfg.stage1_lr, weight_decay=1e-4),
                    opt_s1,
                    replay_buffer,
                    cfg,
                    cfg.stage1_epochs,
                    device,
                    logger,
                )
                if total_l > 0.0:
                    sched_s1.step()
                save_best(net, cfg.latest_model)
                elapsed = time.perf_counter() - t0
                logger.log(
                    f"[Stage1B {it + 1}/{cfg.stage1_iters}] new={len(samples)}, buf={len(replay_buffer)} "
                    f"{replay_buffer.stats()}, loss={total_l:.4f} (pi={pol_l:.4f}, v={val_l:.4f}), {elapsed:.1f}s"
                )

                should_eval = ((it + 1) % cfg.eval_interval == 0) or ((it + 1) == cfg.stage1_iters)
                if should_eval:
                    ev = _evaluate_model(net, cfg, cfg.eval_games, cfg.eval_seed)
                    logger.log(f"  [Stage1B 評価] {_format_eval(ev)}")
                    improved = is_better_eval(ev.win_rate, ev.mean_stone_diff, best_rate, best_diff)
                    if improved:
                        best_rate, best_diff = ev.win_rate, ev.mean_stone_diff
                        save_best(net, cfg.best_model)
                        logger.log(f"  ✅ ベスト更新 -> {Path(cfg.best_model).name}")

                    if improved and should_trigger_certification(ev, cfg):
                        cert_net = OthelloNNet(board_size=cfg.board_size, dropout=cfg.dropout)
                        load_checkpoint(cert_net, cfg.best_model)
                        cert_res = _evaluate_model(cert_net, cfg, cfg.cert_games, cfg.eval_seed)
                        logger.log(f"  [公式 {cfg.cert_games} 局認定] {_format_eval(cert_res)}")
                        if certification_passed(cert_res, cfg.win_rate_target) and not cfg.force_train:
                            logger.log("🎉 Stage 1B で目標達成！")
                            return True

                    if ev.win_rate >= cfg.stage1_promote_rate:
                        logger.log(
                            f"  🚀 Stage 1B 昇格条件 ({ev.win_rate * 100:.1f}% >= {cfg.stage1_promote_rate * 100:.1f}%) 到達 → Stage 2 へ"
                        )
                        break

        # === Stage 2: 安定化並列自己対戦 AlphaZero RL ===
        if cfg.stage2_iters > 0:
            load_checkpoint(net, cfg.best_model)
            replay_buffer.trim_to(cfg.stage2_keep_distill)
            logger.log(
                f"--- Stage 2: 安定化自己対戦 RL (max {cfg.stage2_iters} iters, lr={cfg.stage2_lr}, keep_buf={len(replay_buffer)}) ---"
            )
            opt_s2: optim.Optimizer = optim.AdamW(
                net.parameters(), lr=cfg.stage2_lr, weight_decay=1e-4
            )
            scheduler = optim.lr_scheduler.CosineAnnealingLR(
                opt_s2, T_max=max(1, cfg.stage2_iters), eta_min=cfg.stage2_min_lr
            )
            no_improve = 0

            for it in range(cfg.stage2_iters):
                t0 = time.perf_counter()
                samples = collect_selfplay_games(net, cfg, seed_base=50_000 + it * 1000)
                replay_buffer.add_samples(samples, source="selfplay")
                total_l, pol_l, val_l, device, opt_s2 = _train_step_with_fallback(
                    net,
                    lambda m: optim.AdamW(m.parameters(), lr=cfg.stage2_lr, weight_decay=1e-4),
                    opt_s2,
                    replay_buffer,
                    cfg,
                    cfg.stage2_epochs,
                    device,
                    logger,
                )
                if total_l > 0.0:
                    scheduler.step()
                save_best(net, cfg.latest_model)
                elapsed = time.perf_counter() - t0
                logger.log(
                    f"[Stage2 {it + 1}/{cfg.stage2_iters}] new={len(samples)}, buf={len(replay_buffer)} {replay_buffer.stats()}, "
                    f"loss={total_l:.4f} (pi={pol_l:.4f}, v={val_l:.4f}), {elapsed:.1f}s"
                )

                should_eval = ((it + 1) % cfg.eval_interval == 0) or ((it + 1) == cfg.stage2_iters)
                if should_eval:
                    ev = _evaluate_model(net, cfg, cfg.eval_games, cfg.eval_seed)
                    logger.log(f"  [Stage2 評価] {_format_eval(ev)}")
                    improved = is_better_eval(ev.win_rate, ev.mean_stone_diff, best_rate, best_diff)
                    if improved:
                        best_rate, best_diff = ev.win_rate, ev.mean_stone_diff
                        save_best(net, cfg.best_model)
                        no_improve = 0
                        logger.log(f"  ✅ ベスト更新 -> {Path(cfg.best_model).name}")
                    else:
                        no_improve += 1
                        logger.log(f"  ⏳ 改善なし ({no_improve}/{cfg.patience})")

                    if improved and should_trigger_certification(ev, cfg):
                        cert_net = OthelloNNet(board_size=cfg.board_size, dropout=cfg.dropout)
                        load_checkpoint(cert_net, cfg.best_model)
                        cert_res = _evaluate_model(cert_net, cfg, cfg.cert_games, cfg.eval_seed)
                        logger.log(f"  [公式 {cfg.cert_games} 局認定] {_format_eval(cert_res)}")
                        if certification_passed(cert_res, cfg.win_rate_target) and not cfg.force_train:
                            logger.log("🎉 Stage 2 で目標達成！")
                            return True

                    if no_improve >= cfg.patience:
                        logger.log(f"🛑 patience={cfg.patience} 到達のため Stage 2 を早期終了します")
                        break

        # === Stage 3: 最終公式認定 ===
        final_net = OthelloNNet(board_size=cfg.board_size, dropout=cfg.dropout)
        load_checkpoint(final_net, cfg.best_model)
        final_res = _evaluate_model(final_net, cfg, cfg.cert_games, cfg.eval_seed)
        logger.log("=" * 70)
        logger.log(f"[Stage 3 最終公式認定 ({cfg.cert_games} 局)] {_format_eval(final_res)}")
        passed = certification_passed(final_res, cfg.win_rate_target)
        logger.log("🎉 目標達成 (PASS)" if passed else "❌ 目標未達 (FAIL)")
        logger.log("=" * 70)
        return passed
    finally:
        logger.close()


def parse_args(argv: list[str] | None = None) -> HybridTrainConfig:
    """CLI 引数をパースして HybridTrainConfig を返す。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dropout", type=float, default=HybridTrainConfig.dropout)
    parser.add_argument("--pretrain-games", type=int, default=HybridTrainConfig.pretrain_games)
    parser.add_argument("--pretrain-teacher-ms", type=int, default=HybridTrainConfig.pretrain_teacher_ms)
    parser.add_argument("--pretrain-epochs", type=int, default=HybridTrainConfig.pretrain_epochs)
    parser.add_argument("--pretrain-lr", type=float, default=HybridTrainConfig.pretrain_lr)
    parser.add_argument("--pretrain-cache", type=str, default=HybridTrainConfig.pretrain_cache)
    parser.add_argument("--rebuild-pretrain", action="store_true")
    parser.add_argument("--stage1-iters", type=int, default=HybridTrainConfig.stage1_iters)
    parser.add_argument("--stage2-iters", type=int, default=HybridTrainConfig.stage2_iters)
    parser.add_argument("--dagger-games", type=int, default=HybridTrainConfig.dagger_games)
    parser.add_argument("--dagger-sims", type=int, default=HybridTrainConfig.dagger_sims)
    parser.add_argument("--teacher-time-ms", type=int, default=HybridTrainConfig.teacher_time_limit_ms)
    parser.add_argument("--selfplay-games", type=int, default=HybridTrainConfig.selfplay_games)
    parser.add_argument("--selfplay-sims", type=int, default=HybridTrainConfig.selfplay_sims)
    parser.add_argument("--batch-size", type=int, default=HybridTrainConfig.batch_size)
    parser.add_argument("--eval-games", type=int, default=HybridTrainConfig.eval_games)
    parser.add_argument("--eval-sims", type=int, default=HybridTrainConfig.eval_sims)
    parser.add_argument("--eval-interval", type=int, default=HybridTrainConfig.eval_interval)
    parser.add_argument("--cert-games", type=int, default=HybridTrainConfig.cert_games)
    parser.add_argument("--seed", type=int, default=HybridTrainConfig.eval_seed)
    parser.add_argument("--opponent", choices=["minimax", "negamax"], default=HybridTrainConfig.opponent)
    parser.add_argument("--opponent-time-ms", type=int, default=HybridTrainConfig.opponent_time_limit_ms)
    parser.add_argument("--target", type=float, default=HybridTrainConfig.win_rate_target)
    parser.add_argument("--patience", type=int, default=HybridTrainConfig.patience)
    parser.add_argument("--workers", type=int, default=HybridTrainConfig.workers)
    parser.add_argument("--device", choices=["auto", "cpu", "mps"], default=HybridTrainConfig.device)
    parser.add_argument("--warm-start", type=str, default=HybridTrainConfig.warm_start)
    parser.add_argument("--best-model", type=str, default=HybridTrainConfig.best_model)
    parser.add_argument("--latest-model", type=str, default=HybridTrainConfig.latest_model)
    parser.add_argument("--force-train", action="store_true")
    parser.add_argument("--log-file", type=str, default=HybridTrainConfig.log_file)
    args = parser.parse_args(argv)

    return HybridTrainConfig(
        dropout=args.dropout,
        pretrain_games=args.pretrain_games,
        pretrain_teacher_ms=args.pretrain_teacher_ms,
        pretrain_epochs=args.pretrain_epochs,
        pretrain_lr=args.pretrain_lr,
        pretrain_cache=args.pretrain_cache,
        rebuild_pretrain=args.rebuild_pretrain,
        stage1_iters=args.stage1_iters,
        stage2_iters=args.stage2_iters,
        dagger_games=args.dagger_games,
        dagger_sims=args.dagger_sims,
        teacher_time_limit_ms=args.teacher_time_ms,
        selfplay_games=args.selfplay_games,
        selfplay_sims=args.selfplay_sims,
        batch_size=args.batch_size,
        eval_games=args.eval_games,
        eval_sims=args.eval_sims,
        eval_interval=args.eval_interval,
        cert_games=args.cert_games,
        eval_seed=args.seed,
        opponent=args.opponent,
        opponent_time_limit_ms=args.opponent_time_ms,
        win_rate_target=args.target,
        patience=args.patience,
        workers=args.workers,
        device=args.device,
        warm_start=args.warm_start,
        best_model=args.best_model,
        latest_model=args.latest_model,
        force_train=args.force_train,
        log_file=args.log_file,
    )


if __name__ == "__main__":
    cfg = parse_args()
    sys.exit(0 if main(cfg) else 1)

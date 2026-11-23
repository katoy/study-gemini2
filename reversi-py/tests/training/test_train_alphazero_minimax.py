"""scripts/train_alphazero_minimax.py のテスト。"""
from __future__ import annotations

import pytest

TORCH_AVAILABLE = True
try:
    import torch  # noqa: F401
except ImportError:
    TORCH_AVAILABLE = False


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch が必要")
class TestTrainAlphazeroMinimax:
    def test_make_smoothed_policy_distribution(self) -> None:
        from scripts.train_alphazero_minimax import make_smoothed_policy

        # 単一合法手は確率 1.0
        p1 = make_smoothed_policy([(2, 3)], (2, 3), board_size=8, label_smoothing=0.10)
        assert float(p1.sum()) == pytest.approx(1.0)
        assert float(p1[2 * 8 + 3]) == pytest.approx(1.0)

        # 複数合法手はラベル平滑化され非合法手は 0.0
        moves = [(2, 3), (3, 2), (4, 5)]
        p2 = make_smoothed_policy(moves, (3, 2), board_size=8, label_smoothing=0.10)
        assert float(p2.sum()) == pytest.approx(1.0)
        assert float(p2[3 * 8 + 2]) == pytest.approx(0.90)
        assert float(p2[2 * 8 + 3]) == pytest.approx(0.05)
        assert float(p2[4 * 8 + 5]) == pytest.approx(0.05)
        assert float(p2[0]) == 0.0

    def test_score_to_value_mapping(self) -> None:
        from scripts.train_alphazero_minimax import score_to_value

        # 終盤読み切り確定値は勝敗へスナップ
        assert score_to_value(20000.0, -1.0) == 1.0
        assert score_to_value(-10000.0, 1.0) == -1.0
        # スコア 0 は終局勝敗をそのまま使用
        assert score_to_value(0.0, -1.0) == -1.0
        # 中盤スコアは終局勝敗と tanh をブレンド
        mid = score_to_value(150.0, 1.0)
        assert 0.5 < mid < 1.0

    def test_dagger_game_updates_game_board_for_teacher(self) -> None:
        """回帰テスト: 教師へ初期盤面だけでなく更新された進行盤面が渡される。"""
        from agents.base_agent import Agent
        from agents.networks.othello_net import OthelloNNet
        from scripts.train_alphazero_minimax import HybridTrainConfig, play_dagger_game

        observed_stone_counts: list[int] = []

        class SpyTeacher(Agent):
            def play(self, game):
                stones = sum(1 for row in game.board.board for c in row if c != 0)
                observed_stone_counts.append(stones)
                valid = game.get_valid_moves()
                return valid[0] if valid else None

        class FastOpponent(Agent):
            def play(self, game):
                valid = game.get_valid_moves()
                return valid[-1] if valid else None

        net = OthelloNNet(board_size=8)
        cfg = HybridTrainConfig(
            board_size=8,
            dagger_sims=2,
            dagger_temp_moves=2,
            opening_random_plies=2,
        )
        samples = play_dagger_game(
            net,
            cfg,
            az_is_white=True,
            seed=0,
            teacher_agent=SpyTeacher(),
            opponent_agent=FastOpponent(),
        )
        assert len(samples) > 0
        assert len(set(observed_stone_counts)) > 1
        assert max(observed_stone_counts) > min(observed_stone_counts)
        for board_p, pi, z in samples:
            assert board_p.shape == (8, 8)
            assert pi.shape == (65,)
            assert -1.0 <= z <= 1.0

    def test_teacher_pretrain_game_smoke(self) -> None:
        from agents.base_agent import Agent
        from scripts.train_alphazero_minimax import (
            HybridTrainConfig,
            play_teacher_pretrain_game,
        )

        class FastTeacher(Agent):
            def play(self, game):
                valid = game.get_valid_moves()
                return valid[0] if valid else None

        cfg = HybridTrainConfig(board_size=8, label_smoothing=0.05)
        samples = play_teacher_pretrain_game(cfg, seed=3, teacher_agent=FastTeacher())
        assert len(samples) > 0
        for board_p, pi, z in samples:
            assert board_p.shape == (8, 8)
            assert pi.shape == (65,)
            assert -1.0 <= z <= 1.0

    def test_teacher_pretrain_game_vs_opponent_smoke(self) -> None:
        from agents.base_agent import Agent
        from scripts.train_alphazero_minimax import (
            HybridTrainConfig,
            play_teacher_pretrain_game,
        )

        opp_turns: list[int] = []

        class FastTeacher(Agent):
            def play(self, game):
                valid = game.get_valid_moves()
                return valid[0] if valid else None

        class FastOpponent(Agent):
            def play(self, game):
                opp_turns.append(game.turn)
                valid = game.get_valid_moves()
                return valid[-1] if valid else None

        cfg = HybridTrainConfig(board_size=8, label_smoothing=0.05)
        samples_even = play_teacher_pretrain_game(
            cfg,
            seed=2,
            vs_opponent=True,
            teacher_agent=FastTeacher(),
            opponent_agent=FastOpponent(),
        )
        assert len(samples_even) > 0
        # seed=2 なら教師は白 (+1)、相手は黒 (-1) 側のみ打つ
        assert opp_turns and all(t == -1 for t in opp_turns)
        for board_p, pi, z in samples_even:
            assert board_p.shape == (8, 8)
            assert pi.shape == (65,)
            assert -1.0 <= z <= 1.0

    def test_selfplay_game_smoke(self) -> None:
        from agents.networks.othello_net import OthelloNNet
        from scripts.train_alphazero_minimax import HybridTrainConfig, play_selfplay_game

        net = OthelloNNet(board_size=8)
        cfg = HybridTrainConfig(board_size=8, selfplay_sims=2, selfplay_temp_moves=2)
        samples = play_selfplay_game(net, cfg, seed=1)
        assert len(samples) > 0
        for board_p, pi, z in samples:
            assert board_p.shape == (8, 8)
            assert pi.shape == (65,)
            assert z in (-1.0, 0.0, 1.0)

    def test_eval_helpers_and_strict_target(self) -> None:
        from scripts.train_alphazero_minimax import (
            HybridTrainConfig,
            certification_passed,
            is_better_eval,
            should_trigger_certification,
        )
        from training.alphazero.evaluation import EvalResult

        assert is_better_eval(0.8, -5.0, 0.7, 10.0)
        assert is_better_eval(0.8, 2.0, 0.8, 1.0)
        assert not is_better_eval(0.8, 1.0, 0.8, 1.0)

        cfg = HybridTrainConfig(win_rate_target=0.80, screen_cert_trigger=0.85)
        # ちょうど 0.80 は厳密超過 (> 0.80) で不合格
        exact_80 = EvalResult(win_rate=0.80, mean_stone_diff=3.0, results=[])
        assert not certification_passed(exact_80, 0.80)
        assert not should_trigger_certification(exact_80, cfg)

        above_80 = EvalResult(win_rate=0.82, mean_stone_diff=4.0, results=[])
        assert certification_passed(above_80, 0.80)
        assert should_trigger_certification(above_80, cfg)

    def test_train_on_buffer_and_cli_parsing(self, tmp_path) -> None:
        import numpy as np
        import torch
        import torch.optim as optim
        from agents.networks.othello_net import OthelloNNet
        from scripts.train_alphazero_minimax import (
            DualLogger,
            parse_args,
            select_device,
            train_on_buffer,
        )
        from training.alphazero.replay_buffer import ReplayBuffer

        cfg = parse_args(["--stage1-iters", "2", "--workers", "1", "--device", "cpu"])
        assert cfg.stage1_iters == 2
        assert cfg.workers == 1
        assert select_device("cpu") == "cpu"

        log_path = tmp_path / "train.log"
        logger = DualLogger(str(log_path))
        logger.log("hello")
        logger.close()
        assert "hello" in log_path.read_text(encoding="utf-8")

        net = OthelloNNet(board_size=8)
        opt = optim.AdamW(net.parameters(), lr=1e-4)
        buf = ReplayBuffer(max_positions=16)
        samples = [
            (
                np.zeros((8, 8), dtype=np.int8),
                np.full(65, 1.0 / 65.0, dtype=np.float32),
                1.0 if i % 2 == 0 else -1.0,
            )
            for i in range(8)
        ]
        buf.add_samples(samples, source="dagger")
        total_l, pol_l, val_l = train_on_buffer(
            net, opt, buf, batch_size=4, epochs=1, device="cpu"
        )
        assert total_l > 0.0
        assert pol_l > 0.0
        assert val_l >= 0.0
        assert next(net.parameters()).device == torch.device("cpu")

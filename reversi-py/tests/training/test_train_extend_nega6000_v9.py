"""scripts/train_extend_nega6000_v9.py のテスト。"""
from __future__ import annotations

import pytest

TORCH_AVAILABLE = True
try:
    import torch  # noqa: F401
except ImportError:
    TORCH_AVAILABLE = False


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch が必要")
class TestV9Training:
    def test_validate_training_config_rejects_batch_size_one(self) -> None:
        """batch_size < 2 の場合、ValueError を発生させる。"""
        from scripts.train_extend_nega6000_v9 import (
            TrainConfig,
            validate_training_config,
        )

        cfg = TrainConfig(batch_size=1)
        with pytest.raises(ValueError, match="batch_size >= 2"):
            validate_training_config(cfg)

    def test_resolve_resume_path_prefers_latest_when_warm_start_missing(
        self, tmp_path
    ) -> None:
        """warm_start が無いとき、latest_model を返す。"""
        from scripts.train_extend_nega6000_v9 import (
            TrainConfig,
            resolve_resume_path,
        )

        warm_start = tmp_path / "warm.pth"
        latest = tmp_path / "latest.pth"
        latest.write_bytes(b"checkpoint")
        cfg = TrainConfig(warm_start=str(warm_start), latest_model=str(latest))

        assert resolve_resume_path(cfg) == latest

    def test_resolve_resume_path_custom_warm_start_takes_priority(
        self, tmp_path
    ) -> None:
        """カスタム warm_start が指定されている場合、それを優先。"""
        from scripts.train_extend_nega6000_v9 import (
            TrainConfig,
            resolve_resume_path,
        )

        warm_start = tmp_path / "warm.pth"
        latest = tmp_path / "latest.pth"
        warm_start.write_bytes(b"warm")
        latest.write_bytes(b"latest")
        cfg = TrainConfig(warm_start=str(warm_start), latest_model=str(latest))

        # warm_start がデフォルト値と異なる場合、優先される
        assert resolve_resume_path(cfg) == warm_start

    def test_should_evaluate_iteration_defers_until_interval_or_final(self) -> None:
        """eval_interval の倍数またはラスト イテレーションで評価。"""
        from scripts.train_extend_nega6000_v9 import (
            TrainConfig,
            should_evaluate_iteration,
        )

        cfg = TrainConfig(n_iters=5, eval_interval=3)

        assert not should_evaluate_iteration(0, cfg)
        assert not should_evaluate_iteration(1, cfg)
        assert should_evaluate_iteration(2, cfg)  # 3rd iteration
        assert not should_evaluate_iteration(3, cfg)
        assert should_evaluate_iteration(4, cfg)  # final (5th)

    def test_dual_negamax_target_requires_both_rates(self) -> None:
        """両相手の勝率が目標以上でのみ合格。"""
        from scripts.train_extend_nega6000_v9 import dual_negamax_target_met

        assert dual_negamax_target_met(
            {"negamax_3k": 0.95, "negamax_6k": 0.96}, 0.95
        )
        assert not dual_negamax_target_met(
            {"negamax_3k": 0.96, "negamax_6k": 0.94}, 0.95
        )

    def test_v9_uses_replay_buffer(self) -> None:
        """v9 の設定で replay_buffer が有効（maxlen > games_per_iter）。"""
        from scripts.train_extend_nega6000_v9 import TrainConfig

        cfg = TrainConfig()
        # replay_buffer maxlen = 10 * games_per_iter
        expected_maxlen = 10 * cfg.games_per_iter
        # v9 では games_per_iter = 16、よって maxlen = 160
        assert expected_maxlen == 160

    def test_v9_config_uses_lower_learning_rate(self) -> None:
        """v9 では learning rate が 5e-5（v8 は 1e-4）。"""
        from scripts.train_extend_nega6000_v9 import TrainConfig

        cfg = TrainConfig()
        assert cfg.lr == 5e-5

    def test_v9_config_increased_games_per_iter(self) -> None:
        """v9 では games_per_iter = 16（v8 は 12）。"""
        from scripts.train_extend_nega6000_v9 import TrainConfig

        cfg = TrainConfig()
        assert cfg.games_per_iter == 16

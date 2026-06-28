"""scripts/train_extend_nega6000_v7_dual_negamax.py のテスト。"""

import pytest

TORCH_AVAILABLE = True
try:
    import torch  # noqa: F401
except ImportError:
    TORCH_AVAILABLE = False


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch が必要")
class TestDualNegamaxTraining:
    def test_dual_negamax_target_requires_both_rates(self) -> None:
        from scripts.train_extend_nega6000_v7_dual_negamax import (
            dual_negamax_target_met,
        )

        assert dual_negamax_target_met({"negamax_3k": 0.95, "negamax_6k": 0.96}, 0.95)
        assert not dual_negamax_target_met(
            {"negamax_3k": 0.96, "negamax_6k": 0.94},
            0.95,
        )

    def test_evaluate_vs_dual_negamax_uses_both_time_limits(self, monkeypatch) -> None:
        from scripts import train_extend_nega6000_v7_dual_negamax as mod

        calls: list[int] = []

        def fake_evaluate_against_negamax(net, n_games, cfg, time_limit_ms):
            calls.append(time_limit_ms)
            return 0.97 if time_limit_ms == 3000 else 0.96

        monkeypatch.setattr(mod, "evaluate_against_negamax", fake_evaluate_against_negamax)

        rates = mod.evaluate_vs_dual_negamax(object(), n_games=4, cfg=object())

        assert calls == [3000, 6000]
        assert rates == {"negamax_3k": 0.97, "negamax_6k": 0.96}

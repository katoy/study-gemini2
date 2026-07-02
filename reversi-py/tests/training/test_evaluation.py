"""training/alphazero/evaluation.py のテスト。"""
from __future__ import annotations

import pytest

TORCH_AVAILABLE = True
try:
    import torch  # noqa: F401
except ImportError:
    TORCH_AVAILABLE = False


def create_mock_agents(monkeypatch):
    """AlphaZero と Negamax のモック agent を作成して設定する。"""

    def mock_from_net(net, n_simulations):
        class MockAlphaZero:
            def play(self, game):
                valid = game.get_valid_moves()
                return valid[0] if valid else None

        return MockAlphaZero()

    def mock_negamax_init(self, time_limit_ms):
        pass

    def mock_negamax_play(self, game):
        valid = game.get_valid_moves()
        return valid[0] if valid else None

    monkeypatch.setattr(
        "training.alphazero.evaluation.AlphaZeroAgent.from_net",
        mock_from_net,
    )
    monkeypatch.setattr(
        "training.alphazero.evaluation.NegamaxAgent.__init__",
        mock_negamax_init,
    )
    monkeypatch.setattr(
        "training.alphazero.evaluation.NegamaxAgent.play",
        mock_negamax_play,
    )


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch が必要")
class TestEvaluateAgainstNegamax:
    def test_n_games_must_be_even(self) -> None:
        """n_games が奇数の場合、ValueError を発生させる。"""
        from training.alphazero.evaluation import evaluate_against_negamax

        net = object()

        with pytest.raises(ValueError, match="n_games must be even"):
            evaluate_against_negamax(
                net,
                n_games=5,
                time_limit_ms=3000,
            )

    def test_eval_result_has_required_fields(self, monkeypatch) -> None:
        """EvalResult が win_rate, mean_stone_diff, results フィールドを持つ。"""
        from training.alphazero.evaluation import evaluate_against_negamax

        create_mock_agents(monkeypatch)

        net = object()

        result = evaluate_against_negamax(
            net,
            n_games=2,
            time_limit_ms=3000,
            n_simulations=10,
        )

        assert hasattr(result, "win_rate")
        assert hasattr(result, "mean_stone_diff")
        assert hasattr(result, "results")
        assert isinstance(result.win_rate, float)
        assert isinstance(result.mean_stone_diff, float)
        assert isinstance(result.results, list)
        assert len(result.results) == 2

    def test_results_contain_per_game_records(self, monkeypatch) -> None:
        """各ゲームの結果に opening_index, az_is_white, az_wins, stone_diff を含む。"""
        from training.alphazero.evaluation import evaluate_against_negamax

        create_mock_agents(monkeypatch)

        net = object()

        result = evaluate_against_negamax(
            net,
            n_games=4,
            time_limit_ms=3000,
            n_simulations=10,
        )

        # 4 ゲーム = 2 開口 × 2 色
        for i, record in enumerate(result.results):
            assert "opening_index" in record
            assert "az_is_white" in record
            assert "az_wins" in record
            assert "stone_diff" in record
            assert record["opening_index"] == i // 2
            assert isinstance(record["az_is_white"], bool)
            assert isinstance(record["az_wins"], bool)
            assert isinstance(record["stone_diff"], int)

    def test_pair_design_two_games_per_opening(self, monkeypatch) -> None:
        """n_games=4 のとき、2 開口が各々2ゲーム（先手/後手）実施される。"""
        from training.alphazero.evaluation import evaluate_against_negamax

        create_mock_agents(monkeypatch)

        net = object()

        result = evaluate_against_negamax(
            net,
            n_games=4,
            time_limit_ms=3000,
            n_simulations=10,
        )

        # 2 開口のカウント
        opening_0_count = sum(1 for r in result.results if r["opening_index"] == 0)
        opening_1_count = sum(1 for r in result.results if r["opening_index"] == 1)

        assert opening_0_count == 2  # 開口 0: 白手番 + 黒手番
        assert opening_1_count == 2  # 開口 1: 白手番 + 黒手番

        # 各開口で先手/後手が両方存在することを確認
        for opening_idx in [0, 1]:
            games = [r for r in result.results if r["opening_index"] == opening_idx]
            az_white_colors = {g["az_is_white"] for g in games}
            assert az_white_colors == {True, False}, f"開口 {opening_idx} で色のバリエーションなし"

"""training/alphazero/evaluation.py のテスト。"""
from __future__ import annotations

from typing import Any

import pytest

TORCH_AVAILABLE = True
try:
    import torch  # noqa: F401
except ImportError:
    TORCH_AVAILABLE = False


def create_mock_agents(monkeypatch):
    """AlphaZero と Negamax のモック agent を作成して設定する。"""

    def mock_from_net(net, n_simulations, **kwargs):
        # **kwargs により新パラメータ endgame_empties, endgame_time_limit_ms をキャッチ
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

        net: Any = object()

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

        net: Any = object()

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

        net: Any = object()

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

        net: Any = object()

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

    def test_pair_design_shares_exact_opening_board(self, monkeypatch) -> None:
        """同一開口インデックスの白番局と黒番局が同一の初期盤面・手番から始まる。"""
        from training.alphazero.evaluation import evaluate_against_negamax

        seen_openings: list[tuple[list[list[int]], int]] = []
        game_started = {"captured": False}

        def record_move(game) -> tuple[int, int] | None:
            if not game_started["captured"]:
                seen_openings.append(([row[:] for row in game.board.board], game.turn))
                game_started["captured"] = True
            valid = game.get_valid_moves()
            return valid[0] if valid else None

        def mock_from_net(net, n_simulations, **kwargs):
            class RecordingAlphaZero:
                def play(self, game):
                    return record_move(game)

            return RecordingAlphaZero()

        def mock_negamax_init(self, time_limit_ms):
            game_started["captured"] = False

        def mock_negamax_play(self, game):
            return record_move(game)

        monkeypatch.setattr("training.alphazero.evaluation.AlphaZeroAgent.from_net", mock_from_net)
        monkeypatch.setattr("training.alphazero.evaluation.NegamaxAgent.__init__", mock_negamax_init)
        monkeypatch.setattr("training.alphazero.evaluation.NegamaxAgent.play", mock_negamax_play)

        net: Any = object()
        result = evaluate_against_negamax(
            net, n_games=4, time_limit_ms=10, n_simulations=2, opening_random_plies=4, seed=7
        )
        assert len(seen_openings) == 4
        assert seen_openings[0] == seen_openings[1]
        assert seen_openings[2] == seen_openings[3]
        assert result.wins + result.draws + result.losses == 4
        lo, hi = result.wilson_ci()
        assert 0.0 <= lo <= result.win_rate <= hi <= 1.0

    def test_evaluate_against_agent_with_minimax_and_empty_wilson_ci(self, monkeypatch) -> None:
        """evaluate_against_agent が任意 opponent_factory で動作し、空 EvalResult も安全。"""
        from agents.minimax_agent import MinimaxAgent
        from training.alphazero.evaluation import EvalResult, evaluate_against_agent

        empty = EvalResult(win_rate=0.0, mean_stone_diff=0.0, results=[])
        assert empty.wilson_ci() == (0.0, 0.0)

        create_mock_agents(monkeypatch)
        net: Any = object()
        res = evaluate_against_agent(
            net,
            lambda: MinimaxAgent(time_limit_ms=20, max_depth=1, endgame_empties=0),
            n_games=2,
            n_simulations=2,
            opening_random_plies=2,
            seed=11,
            show_progress=False,
        )
        assert len(res.results) == 2
        assert res.wins + res.draws + res.losses == 2

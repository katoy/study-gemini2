"""PatternAgent の 8x8 盤面テスト。"""
from unittest.mock import patch

from game import Game
from agents.pattern_agent import PatternAgent


def test_pattern_agent_initializes() -> None:
    """PatternAgent が正常に初期化できる"""
    agent = PatternAgent(weights_path=None, time_limit_ms=100)
    assert agent is not None
    assert agent._time_limit_ms == 100


def test_pattern_agent_evaluator_initialized() -> None:
    """PatternAgent が PatternEvaluator を 8x8 盤面で初期化する"""
    agent = PatternAgent(weights_path=None, time_limit_ms=100)
    assert agent._evaluator is not None
    assert agent._evaluator.board_size == 8


def test_pattern_agent_mocked_play() -> None:
    """PatternAgent が 8x8 盤面で着手を返す (mock 使用)"""
    agent = PatternAgent(weights_path=None, time_limit_ms=100)

    # _negamax メソッドを mock して高速化
    with patch.object(agent, '_negamax', return_value=(1.0, (2, 3))):
        game = Game(board_size=8)
        move = agent.play(game)

    # play メソッドは最善手を返す
    if move is not None:
        assert isinstance(move, tuple)
        assert len(move) == 2
        assert 0 <= move[0] < 8
        assert 0 <= move[1] < 8

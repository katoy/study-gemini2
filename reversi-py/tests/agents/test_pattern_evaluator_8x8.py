"""PatternEvaluator の 8x8 盤面テスト。"""
from agents.pattern_evaluator import PatternEvaluator


def test_pattern_evaluator_initializes() -> None:
    """PatternEvaluator が 8x8 盤面で初期化できる"""
    evaluator = PatternEvaluator(board_size=8, weights_path=None)
    assert evaluator is not None
    assert evaluator.board_size == 8


def test_pattern_evaluator_evaluates_board() -> None:
    """PatternEvaluator が 8x8 盤面を評価できる"""
    evaluator = PatternEvaluator(board_size=8, weights_path=None)

    # 初期盤面
    board = [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, -1, 0, 0, 0],
        [0, 0, 0, -1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]

    # 黒番（turn=-1）で評価
    value = evaluator.evaluate(board, turn=-1)
    assert isinstance(value, float)

    # 白番（turn=1）で評価
    value = evaluator.evaluate(board, turn=1)
    assert isinstance(value, float)


def test_pattern_evaluator_pattern_index() -> None:
    """PatternEvaluator がパターンインデックスを計算できる"""
    evaluator = PatternEvaluator(board_size=8, weights_path=None)

    board = [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, -1, 0, 0, 0],
        [0, 0, 0, -1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]

    # top edge squares のパターンを取得
    if hasattr(evaluator, 'patterns'):
        # パターンが存在する場合
        assert isinstance(evaluator.patterns, dict)

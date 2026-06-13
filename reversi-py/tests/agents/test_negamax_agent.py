"""NegamaxAgent の単体テスト。"""
import pytest

from agents.negamax_agent import _build_weight_table


class TestBuildWeightTable:
    """位置重みテーブル生成のテスト。"""

    @pytest.mark.parametrize("n", [4, 6, 8, 16])
    def test_table_size(self, n):
        table = _build_weight_table(n)
        assert len(table) == n
        assert all(len(row) == n for row in table)

    @pytest.mark.parametrize("n", [4, 6, 8, 16])
    def test_rotational_symmetry(self, n):
        """テーブルは 90 度回転で不変（4 回回転対称）。"""
        table = _build_weight_table(n)
        rotated = tuple(zip(*table[::-1]))
        assert rotated == table

    def test_role_weights_8x8(self):
        table = _build_weight_table(8)
        assert table[0][0] == 100      # 角
        assert table[1][1] == -50      # X マス
        assert table[0][1] == -20      # C マス
        assert table[0][3] == 10       # 辺
        assert table[1][3] == -2       # 辺の 1 つ内側
        assert table[3][3] == 0        # 中央

    def test_corner_beats_edge_beats_x(self):
        table = _build_weight_table(8)
        assert table[0][0] > table[0][3] > 0 > table[1][1]

    def test_cache_returns_same_object(self):
        assert _build_weight_table(8) is _build_weight_table(8)

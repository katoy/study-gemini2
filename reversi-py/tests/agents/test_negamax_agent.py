"""NegamaxAgent の単体テスト。"""
import pytest

from agents.negamax_agent import (
    _apply,
    _build_weight_table,
    _flips_for_move,
    _undo,
    _valid_moves,
)


class TestBuildWeightTable:
    """位置重みテーブル生成のテスト。"""

    @pytest.mark.parametrize("n", [4, 6, 8, 16])
    def test_table_size(self, n: int) -> None:
        table = _build_weight_table(n)
        assert len(table) == n
        assert all(len(row) == n for row in table)

    @pytest.mark.parametrize("n", [4, 6, 8, 16])
    def test_rotational_symmetry(self, n: int) -> None:
        """テーブルは 90 度回転で不変（4 回回転対称）。"""
        table = _build_weight_table(n)
        rotated = tuple(zip(*table[::-1]))
        assert rotated == table

    def test_role_weights_8x8(self) -> None:
        table = _build_weight_table(8)
        assert table[0][0] == 100      # 角
        assert table[1][1] == -50      # X マス
        assert table[0][1] == -20      # C マス
        assert table[0][3] == 10       # 辺
        assert table[1][3] == -2       # 辺の 1 つ内側
        assert table[3][3] == 0        # 中央

    def test_corner_beats_edge_beats_x(self) -> None:
        table = _build_weight_table(8)
        assert table[0][0] > table[0][3] > 0 > table[1][1]

    def test_cache_returns_same_object(self) -> None:
        assert _build_weight_table(8) is _build_weight_table(8)


def _initial_board(n: int = 8) -> list:
    """初期配置の盤面を作る（board.py の Board.__init__ と同一配置）。"""
    board = [[0] * n for _ in range(n)]
    h = n // 2
    board[h - 1][h - 1] = board[h][h] = 1       # 白
    board[h - 1][h] = board[h][h - 1] = -1      # 黒
    return board


from agents.negamax_agent import (
    _PHASE_COEFFS,
    _disc_diff,
    _evaluate,
    _phase_coeffs,
    _stable_edge_count,
    _terminal_score,
)


class TestEvaluation:
    """評価関数のテスト。"""

    def test_phase_coeffs_three_stages(self) -> None:
        n = 8
        early = _initial_board(n)                      # 4 石 → fill 0.0625
        mid = [[-1] * n for _ in range(4)] + [[0] * n for _ in range(4)]  # fill 0.5
        late = [[-1] * n for _ in range(7)] + [[0] * n]                   # fill 0.875
        assert _phase_coeffs(early, n) == _PHASE_COEFFS[0]
        assert _phase_coeffs(mid, n) == _PHASE_COEFFS[1]
        assert _phase_coeffs(late, n) == _PHASE_COEFFS[2]

    def test_stable_edge_count(self) -> None:
        board = [[0] * 8 for _ in range(8)]
        board[0][0] = board[0][1] = board[0][2] = -1   # 上辺の角から 3 連
        board[1][0] = -1                               # 左辺の角から 2 連目
        assert _stable_edge_count(board, 8, -1) == 4
        assert _stable_edge_count(board, 8, 1) == 0

    def test_stable_edge_count_no_corner_means_zero(self) -> None:
        board = [[0] * 8 for _ in range(8)]
        board[0][3] = -1   # 角に接続しない辺石は数えない
        assert _stable_edge_count(board, 8, -1) == 0

    def test_disc_diff(self) -> None:
        board = _initial_board(8)
        board[0][0] = -1
        assert _disc_diff(board, -1) == 1
        assert _disc_diff(board, 1) == -1

    def test_terminal_score_scale(self) -> None:
        board = _initial_board(8)
        board[0][0] = -1
        assert _terminal_score(board, -1) == 10000
        assert _terminal_score(board, 1) == -10000

    def test_evaluate_is_symmetric(self) -> None:
        """同一局面で手番を入れ替えると符号が反転する。"""
        board = _initial_board(8)
        board[2][3] = -1
        assert _evaluate(board, 8, -1) == pytest.approx(-_evaluate(board, 8, 1))

    def test_evaluate_prefers_corner(self) -> None:
        """角を持つ側の評価が高い。"""
        board = _initial_board(8)
        with_corner = [row[:] for row in board]
        with_corner[0][0] = -1
        assert _evaluate(with_corner, 8, -1) > _evaluate(board, 8, -1)


class TestSearchPrimitives:
    """合法手生成と make/unmake のテスト。"""

    def test_valid_moves_matches_board_class(self) -> None:
        """モジュール内の合法手生成が Board.get_valid_moves と一致する。"""
        from board import Board
        b = Board(board_size=8)
        board = _initial_board(8)
        assert _valid_moves(board, 8, -1) == b.get_valid_moves(-1)
        assert _valid_moves(board, 8, 1) == b.get_valid_moves(1)

    def test_flips_for_move_initial_position(self) -> None:
        board = _initial_board(8)
        # 黒 (turn=-1) が (2, 3) に打つと (3, 3) の白が返る
        assert _flips_for_move(board, 8, 2, 3, -1) == [(3, 3)]

    def test_flips_for_occupied_cell_is_empty(self) -> None:
        board = _initial_board(8)
        assert _flips_for_move(board, 8, 3, 3, -1) == []

    def test_apply_undo_roundtrip(self) -> None:
        """_apply して _undo すると盤面が完全に元へ戻る。"""
        board = _initial_board(8)
        snapshot = [row[:] for row in board]
        flips = _flips_for_move(board, 8, 2, 3, -1)
        _apply(board, (2, 3), flips, -1)
        assert board[2][3] == -1
        assert board[3][3] == -1  # 反転済み
        _undo(board, (2, 3), flips, -1)
        assert board == snapshot

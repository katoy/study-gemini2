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


from unittest.mock import Mock

from agents.negamax_agent import NegamaxAgent, _SearchTimeout


def _make_game(board: list, turn: int) -> Mock:
    """探索に必要な最小限の Game モックを作る。"""
    from board import Board
    game = Mock()
    n = len(board)
    b = Board(board_size=n)
    b.board = [row[:] for row in board]
    game.board = b
    game.turn = turn
    game.get_board.return_value = [row[:] for row in board]
    game.get_valid_moves.return_value = b.get_valid_moves(turn)
    game.get_board_size.return_value = n
    return game


def _deterministic_agent(depth: int = 3) -> NegamaxAgent:
    """時間制限を実質無効化した決定論的エージェント。"""
    return NegamaxAgent(time_limit_ms=10**9, max_depth=depth)


class TestNegamaxAgentPlay:
    """NegamaxAgent.play の振る舞いテスト。"""

    def test_no_valid_moves_returns_none(self) -> None:
        board = [[-1] * 8 for _ in range(8)]   # 黒で埋め尽くし → 合法手なし
        game = _make_game(board, turn=1)
        assert _deterministic_agent().play(game) is None

    def test_single_move_returned_without_search(self) -> None:
        game = _make_game(_initial_board(8), turn=-1)
        game.get_valid_moves.return_value = [(2, 3)]
        assert _deterministic_agent().play(game) == (2, 3)

    def test_returns_legal_move_from_initial_position(self) -> None:
        game = _make_game(_initial_board(8), turn=-1)
        move = _deterministic_agent().play(game)
        assert move in game.board.get_valid_moves(-1)

    def test_takes_corner_when_available(self) -> None:
        """角が合法手なら角を選ぶ（深さ 2 で十分）。"""
        board = [[0] * 8 for _ in range(8)]
        board[0][1] = 1     # C マスに白
        board[0][2] = -1    # 黒
        board[4][4] = board[4][5] = 1
        board[5][4] = -1
        game = _make_game(board, turn=-1)
        assert (0, 0) in game.board.get_valid_moves(-1)
        move = _deterministic_agent(depth=2).play(game)
        assert move == (0, 0)

    def test_returns_legal_move_with_tiny_time_limit(self) -> None:
        """time_limit_ms=1 でも depth 1 の結果で合法手を返す。"""
        agent = NegamaxAgent(time_limit_ms=1)
        game = _make_game(_initial_board(8), turn=-1)
        move = agent.play(game)
        assert move in game.board.get_valid_moves(-1)

    def test_deterministic_same_input_same_output(self) -> None:
        game1 = _make_game(_initial_board(8), turn=-1)
        game2 = _make_game(_initial_board(8), turn=-1)
        assert _deterministic_agent().play(game1) == _deterministic_agent().play(game2)


class TestEndgameAndPass:
    """終盤読み切りとパス処理のテスト。"""

    def test_endgame_solver_picks_winning_move(self) -> None:
        """4x4 の残り 1 マスを埋める唯一の合法手を完全読みで選ぶ。"""
        board = [
            [-1, -1, -1, -1],
            [-1, 1, 1, -1],
            [-1, 1, 0, -1],
            [-1, -1, -1, -1],
        ]
        # 黒 (turn=-1) は (2, 2) のみ合法手（上方向で (1, 2) の白を挟む）
        game = _make_game(board, turn=-1)
        assert game.board.get_valid_moves(-1) == [(2, 2)]
        agent = NegamaxAgent(time_limit_ms=10**9, endgame_empties=12)
        # 合法手 1 つのショートカットを通さず探索経路を踏むため直接呼ぶ
        n = 4
        inner = [row[:] for row in board]
        agent._deadline = float("inf")
        agent._node_count = 0
        assert agent._search_root(inner, n, -1, depth=1, endgame=True) == (2, 2)

    def test_negamax_pass_switches_turn_without_consuming_depth(self) -> None:
        """手番側に合法手がなく相手にある局面では手番交代して探索を続ける。

        パス処理は深さを消費しない（深さ 2 で黒パス → 白着手 → 黒評価値が返る）。
        最終的にダブルパスになる場合は終局スコアが返される。
        """
        board = [[0] * 4 for _ in range(4)]
        board[0][0] = 1
        board[0][1] = -1
        # 黒に合法手なし、白に (0, 2) の合法手あり
        # 白が着手後、黒にも合法手がない（ダブルパス）→ 終局スコアが返される
        agent = _deterministic_agent()
        agent._deadline = float("inf")
        agent._node_count = 0
        value = agent._negamax(board, 4, -1, 2, float("-inf"), float("inf"),
                               endgame=False, passed=False)
        # ダブルパス → 終局スコア（10000 倍）が返される
        # 黒視点で石差 -3（白 3 石、黒 0 石） → -30000
        assert value == -30000.0

    def test_negamax_double_pass_returns_terminal_score(self) -> None:
        """双方に合法手がない局面は終局として確定スコアを返す。"""
        board = [[0] * 4 for _ in range(4)]
        board[0][0] = -1   # 黒石 1 つのみ → どちらも着手不能
        agent = _deterministic_agent()
        agent._deadline = float("inf")
        agent._node_count = 0
        value = agent._negamax(board, 4, -1, 3, float("-inf"), float("inf"),
                               endgame=False, passed=False)
        assert value == 10000.0   # 黒視点: 石差 +1 × 10000


class TestTimeManagement:
    """時間管理と _SearchTimeout のテスト。"""

    def test_negamax_raises_timeout_when_deadline_passed(self) -> None:
        agent = NegamaxAgent(time_limit_ms=10**9)
        agent._deadline = 0.0           # 過去のデッドライン
        agent._node_count = 511         # 次のノードで時刻チェックが走る
        board = _initial_board(8)
        with pytest.raises(_SearchTimeout):
            agent._negamax(board, 8, -1, 3, float("-inf"), float("inf"),
                           endgame=False, passed=False)

    def test_play_survives_mid_search_timeout(self, monkeypatch) -> None:
        """深さ 2 以降で時間切れになっても depth 1 の手を返す。"""
        agent = NegamaxAgent(time_limit_ms=10**9, max_depth=10)
        game = _make_game(_initial_board(8), turn=-1)
        original = agent._search_root
        calls = {"n": 0}

        def flaky(*args, **kwargs):
            calls["n"] += 1
            if calls["n"] >= 2:
                raise _SearchTimeout()
            return original(*args, **kwargs)

        monkeypatch.setattr(agent, "_search_root", flaky)
        move = agent.play(game)
        assert move in game.board.get_valid_moves(-1)


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

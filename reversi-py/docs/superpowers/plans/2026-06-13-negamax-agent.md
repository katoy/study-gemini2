# NegamaxAgent 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 現 MCTS より強い純 Python の API プレイヤー `NegamaxAgent`（アルファベータ + 反復深化 + 終盤読み切り）を `agent_type="negamax"` として追加する。

**Architecture:** `agents/negamax_agent.py` 1 ファイルに、make/unmake 方式の軽量探索（deepcopy なし）、サイズ非依存の位置重みテーブル、ゲームフェーズ別評価関数、反復深化 + デッドライン管理を実装する。サーバー（`server/api_server.py`）・GUI（`config/agents_config.py`）・テスト 3 層に登録する。乱択を使わず完全に決定論的。

**Tech Stack:** Python 3（純標準ライブラリ）、pytest、FastAPI TestClient、uv。

**参照仕様書:** `docs/superpowers/specs/2026-06-13-negamax-agent-design.md`

**実行コマンドの前提:** リポジトリの `reversi-py/` ディレクトリで `uv run pytest ...` を実行する。

---

### Task 1: 位置重みテーブル `_build_weight_table`

**Files:**
- Create: `agents/negamax_agent.py`
- Test: `tests/agents/test_negamax_agent.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/agents/test_negamax_agent.py` を新規作成:

```python
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
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `uv run pytest tests/agents/test_negamax_agent.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'agents.negamax_agent'`）

- [ ] **Step 3: 最小実装を書く**

`agents/negamax_agent.py` を新規作成:

```python
# agents/negamax_agent.py
"""Negamax（アルファベータ枝刈り + 反復深化 + 終盤読み切り）エージェント。

純 Python・依存ゼロで現 MCTS より深く読む API プレイヤー。
設計書: docs/superpowers/specs/2026-06-13-negamax-agent-design.md
"""
from functools import lru_cache
from typing import Tuple

# マスの役割ごとの重み
_WEIGHT_CORNER = 100   # 角
_WEIGHT_X = -50        # X マス（角の斜め隣）
_WEIGHT_C = -20        # C マス（角の縦横隣）
_WEIGHT_EDGE = 10      # その他の辺
_WEIGHT_INNER = -2     # 辺の 1 つ内側
_WEIGHT_CENTER = 0     # 中央部


@lru_cache(maxsize=None)
def _build_weight_table(n: int) -> Tuple[Tuple[int, ...], ...]:
    """サイズ n の位置重みテーブルをマスの役割から生成する。

    最寄りの辺までの距離 (er, ec) で役割を判定するため、
    どの盤面サイズでも一貫した 4 回回転対称のテーブルになる。

    Args:
        n: 盤面サイズ。

    Returns:
        n x n の重みテーブル（イミュータブルなタプルの入れ子）。
    """
    table = [[_WEIGHT_CENTER] * n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            er = min(r, n - 1 - r)
            ec = min(c, n - 1 - c)
            if er == 0 and ec == 0:
                w = _WEIGHT_CORNER
            elif er == 1 and ec == 1:
                w = _WEIGHT_X
            elif {er, ec} == {0, 1}:
                w = _WEIGHT_C
            elif er == 0 or ec == 0:
                w = _WEIGHT_EDGE
            elif er == 1 or ec == 1:
                w = _WEIGHT_INNER
            else:
                w = _WEIGHT_CENTER
            table[r][c] = w
    return tuple(tuple(row) for row in table)
```

- [ ] **Step 4: テストが通ることを確認**

Run: `uv run pytest tests/agents/test_negamax_agent.py -v`
Expected: PASS（全件）

- [ ] **Step 5: コミット**

```bash
git add agents/negamax_agent.py tests/agents/test_negamax_agent.py
git commit -m "feat: Negamax 用のサイズ非依存位置重みテーブルを追加"
```

---

### Task 2: 探索プリミティブ（合法手・反転・make/unmake）

**Files:**
- Modify: `agents/negamax_agent.py`
- Test: `tests/agents/test_negamax_agent.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/agents/test_negamax_agent.py` に追記:

```python
from agents.negamax_agent import _apply, _flips_for_move, _undo, _valid_moves


def _initial_board(n: int = 8) -> list:
    """初期配置の盤面を作る（board.py の Board.__init__ と同一配置）。"""
    board = [[0] * n for _ in range(n)]
    h = n // 2
    board[h - 1][h - 1] = board[h][h] = 1       # 白
    board[h - 1][h] = board[h][h - 1] = -1      # 黒
    return board


class TestSearchPrimitives:
    """合法手生成と make/unmake のテスト。"""

    def test_valid_moves_matches_board_class(self):
        """モジュール内の合法手生成が Board.get_valid_moves と一致する。"""
        from board import Board
        b = Board(board_size=8)
        board = _initial_board(8)
        assert _valid_moves(board, 8, -1) == b.get_valid_moves(-1)
        assert _valid_moves(board, 8, 1) == b.get_valid_moves(1)

    def test_flips_for_move_initial_position(self):
        board = _initial_board(8)
        # 黒 (turn=-1) が (2, 3) に打つと (3, 3) の白が返る
        assert _flips_for_move(board, 8, 2, 3, -1) == [(3, 3)]

    def test_flips_for_occupied_cell_is_empty(self):
        board = _initial_board(8)
        assert _flips_for_move(board, 8, 3, 3, -1) == []

    def test_apply_undo_roundtrip(self):
        """_apply して _undo すると盤面が完全に元へ戻る。"""
        board = _initial_board(8)
        snapshot = [row[:] for row in board]
        flips = _flips_for_move(board, 8, 2, 3, -1)
        _apply(board, (2, 3), flips, -1)
        assert board[2][3] == -1
        assert board[3][3] == -1  # 反転済み
        _undo(board, (2, 3), flips, -1)
        assert board == snapshot
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `uv run pytest tests/agents/test_negamax_agent.py::TestSearchPrimitives -v`
Expected: FAIL（`ImportError: cannot import name '_apply'`）

- [ ] **Step 3: 実装を書く**

`agents/negamax_agent.py` に追記（import に `List, Optional` を追加）:

```python
from typing import List, Optional, Tuple

# 8 方向の走査ベクトル
_DIRECTIONS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1), (0, 1),
    (1, -1), (1, 0), (1, 1),
)


def _flips_for_move(
    board: List[List[int]], n: int, row: int, col: int, turn: int
) -> List[Tuple[int, int]]:
    """着手 (row, col) で反転する石のリストを返す（空なら不合法手）。

    board.py の Board._get_flipped_in_direction と同じ走査ロジックを
    探索用に関数化したもの。Board クラスは変更しない。
    """
    if board[row][col] != 0:
        return []
    flips: List[Tuple[int, int]] = []
    for dr, dc in _DIRECTIONS:
        line: List[Tuple[int, int]] = []
        r, c = row + dr, col + dc
        while 0 <= r < n and 0 <= c < n:
            v = board[r][c]
            if v == 0:
                break
            if v == turn:
                flips.extend(line)
                break
            line.append((r, c))
            r += dr
            c += dc
    return flips


def _valid_moves(board: List[List[int]], n: int, turn: int) -> List[Tuple[int, int]]:
    """turn 側の合法手を row-major 順で返す。"""
    return [
        (r, c)
        for r in range(n)
        for c in range(n)
        if board[r][c] == 0 and _flips_for_move(board, n, r, c, turn)
    ]


def _apply(
    board: List[List[int]], move: Tuple[int, int],
    flips: List[Tuple[int, int]], turn: int,
) -> None:
    """着手を盤面に破壊的に適用する（_undo と対で使う）。"""
    board[move[0]][move[1]] = turn
    for r, c in flips:
        board[r][c] = turn


def _undo(
    board: List[List[int]], move: Tuple[int, int],
    flips: List[Tuple[int, int]], turn: int,
) -> None:
    """_apply の逆操作で盤面を元に戻す。"""
    board[move[0]][move[1]] = 0
    for r, c in flips:
        board[r][c] = -turn
```

- [ ] **Step 4: テストが通ることを確認**

Run: `uv run pytest tests/agents/test_negamax_agent.py -v`
Expected: PASS（全件）

- [ ] **Step 5: コミット**

```bash
git add agents/negamax_agent.py tests/agents/test_negamax_agent.py
git commit -m "feat: Negamax 探索用の make/unmake プリミティブを追加"
```

---

### Task 3: 評価関数（フェーズ係数・確定石・終局スコア）

**Files:**
- Modify: `agents/negamax_agent.py`
- Test: `tests/agents/test_negamax_agent.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/agents/test_negamax_agent.py` に追記:

```python
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

    def test_phase_coeffs_three_stages(self):
        n = 8
        early = _initial_board(n)                      # 4 石 → fill 0.0625
        mid = [[-1] * n for _ in range(4)] + [[0] * n for _ in range(4)]  # fill 0.5
        late = [[-1] * n for _ in range(7)] + [[0] * n]                   # fill 0.875
        assert _phase_coeffs(early, n) == _PHASE_COEFFS[0]
        assert _phase_coeffs(mid, n) == _PHASE_COEFFS[1]
        assert _phase_coeffs(late, n) == _PHASE_COEFFS[2]

    def test_stable_edge_count(self):
        board = [[0] * 8 for _ in range(8)]
        board[0][0] = board[0][1] = board[0][2] = -1   # 上辺の角から 3 連
        board[1][0] = -1                               # 左辺の角から 2 連目
        assert _stable_edge_count(board, 8, -1) == 4
        assert _stable_edge_count(board, 8, 1) == 0

    def test_stable_edge_count_no_corner_means_zero(self):
        board = [[0] * 8 for _ in range(8)]
        board[0][3] = -1   # 角に接続しない辺石は数えない
        assert _stable_edge_count(board, 8, -1) == 0

    def test_disc_diff(self):
        board = _initial_board(8)
        board[0][0] = -1
        assert _disc_diff(board, -1) == 1
        assert _disc_diff(board, 1) == -1

    def test_terminal_score_scale(self):
        board = _initial_board(8)
        board[0][0] = -1
        assert _terminal_score(board, -1) == 10000
        assert _terminal_score(board, 1) == -10000

    def test_evaluate_is_symmetric(self):
        """同一局面で手番を入れ替えると符号が反転する。"""
        board = _initial_board(8)
        board[2][3] = -1
        assert _evaluate(board, 8, -1) == pytest.approx(-_evaluate(board, 8, 1))

    def test_evaluate_prefers_corner(self):
        """角を持つ側の評価が高い。"""
        board = _initial_board(8)
        with_corner = [row[:] for row in board]
        with_corner[0][0] = -1
        assert _evaluate(with_corner, 8, -1) > _evaluate(board, 8, -1)
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `uv run pytest tests/agents/test_negamax_agent.py::TestEvaluation -v`
Expected: FAIL（ImportError）

- [ ] **Step 3: 実装を書く**

`agents/negamax_agent.py` に追記:

```python
# 終局時の確定スコアの倍率。ヒューリスティック値と桁で確実に区別する
_TERMINAL_SCALE = 10000

# ゲームフェーズ係数: (位置重み, mobility, 角, 確定石, 石差)
_PHASE_COEFFS = (
    (1.0, 8.0, 25.0, 10.0, 0.0),   # 序盤 (fill < 0.33)
    (1.0, 6.0, 30.0, 15.0, 0.0),   # 中盤 (0.33 <= fill <= 0.70)
    (0.3, 2.0, 30.0, 20.0, 5.0),   # 終盤 (fill > 0.70)
)
_EARLY_FILL = 0.33
_MID_FILL = 0.70


def _phase_coeffs(board: List[List[int]], n: int) -> Tuple[float, ...]:
    """盤面の埋まり具合からゲームフェーズの係数組を返す。"""
    stones = sum(1 for row in board for v in row if v != 0)
    fill = stones / (n * n)
    if fill < _EARLY_FILL:
        return _PHASE_COEFFS[0]
    if fill <= _MID_FILL:
        return _PHASE_COEFFS[1]
    return _PHASE_COEFFS[2]


def _stable_edge_count(board: List[List[int]], n: int, color: int) -> int:
    """各角から辺に沿って連続する color の石を数える（簡易確定石カウント）。"""
    stable: set = set()
    corners = (
        (0, 0, (0, 1), (1, 0)),
        (0, n - 1, (0, -1), (1, 0)),
        (n - 1, 0, (0, 1), (-1, 0)),
        (n - 1, n - 1, (0, -1), (-1, 0)),
    )
    for r0, c0, d1, d2 in corners:
        if board[r0][c0] != color:
            continue
        for dr, dc in (d1, d2):
            r, c = r0, c0
            while 0 <= r < n and 0 <= c < n and board[r][c] == color:
                stable.add((r, c))
                r += dr
                c += dc
    return len(stable)


def _disc_diff(board: List[List[int]], turn: int) -> int:
    """手番側から見た石差。"""
    return turn * sum(v for row in board for v in row)


def _terminal_score(board: List[List[int]], turn: int) -> float:
    """終局局面の確定スコア（手番側視点）。"""
    return float(_disc_diff(board, turn) * _TERMINAL_SCALE)


def _evaluate(board: List[List[int]], n: int, turn: int) -> float:
    """手番側から見たヒューリスティック評価値。"""
    w_pos, w_mob, w_corner, w_stable, w_disc = _phase_coeffs(board, n)
    weights = _build_weight_table(n)
    pos = 0
    disc = 0
    for r in range(n):
        for c in range(n):
            v = board[r][c]
            if v != 0:
                pos += v * weights[r][c]
                disc += v
    mobility = len(_valid_moves(board, n, turn)) - len(_valid_moves(board, n, -turn))
    corners = sum(board[r][c] for r in (0, n - 1) for c in (0, n - 1))
    stable = _stable_edge_count(board, n, turn) - _stable_edge_count(board, n, -turn)
    return (
        w_pos * pos * turn
        + w_mob * mobility
        + w_corner * corners * turn
        + w_stable * stable
        + w_disc * disc * turn
    )
```

- [ ] **Step 4: テストが通ることを確認**

Run: `uv run pytest tests/agents/test_negamax_agent.py -v`
Expected: PASS（全件）

- [ ] **Step 5: コミット**

```bash
git add agents/negamax_agent.py tests/agents/test_negamax_agent.py
git commit -m "feat: Negamax のフェーズ別評価関数と確定石カウントを追加"
```

---

### Task 4: NegamaxAgent 本体（反復深化・時間管理・パス処理）

**Files:**
- Modify: `agents/negamax_agent.py`
- Test: `tests/agents/test_negamax_agent.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/agents/test_negamax_agent.py` に追記:

```python
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

    def test_no_valid_moves_returns_none(self):
        board = [[-1] * 8 for _ in range(8)]   # 黒で埋め尽くし → 合法手なし
        game = _make_game(board, turn=1)
        assert _deterministic_agent().play(game) is None

    def test_single_move_returned_without_search(self):
        game = _make_game(_initial_board(8), turn=-1)
        game.get_valid_moves.return_value = [(2, 3)]
        assert _deterministic_agent().play(game) == (2, 3)

    def test_returns_legal_move_from_initial_position(self):
        game = _make_game(_initial_board(8), turn=-1)
        move = _deterministic_agent().play(game)
        assert move in game.board.get_valid_moves(-1)

    def test_takes_corner_when_available(self):
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

    def test_returns_legal_move_with_tiny_time_limit(self):
        """time_limit_ms=1 でも depth 1 の結果で合法手を返す。"""
        agent = NegamaxAgent(time_limit_ms=1)
        game = _make_game(_initial_board(8), turn=-1)
        move = agent.play(game)
        assert move in game.board.get_valid_moves(-1)

    def test_deterministic_same_input_same_output(self):
        game1 = _make_game(_initial_board(8), turn=-1)
        game2 = _make_game(_initial_board(8), turn=-1)
        assert _deterministic_agent().play(game1) == _deterministic_agent().play(game2)


class TestEndgameAndPass:
    """終盤読み切りとパス処理のテスト。"""

    def test_endgame_solver_picks_winning_move(self):
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

    def test_negamax_pass_switches_turn_without_consuming_depth(self):
        """手番側に合法手がなく相手にある局面では手番交代して探索を続ける。"""
        # 白 (0,0) を黒 (0,1) が隣接: 黒に合法手なし、白は (0,2) に打てる
        board = [[0] * 4 for _ in range(4)]
        board[0][0] = 1
        board[0][1] = -1
        agent = _deterministic_agent()
        agent._deadline = float("inf")
        agent._node_count = 0
        value = agent._negamax(board, 4, -1, 2, float("-inf"), float("inf"),
                               endgame=False, passed=False)
        assert abs(value) < 10000   # 終局スコアではなく通常の評価値が返る

    def test_negamax_double_pass_returns_terminal_score(self):
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

    def test_negamax_raises_timeout_when_deadline_passed(self):
        agent = NegamaxAgent(time_limit_ms=10**9)
        agent._deadline = 0.0           # 過去のデッドライン
        agent._node_count = 511         # 次のノードで時刻チェックが走る
        board = _initial_board(8)
        with pytest.raises(_SearchTimeout):
            agent._negamax(board, 8, -1, 3, float("-inf"), float("inf"),
                           endgame=False, passed=False)

    def test_play_survives_mid_search_timeout(self, monkeypatch):
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
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `uv run pytest tests/agents/test_negamax_agent.py -v`
Expected: FAIL（`ImportError: cannot import name 'NegamaxAgent'`）

- [ ] **Step 3: 実装を書く**

`agents/negamax_agent.py` に追記（ファイル先頭の import 群に `time` と
`from .base_agent import Agent`、`TYPE_CHECKING` ブロックを追加）:

```python
import time
from typing import TYPE_CHECKING

from .base_agent import Agent

if TYPE_CHECKING:
    from game import Game

# 時刻チェックを行うノード数の間隔（time.monotonic 呼び出しの間引き）
_NODES_PER_TIME_CHECK = 512


class _SearchTimeout(Exception):
    """探索の時間切れを示す内部例外。"""


class NegamaxAgent(Agent):
    """Negamax + アルファベータ枝刈りで先読みする AI エージェント。

    反復深化により常に時間内で読めた最深の結果を返す。
    終盤（空きマスが endgame_empties 以下）は石差のみで完全読み切りを行う。
    乱択を使わないため、max_depth を固定すれば完全に決定論的。
    """

    def __init__(
        self,
        time_limit_ms: int = 3000,
        max_depth: int = 60,
        endgame_empties: int = 12,
    ) -> None:
        """NegamaxAgent を初期化します。

        Args:
            time_limit_ms: 思考時間の上限（ミリ秒）。
            max_depth: 探索深さの上限。テストでは小さく固定して決定論化する。
            endgame_empties: 終盤読み切りに切り替える空きマス数の閾値。
        """
        self.time_limit_ms = time_limit_ms
        self.max_depth = max_depth
        self.endgame_empties = endgame_empties
        self._deadline = 0.0
        self._node_count = 0

    def play(self, game: 'Game') -> Optional[Tuple[int, int]]:
        """反復深化探索で最善手を選択します。

        Args:
            game: 現在のゲーム状態。

        Returns:
            (row, col) のタプル、または合法手がない場合は None。
        """
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            return None
        if len(valid_moves) == 1:
            return valid_moves[0]  # 有効な手が 1 つなら探索不要

        board = [row[:] for row in game.get_board()]
        n = len(board)
        turn = game.turn
        empties = sum(row.count(0) for row in board)
        endgame = empties <= self.endgame_empties
        depth_cap = min(self.max_depth, empties)

        start = time.monotonic()
        self._deadline = start + self.time_limit_ms / 1000.0
        self._node_count = 0

        best_move: Tuple[int, int] = valid_moves[0]
        depth = 1
        while depth <= depth_cap:
            try:
                best_move = self._search_root(
                    board, n, turn, depth, endgame, pv=best_move
                )
            except _SearchTimeout:
                break
            if depth >= empties:
                break  # 完全読み切り済み
            elapsed = time.monotonic() - start
            remaining = self._deadline - time.monotonic()
            if remaining < elapsed:
                break  # 次の深さは完走できる見込みがない
            depth += 1
        return best_move

    def _search_root(
        self,
        board: List[List[int]],
        n: int,
        turn: int,
        depth: int,
        endgame: bool,
        pv: Optional[Tuple[int, int]] = None,
    ) -> Tuple[int, int]:
        """ルート局面を深さ depth で探索し最善手を返す。"""
        moves = self._ordered_moves(board, n, turn)
        if pv is not None:
            moves.sort(key=lambda mf: mf[0] != pv)  # 前深さの最善手を先頭へ
        alpha = float("-inf")
        beta = float("inf")
        best_score = float("-inf")
        best_move = moves[0][0]
        for move, flips in moves:
            _apply(board, move, flips, turn)
            try:
                score = -self._negamax(
                    board, n, -turn, depth - 1, -beta, -alpha,
                    endgame=endgame, passed=False,
                )
            finally:
                _undo(board, move, flips, turn)
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)
        return best_move

    def _negamax(
        self,
        board: List[List[int]],
        n: int,
        turn: int,
        depth: int,
        alpha: float,
        beta: float,
        endgame: bool,
        passed: bool,
    ) -> float:
        """手番側視点の negamax 値を返す（アルファベータ枝刈り付き）。"""
        self._node_count += 1
        if (
            self._node_count % _NODES_PER_TIME_CHECK == 0
            and time.monotonic() > self._deadline
        ):
            raise _SearchTimeout()

        if depth <= 0:
            if endgame:
                return float(_disc_diff(board, turn))
            return _evaluate(board, n, turn)

        moves = self._ordered_moves(board, n, turn)
        if not moves:
            if passed:
                return _terminal_score(board, turn)  # 双方パス → 終局
            # 深さを消費せず手番交代（passed=True で無限再帰を防止）
            return -self._negamax(
                board, n, -turn, depth, -beta, -alpha,
                endgame=endgame, passed=True,
            )

        best = float("-inf")
        for move, flips in moves:
            _apply(board, move, flips, turn)
            try:
                score = -self._negamax(
                    board, n, -turn, depth - 1, -beta, -alpha,
                    endgame=endgame, passed=False,
                )
            finally:
                _undo(board, move, flips, turn)
            best = max(best, score)
            alpha = max(alpha, score)
            if alpha >= beta:
                break  # ベータカット
        return best

    def _ordered_moves(
        self, board: List[List[int]], n: int, turn: int
    ) -> List[Tuple[Tuple[int, int], List[Tuple[int, int]]]]:
        """合法手を (move, flips) のリストで返す（位置重み降順）。

        Python の sort は安定なので、同重みの手は row-major 順が保たれ
        探索は完全に決定論的になる。
        """
        weights = _build_weight_table(n)
        moves = [
            ((r, c), flips)
            for r in range(n)
            for c in range(n)
            if board[r][c] == 0
            for flips in (_flips_for_move(board, n, r, c, turn),)
            if flips
        ]
        moves.sort(key=lambda mf: weights[mf[0][0]][mf[0][1]], reverse=True)
        return moves
```

- [ ] **Step 4: テストが通ることを確認**

Run: `uv run pytest tests/agents/test_negamax_agent.py -v`
Expected: PASS（全件）

- [ ] **Step 5: リントと型チェック**

Run: `uv run ruff check agents/negamax_agent.py tests/agents/test_negamax_agent.py && uv run mypy agents/negamax_agent.py`
Expected: エラーなし

- [ ] **Step 6: コミット**

```bash
git add agents/negamax_agent.py tests/agents/test_negamax_agent.py
git commit -m "feat: NegamaxAgent 本体（反復深化・時間管理・パス処理）を実装"
```

---

### Task 5: API サーバーへの登録

**Files:**
- Modify: `server/api_server.py:39-47`（import）、`server/api_server.py:51`（VALID_AGENT_TYPES）、`server/api_server.py:72-82`（_select_agent）
- Test: `tests/server/test_api_server.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/server/test_api_server.py` の `test_play_agent_type_mcts`（行 93-99）の直後に追記:

```python
    def test_play_agent_type_negamax(self):
        payload = {"board": VALID_BOARD, "turn": 1, "agent_type": "negamax"}
        with patch("server.api_server.NegamaxAgent") as MockNegamax:
            MockNegamax.return_value.play.return_value = (2, 3)
            response = self.client.post("/play", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["move"], [2, 3])

    def test_negamax_time_limit_env_var(self):
        """NEGAMAX_TIME_LIMIT_MS 環境変数が反映される。"""
        import os
        from unittest.mock import patch as mock_patch
        with mock_patch.dict(os.environ, {"NEGAMAX_TIME_LIMIT_MS": "123"}):
            from server.api_server import _select_agent
            agent = _select_agent("negamax")
        self.assertEqual(agent.time_limit_ms, 123)
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `uv run pytest tests/server/test_api_server.py -v -k negamax`
Expected: FAIL（`AttributeError: ... has no attribute 'NegamaxAgent'`）

- [ ] **Step 3: サーバーに登録する**

`server/api_server.py` の try ブロック（行 39-47）に import を追加:

```python
    from agents.negamax_agent import NegamaxAgent
```

行 51 を変更:

```python
VALID_AGENT_TYPES = frozenset({"first", "random", "gain", "mcts", "negamax"})
```

`_select_agent()`（行 72-82）の `mcts` 分岐の後に追加:

```python
    if agent_type == "negamax":
        return NegamaxAgent(
            time_limit_ms=int(os.getenv("NEGAMAX_TIME_LIMIT_MS", "3000"))
        )
```

- [ ] **Step 4: テストが通ることを確認**

Run: `uv run pytest tests/server/ -v`
Expected: PASS（全件）

- [ ] **Step 5: コミット**

```bash
git add server/api_server.py tests/server/test_api_server.py
git commit -m "feat: API サーバーに agent_type=negamax を登録"
```

---

### Task 6: 統合テストと conftest の環境変数

**Files:**
- Modify: `tests/integration/test_api_integration.py:57`、`tests/integration/conftest.py:42-47`

- [ ] **Step 1: 統合テストに negamax を追加（先に失敗を確認）**

`tests/integration/test_api_integration.py` 行 57 を変更:

```python
        for agent_type in ("first", "random", "gain", "negamax"):
```

- [ ] **Step 2: conftest に時間短縮の環境変数を追加**

`tests/integration/conftest.py` の env 設定ブロック（行 42-47）に追加:

```python
    env["NEGAMAX_TIME_LIMIT_MS"] = "200"   # CI を遅くしないため思考時間を短縮
```

- [ ] **Step 3: 統合テストが通ることを確認**

Run: `uv run pytest tests/integration/ -v`
Expected: PASS（全件。negamax のリクエストが 200 を返す）

- [ ] **Step 4: コミット**

```bash
git add tests/integration/test_api_integration.py tests/integration/conftest.py
git commit -m "test: negamax の統合テストを追加し CI 用に思考時間を短縮"
```

---

### Task 7: GUI への登録

**Files:**
- Modify: `config/agents_config.py:18-61`（AGENT_DEFINITIONS）

- [ ] **Step 1: AGENT_DEFINITIONS に追加**

`config/agents_config.py` の `'id': 4`（MCTS）エントリの後に追加:

```python
    {
        'id': 5,
        'class': ApiAgent,
        'display_name': 'API (Negamax)',
        'params': {
            'api_url': 'http://127.0.0.1:5001/play',
            'agent_type': 'negamax',
        }
    },
```

- [ ] **Step 2: 既存テストが全て通ることを確認**

Run: `uv run pytest tests/ --ignore=tests/integration -v`
Expected: PASS（config 系テストは AGENT_DEFINITIONS を動的に走査するため追従修正不要）。
もし選択肢数を固定値で検証しているテストが失敗したら、期待値を 5 → 6 に更新する。

- [ ] **Step 3: コミット**

```bash
git add config/agents_config.py
git commit -m "feat: GUI のプレイヤー選択肢に API (Negamax) を追加"
```

---

### Task 8: 強さ検証ベンチマークスクリプト

**Files:**
- Create: `scripts/benchmark_agents.py`

- [ ] **Step 1: スクリプトを書く**

`scripts/benchmark_agents.py` を新規作成（CI 対象外・手動実行用）:

```python
#!/usr/bin/env python3
"""NegamaxAgent vs MonteCarloTreeSearchAgent の自動対戦ベンチマーク。

使い方:
    uv run python scripts/benchmark_agents.py --games 20 --time-limit-ms 1000

受け入れ基準: Negamax (time_limit_ms=1000) が既定 MCTS に勝率 80% 以上。
"""
import argparse
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.mcts_agent import MonteCarloTreeSearchAgent  # noqa: E402
from agents.negamax_agent import NegamaxAgent  # noqa: E402
from game import Game  # noqa: E402


def play_one_game(black_agent, white_agent, board_size: int) -> int:
    """1 局対戦し、石差（黒 - 白）を返す。

    game.py の公開 API（place_stone / switch_turn / check_game_over）を使う。
    place_stone はキャッシュ無効化と履歴管理を行うため、内部状態を直接
    触らない。両者が着手不能になると check_game_over が game_over を立てる。
    """
    game = Game(board_size=board_size)   # game.turn は -1（黒）で開始
    while not game.game_over:
        agent = black_agent if game.turn == -1 else white_agent
        move = agent.play(game)
        if move is not None:
            game.place_stone(move[0], move[1])
        game.switch_turn()
        game.check_game_over()
    black, white = game.board.count_stones()
    return black - white


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=int, default=20)
    parser.add_argument("--time-limit-ms", type=int, default=1000)
    parser.add_argument("--board-size", type=int, default=8)
    args = parser.parse_args()

    wins = losses = draws = 0
    start = time.monotonic()
    for i in range(args.games):
        random.seed(i)  # MCTS 側の乱数を再現可能にする
        negamax = NegamaxAgent(time_limit_ms=args.time_limit_ms)
        mcts = MonteCarloTreeSearchAgent()
        if i % 2 == 0:   # 先手/後手を交互に入れ替える
            diff = play_one_game(negamax, mcts, args.board_size)
        else:
            diff = -play_one_game(mcts, negamax, args.board_size)
        if diff > 0:
            wins += 1
        elif diff < 0:
            losses += 1
        else:
            draws += 1
        print(f"game {i + 1:3d}: negamax 石差 {diff:+d} "
              f"(W{wins} / L{losses} / D{draws})")

    elapsed = time.monotonic() - start
    rate = wins / args.games * 100
    print("-" * 50)
    print(f"games={args.games} 勝率 {rate:.0f}% "
          f"(W{wins} / L{losses} / D{draws}) 所要 {elapsed:.0f}s")
    print("受け入れ基準 (>= 80%):", "PASS" if rate >= 80 else "FAIL")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: ベンチマークを実行して勝率を確認**

Run: `uv run python scripts/benchmark_agents.py --games 20 --time-limit-ms 1000`
Expected: `受け入れ基準 (>= 80%): PASS`

勝率 80% 未満の場合は `agents/negamax_agent.py` の `_PHASE_COEFFS` を調整して再実行する
（mobility 系数を上げる / X マスのペナルティを強める、の順に試す）。

- [ ] **Step 3: コミット**

```bash
git add scripts/benchmark_agents.py
git commit -m "feat: Negamax vs MCTS の対戦ベンチマークスクリプトを追加"
```

---

### Task 9: ドキュメント更新と全体検証

**Files:**
- Modify: `README.md`（AI エージェント一覧・構成図・テスト数）

- [ ] **Step 1: README.md を更新**

- AI エージェント一覧の表に `API (Negamax)` を追加し、戦略説明を 1 行で記載:
  「アルファベータ枝刈り + 反復深化 + 終盤完全読み切り。位置重み・着手可能数・確定石で評価」
- Mermaid 構成図の API Server サブグラフに `Negamax` を追加
- `POST /play` の `agent_type` 列挙に `negamax` を追加
- テスト数の記載を実測値に更新（`uv run pytest --collect-only -q | tail -1` で確認）

- [ ] **Step 2: CI チェック一式を実行**

Run: `bash scripts/ci_check.sh`
Expected: ruff / mypy / pytest / カバレッジ全て成功（カバレッジ 98% 以上を維持）

カバレッジ不足の行が `agents/negamax_agent.py` にあれば、該当分岐のテストを
`tests/agents/test_negamax_agent.py` に追加する。

- [ ] **Step 3: コミット**

```bash
git add README.md
git commit -m "docs: README に Negamax エージェントを追記"
```

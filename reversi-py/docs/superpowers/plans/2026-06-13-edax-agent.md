# EdaxAgent（外部エンジン統合）実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 世界最強クラスの外部エンジン Edax を常駐 subprocess として統合し、`agent_type="edax"` の API プレイヤーを追加する。

**Architecture:** `agents/edax_engine.py`（プロセス管理 + 盤面変換、`popen` 注入でモック可能）と `agents/edax_agent.py`（`Agent` 実装の薄いアダプタ）の 2 ファイル構成。8x8 以外の盤面は `NegamaxAgent` に内部フォールバック。バイナリ未導入時は API が 503 を返す。CI では `EDAX_PATH` 未設定のため統合テストは skip され、単体テストはフェイクプロセスで全分岐をカバーする。

**Tech Stack:** Python 3（subprocess / threading / queue / re）、pytest、FastAPI TestClient、Edax 4.x（GPL v3・リポジトリ非同梱）。

**参照仕様書:** `docs/superpowers/specs/2026-06-13-edax-agent-design.md`

**前提:** `docs/superpowers/plans/2026-06-13-negamax-agent.md` が実装済みであること
（フォールバック先に `NegamaxAgent` を使う。未実装の場合は `MonteCarloTreeSearchAgent` に読み替える）。

**実行コマンドの前提:** リポジトリの `reversi-py/` ディレクトリで `uv run pytest ...` を実行する。

---

### Task 1: 盤面変換の純粋関数

**Files:**
- Create: `agents/edax_engine.py`
- Test: `tests/agents/test_edax_engine.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/agents/test_edax_engine.py` を新規作成:

```python
"""EdaxEngine とその変換関数の単体テスト（実バイナリ不要）。"""
import pytest

from agents.edax_engine import board_to_edax, coord_to_rowcol, rowcol_to_coord


def _initial_board() -> list:
    board = [[0] * 8 for _ in range(8)]
    board[3][3] = board[4][4] = 1     # 白
    board[3][4] = board[4][3] = -1    # 黒
    return board


class TestBoardConversion:
    """盤面・座標変換のテスト。"""

    def test_board_to_edax_initial_position(self):
        result = board_to_edax(_initial_board(), turn=-1)
        cells, turn_char = result.split()
        assert len(cells) == 64
        assert cells[3 * 8 + 3] == "O"   # (3,3) 白
        assert cells[3 * 8 + 4] == "X"   # (3,4) 黒
        assert cells[0] == "-"           # 空マス
        assert turn_char == "X"          # 黒番

    def test_board_to_edax_white_turn(self):
        assert board_to_edax(_initial_board(), turn=1).endswith(" O")

    @pytest.mark.parametrize("coord,expected", [
        ("a1", (0, 0)),
        ("f5", (4, 5)),
        ("h8", (7, 7)),
        ("F5", (4, 5)),   # 大文字も受け付ける
    ])
    def test_coord_to_rowcol(self, coord, expected):
        assert coord_to_rowcol(coord) == expected

    @pytest.mark.parametrize("row,col,expected", [
        (0, 0, "a1"),
        (4, 5, "f5"),
        (7, 7, "h8"),
    ])
    def test_rowcol_to_coord(self, row, col, expected):
        assert rowcol_to_coord(row, col) == expected

    def test_roundtrip(self):
        for row in range(8):
            for col in range(8):
                assert coord_to_rowcol(rowcol_to_coord(row, col)) == (row, col)
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `uv run pytest tests/agents/test_edax_engine.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'agents.edax_engine'`）

- [ ] **Step 3: 最小実装を書く**

`agents/edax_engine.py` を新規作成:

```python
# agents/edax_engine.py
"""Edax 外部エンジンのプロセス管理と盤面・座標変換。

Edax (GPL v3) はリポジトリに同梱せず、外部プロセスとして起動する。
設計書: docs/superpowers/specs/2026-06-13-edax-agent-design.md
"""
from typing import List, Tuple

# 内部表現 → Edax 文字のマッピング（黒 = X、白 = O、空 = -）
_CELL_CHARS = {-1: "X", 1: "O", 0: "-"}


class EdaxProtocolError(Exception):
    """Edax の応答が解釈できない・不正な着手を返したことを示す。"""


class EdaxNotAvailableError(Exception):
    """Edax バイナリが未導入・起動不能であることを示す。"""


def board_to_edax(board: List[List[int]], turn: int) -> str:
    """2 次元リスト盤面を Edax の setboard 形式文字列に変換する。

    Args:
        board: 8x8 の盤面（-1: 黒、0: 空、1: 白）。
        turn: 手番（-1: 黒、1: 白）。

    Returns:
        "64 文字の盤面 + 半角スペース + 手番 1 文字" の文字列。
    """
    cells = "".join(_CELL_CHARS[v] for row in board for v in row)
    return f"{cells} {_CELL_CHARS[turn]}"


def coord_to_rowcol(coord: str) -> Tuple[int, int]:
    """Edax の座標表記（例 "f5"）を (row, col) に変換する。"""
    col = ord(coord[0].lower()) - ord("a")
    row = int(coord[1:]) - 1
    return row, col


def rowcol_to_coord(row: int, col: int) -> str:
    """(row, col) を Edax の座標表記（例 "f5"）に変換する。"""
    return f"{chr(ord('a') + col)}{row + 1}"
```

- [ ] **Step 4: テストが通ることを確認**

Run: `uv run pytest tests/agents/test_edax_engine.py -v`
Expected: PASS（全件）

- [ ] **Step 5: コミット**

```bash
git add agents/edax_engine.py tests/agents/test_edax_engine.py
git commit -m "feat: Edax の盤面・座標変換関数を追加"
```

---

### Task 2: EdaxEngine プロセス管理クラス

**Files:**
- Modify: `agents/edax_engine.py`
- Test: `tests/agents/test_edax_engine.py`

- [ ] **Step 1: フェイクプロセスと失敗するテストを書く**

`tests/agents/test_edax_engine.py` に追記:

```python
import io
import os
import stat

from agents.edax_engine import (
    EdaxEngine,
    EdaxNotAvailableError,
    EdaxProtocolError,
)


class FakeProc:
    """Popen 互換のフェイクプロセス。stdout 行をスクリプトとして再生する。"""

    def __init__(self, stdout_lines, crash_after=None):
        self.stdin = io.StringIO()
        self.stdout = io.StringIO("".join(stdout_lines))
        self._crash_after = crash_after
        self._writes = 0
        self.killed = False
        self.terminated = False

    def poll(self):
        if self._crash_after is not None and self._writes >= self._crash_after:
            return 1   # クラッシュ済み
        return None

    def kill(self):
        self.killed = True

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        return 0


def _make_engine(tmp_path, procs):
    """フェイク popen を注入した EdaxEngine を作る。

    procs: 起動のたびに順番に返す FakeProc のリスト。
    """
    binary = tmp_path / "edax"
    binary.write_text("#!/bin/sh\n")
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    it = iter(procs)

    def fake_popen(*args, **kwargs):
        proc = next(it)
        proc.popen_args = (args, kwargs)
        return proc

    return EdaxEngine(
        edax_path=str(binary), level=5, move_time=1.0, timeout=0.5,
        popen=fake_popen,
    )


class TestEdaxEngine:
    """EdaxEngine のプロセス管理テスト（フェイクプロセス使用）。"""

    def test_is_available_false_when_path_empty(self):
        engine = EdaxEngine(edax_path="", level=5, move_time=1.0, timeout=0.5)
        assert engine.is_available() is False

    def test_is_available_false_when_not_executable(self, tmp_path):
        binary = tmp_path / "edax"
        binary.write_text("")
        binary.chmod(0o644)
        engine = EdaxEngine(edax_path=str(binary), level=5,
                            move_time=1.0, timeout=0.5)
        assert engine.is_available() is False

    def test_is_available_true(self, tmp_path):
        engine = _make_engine(tmp_path, [])
        assert engine.is_available() is True

    def test_get_move_parses_response(self, tmp_path):
        proc = FakeProc(["Edax 4.4\n", "Edax plays F5\n"])
        engine = _make_engine(tmp_path, [proc])
        move = engine.get_move("-" * 64 + " X")
        assert move == "f5"
        sent = proc.stdin.getvalue()
        assert "setboard" in sent
        assert "go" in sent

    def test_get_move_pass_returns_none(self, tmp_path):
        proc = FakeProc(["Edax plays PS\n"])
        engine = _make_engine(tmp_path, [proc])
        assert engine.get_move("-" * 64 + " X") is None

    def test_get_move_restarts_after_crash(self, tmp_path):
        crashed = FakeProc([], crash_after=0)      # 起動直後にクラッシュ判定
        healthy = FakeProc(["Edax plays D3\n"])
        engine = _make_engine(tmp_path, [crashed, healthy])
        engine._ensure_started()                   # 1 つ目のプロセスで起動
        assert engine.get_move("-" * 64 + " X") == "d3"   # 再起動して成功

    def test_get_move_timeout_kills_and_raises(self, tmp_path):
        silent = FakeProc([])                      # 何も出力しない → タイムアウト
        silent2 = FakeProc([])
        engine = _make_engine(tmp_path, [silent, silent2])
        with pytest.raises(EdaxProtocolError):
            engine.get_move("-" * 64 + " X")
        assert silent.killed or silent2.killed

    def test_get_move_raises_when_not_available(self):
        engine = EdaxEngine(edax_path="", level=5, move_time=1.0, timeout=0.5)
        with pytest.raises(EdaxNotAvailableError):
            engine.get_move("-" * 64 + " X")

    def test_shutdown_is_idempotent(self, tmp_path):
        proc = FakeProc(["Edax plays F5\n"])
        engine = _make_engine(tmp_path, [proc])
        engine.get_move("-" * 64 + " X")
        engine.shutdown()
        engine.shutdown()   # 2 回呼んでも例外にならない
        assert proc.terminated or proc.killed
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `uv run pytest tests/agents/test_edax_engine.py::TestEdaxEngine -v`
Expected: FAIL（`ImportError: cannot import name 'EdaxEngine'`）

- [ ] **Step 3: EdaxEngine を実装する**

`agents/edax_engine.py` に追記:

```python
import atexit
import logging
import os
import queue
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# "Edax plays F5" / "Edax plays PS" 形式の応答から着手を抽出する
_MOVE_RE = re.compile(r"plays\s+([A-Ha-h][1-8]|PS|pass)", re.IGNORECASE)
_PASS_TOKENS = frozenset({"ps", "pass"})


class EdaxEngine:
    """Edax プロセスを常駐管理し、setboard/go プロトコルで着手を取得する。

    スレッド安全: get_move 全体をロックで直列化する（FastAPI の
    スレッドプールから並行に呼ばれるため）。
    テスト容易性: popen を注入可能にしてフェイクプロセスで全分岐を検証する。
    """

    def __init__(
        self,
        edax_path: str,
        level: int = 12,
        move_time: float = 3.5,
        timeout: float = 4.0,
        popen: Callable = subprocess.Popen,
    ) -> None:
        """EdaxEngine を初期化します（プロセスはまだ起動しない）。

        Args:
            edax_path: Edax バイナリの絶対パス。空文字なら無効。
            level: 思考レベル（探索深さ）。
            move_time: 1 手の最大思考秒数。
            timeout: 応答待ちの打ち切り秒数。
            popen: プロセス生成関数（テストでフェイクに差し替え可能）。
        """
        self._edax_path = edax_path
        self._level = level
        self._move_time = move_time
        self._timeout = timeout
        self._popen = popen
        self._proc = None
        self._queue: Optional[queue.Queue] = None
        self._lock = threading.Lock()
        atexit.register(self.shutdown)

    def is_available(self) -> bool:
        """バイナリが存在し実行可能かを返す（プロセスは起動しない）。"""
        return (
            bool(self._edax_path)
            and os.path.isfile(self._edax_path)
            and os.access(self._edax_path, os.X_OK)
        )

    def get_move(self, board_str: str) -> Optional[str]:
        """setboard → go で着手を取得する。パスなら None。

        Args:
            board_str: board_to_edax() が返す setboard 引数文字列。

        Returns:
            着手の座標表記（例 "f5"、小文字）、パスの場合は None。

        Raises:
            EdaxNotAvailableError: バイナリ未導入・起動不能。
            EdaxProtocolError: 応答のタイムアウト・解釈不能（再起動リトライ後）。
        """
        if not self.is_available():
            raise EdaxNotAvailableError("edax engine is not available")
        with self._lock:
            try:
                return self._get_move_locked(board_str)
            except EdaxProtocolError:
                # 状態不定の可能性があるため再起動して 1 回だけリトライする
                self._restart()
                return self._get_move_locked(board_str)

    def _get_move_locked(self, board_str: str) -> Optional[str]:
        """ロック取得済み前提で 1 回分の setboard/go を実行する。"""
        self._ensure_started()
        try:
            self._send(f"setboard {board_str}")
            self._send("go")
        except (BrokenPipeError, OSError) as e:
            raise EdaxProtocolError(f"failed to write to edax: {e}") from e
        return self._read_move()

    def _ensure_started(self) -> None:
        """未起動またはクラッシュ済みならプロセスを起動する。"""
        if self._proc is not None and self._proc.poll() is None:
            return
        engine_dir = str(Path(self._edax_path).resolve().parent)
        self._proc = self._popen(
            [self._edax_path, "-q"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=engine_dir,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self._start_reader()
        self._send(f"level {self._level}")
        self._send(f"move-time {self._move_time}")

    def _start_reader(self) -> None:
        """stdout を読み続けて Queue に積む補助スレッドを起動する。"""
        self._queue = queue.Queue()
        proc = self._proc
        out_queue = self._queue

        def _pump() -> None:
            try:
                for line in proc.stdout:
                    out_queue.put(line)
            except (ValueError, OSError):
                pass   # プロセス終了によるストリームクローズは正常系

        threading.Thread(target=_pump, daemon=True).start()

    def _send(self, command: str) -> None:
        """コマンド 1 行を stdin に書き込む。"""
        assert self._proc is not None and self._proc.stdin is not None
        self._proc.stdin.write(command + "\n")
        if hasattr(self._proc.stdin, "flush"):
            self._proc.stdin.flush()

    def _read_move(self) -> Optional[str]:
        """応答行から着手を抽出する。timeout 秒で打ち切り。"""
        assert self._queue is not None
        deadline = time.monotonic() + self._timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self._kill()
                raise EdaxProtocolError("edax response timed out")
            try:
                line = self._queue.get(timeout=min(remaining, 0.1))
            except queue.Empty:
                continue
            match = _MOVE_RE.search(line)
            if match:
                token = match.group(1).lower()
                if token in _PASS_TOKENS:
                    return None
                return token

    def _restart(self) -> None:
        """プロセスを破棄して再起動する。"""
        self._kill()
        self._ensure_started()

    def _kill(self) -> None:
        """プロセスを強制終了して破棄する。"""
        if self._proc is not None:
            try:
                self._proc.kill()
            except OSError:
                pass
            self._proc = None

    def shutdown(self) -> None:
        """プロセスを後始末する（冪等）。atexit からも呼ばれる。"""
        proc = self._proc
        if proc is None:
            return
        self._proc = None
        try:
            if proc.poll() is None and proc.stdin is not None:
                proc.stdin.write("quit\n")
                if hasattr(proc.stdin, "flush"):
                    proc.stdin.flush()
            proc.terminate()
            proc.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired, ValueError):
            try:
                proc.kill()
            except OSError:
                pass
```

注意（実装時の調整ポイント）:
- FakeProc の `stdout` は `io.StringIO` のため `for line in proc.stdout` で全行を即座に読める。
  実プロセスではブロッキング読みになるが、補助スレッド + Queue 方式なので同じコードで動く。
- `test_get_move_timeout_kills_and_raises` では出力なし → `queue.Empty` ループ →
  デッドライン超過 → `_kill` + `EdaxProtocolError` → `get_move` が `_restart` して
  リトライ → 再びタイムアウト → 例外が呼び出し元へ伝播する。

- [ ] **Step 4: テストが通ることを確認**

Run: `uv run pytest tests/agents/test_edax_engine.py -v`
Expected: PASS（全件）

- [ ] **Step 5: リントと型チェック**

Run: `uv run ruff check agents/edax_engine.py tests/agents/test_edax_engine.py && uv run mypy agents/edax_engine.py`
Expected: エラーなし（`import time` はファイル先頭へ移動するなど isort 順に整理する）

- [ ] **Step 6: コミット**

```bash
git add agents/edax_engine.py tests/agents/test_edax_engine.py
git commit -m "feat: Edax 常駐プロセス管理クラス EdaxEngine を実装"
```

---

### Task 3: 共有エンジンシングルトンと EdaxAgent

**Files:**
- Modify: `agents/edax_engine.py`（シングルトン取得関数）
- Create: `agents/edax_agent.py`
- Test: `tests/agents/test_edax_agent.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/agents/test_edax_agent.py` を新規作成:

```python
"""EdaxAgent の単体テスト（エンジンはモック注入）。"""
from unittest.mock import Mock

import pytest

from agents.edax_agent import EdaxAgent
from agents.edax_engine import EdaxNotAvailableError, EdaxProtocolError


def _make_game(size: int = 8, turn: int = -1) -> Mock:
    from board import Board
    game = Mock()
    b = Board(board_size=size)
    game.board = b
    game.turn = turn
    game.get_board.return_value = [row[:] for row in b.board]
    game.get_board_size.return_value = size
    return game


class TestEdaxAgent:

    def test_play_returns_move_from_engine(self):
        engine = Mock()
        engine.is_available.return_value = True
        engine.get_move.return_value = "d3"   # (2, 3) は黒の合法手
        agent = EdaxAgent(engine=engine, fallback=Mock())
        assert agent.play(_make_game(turn=-1)) == (2, 3)

    def test_play_pass_returns_none(self):
        engine = Mock()
        engine.is_available.return_value = True
        engine.get_move.return_value = None
        agent = EdaxAgent(engine=engine, fallback=Mock())
        assert agent.play(_make_game(turn=-1)) is None

    def test_non_8x8_delegates_to_fallback(self):
        engine = Mock()
        fallback = Mock()
        fallback.play.return_value = (1, 2)
        agent = EdaxAgent(engine=engine, fallback=fallback)
        game = _make_game(size=6)
        assert agent.play(game) == (1, 2)
        fallback.play.assert_called_once_with(game)
        engine.get_move.assert_not_called()

    def test_engine_not_available_raises(self):
        engine = Mock()
        engine.is_available.return_value = False
        agent = EdaxAgent(engine=engine, fallback=Mock())
        with pytest.raises(EdaxNotAvailableError):
            agent.play(_make_game())

    def test_illegal_move_from_engine_raises_protocol_error(self):
        engine = Mock()
        engine.is_available.return_value = True
        engine.get_move.return_value = "a1"   # 初期局面では不合法手
        agent = EdaxAgent(engine=engine, fallback=Mock())
        with pytest.raises(EdaxProtocolError):
            agent.play(_make_game(turn=-1))

    def test_default_fallback_is_negamax(self):
        from agents.negamax_agent import NegamaxAgent
        agent = EdaxAgent(engine=Mock())
        assert isinstance(agent._fallback, NegamaxAgent)
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `uv run pytest tests/agents/test_edax_agent.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'agents.edax_agent'`）

- [ ] **Step 3: シングルトン取得関数とエージェントを実装する**

`agents/edax_engine.py` の末尾に追記:

```python
_shared_engine: Optional[EdaxEngine] = None
_shared_engine_lock = threading.Lock()


def get_shared_engine() -> EdaxEngine:
    """環境変数から設定したプロセス共有の EdaxEngine を返す。"""
    global _shared_engine
    with _shared_engine_lock:
        if _shared_engine is None:
            _shared_engine = EdaxEngine(
                edax_path=os.getenv("EDAX_PATH", ""),
                level=int(os.getenv("EDAX_LEVEL", "12")),
                move_time=float(os.getenv("EDAX_MOVE_TIME", "3.5")),
                timeout=float(os.getenv("EDAX_TIMEOUT", "4.0")),
            )
        return _shared_engine
```

`agents/edax_agent.py` を新規作成:

```python
# agents/edax_agent.py
"""外部エンジン Edax に着手を委譲する AI エージェント。"""
import logging
from typing import Optional, Tuple, TYPE_CHECKING

from .base_agent import Agent
from .edax_engine import (
    EdaxEngine,
    EdaxNotAvailableError,
    EdaxProtocolError,
    board_to_edax,
    coord_to_rowcol,
    get_shared_engine,
)
from .negamax_agent import NegamaxAgent

if TYPE_CHECKING:
    from game import Game

logger = logging.getLogger(__name__)

# Edax が対応する盤面サイズ（8x8 専用）
_EDAX_BOARD_SIZE = 8


class EdaxAgent(Agent):
    """Edax 外部エンジンで着手を決める最強クラスの AI エージェント。

    8x8 以外の盤面では fallback エージェントに委譲する。
    """

    def __init__(
        self,
        engine: Optional[EdaxEngine] = None,
        fallback: Optional[Agent] = None,
    ) -> None:
        """EdaxAgent を初期化します。

        Args:
            engine: 使用するエンジン。省略時はプロセス共有シングルトン。
            fallback: 非 8x8 盤面用の代替エージェント。省略時は NegamaxAgent。
        """
        self._engine = engine if engine is not None else get_shared_engine()
        self._fallback = fallback if fallback is not None else NegamaxAgent()

    def play(self, game: 'Game') -> Optional[Tuple[int, int]]:
        """Edax に問い合わせて着手を返します。

        Args:
            game: 現在のゲーム状態。

        Returns:
            (row, col) のタプル、またはパスの場合は None。

        Raises:
            EdaxNotAvailableError: エンジン未導入（API 層が 503 に変換）。
            EdaxProtocolError: エンジンが不合法手を返した（API 層が 500 に変換）。
        """
        if game.get_board_size() != _EDAX_BOARD_SIZE:
            logger.warning(
                "Edax は 8x8 専用のためフォールバックエージェントを使用します "
                "(board_size=%d)", game.get_board_size()
            )
            return self._fallback.play(game)

        if not self._engine.is_available():
            raise EdaxNotAvailableError("edax engine is not available")

        coord = self._engine.get_move(board_to_edax(game.get_board(), game.turn))
        if coord is None:
            return None

        move = coord_to_rowcol(coord)
        if move not in game.board.get_valid_moves(game.turn):
            raise EdaxProtocolError(
                f"edax returned an illegal move: {coord} -> {move}"
            )
        return move
```

- [ ] **Step 4: テストが通ることを確認**

Run: `uv run pytest tests/agents/test_edax_agent.py tests/agents/test_edax_engine.py -v`
Expected: PASS（全件）

- [ ] **Step 5: コミット**

```bash
git add agents/edax_engine.py agents/edax_agent.py tests/agents/test_edax_agent.py
git commit -m "feat: EdaxAgent（非 8x8 フォールバック付き）を実装"
```

---

### Task 4: API サーバーへの登録と 503 ハンドリング

**Files:**
- Modify: `server/api_server.py:39-47`（import）、`server/api_server.py:51`（VALID_AGENT_TYPES）、`server/api_server.py:72-82`（_select_agent）、`/play` の例外ハンドリング
- Test: `tests/server/test_api_server.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/server/test_api_server.py` に追記（クラス内、negamax テストの後）:

```python
    def test_play_agent_type_edax(self):
        payload = {"board": VALID_BOARD, "turn": 1, "agent_type": "edax"}
        with patch("server.api_server.EdaxAgent") as MockEdax:
            MockEdax.return_value.play.return_value = (2, 3)
            response = self.client.post("/play", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["move"], [2, 3])

    def test_play_edax_not_available_returns_503(self):
        from agents.edax_engine import EdaxNotAvailableError
        payload = {"board": VALID_BOARD, "turn": 1, "agent_type": "edax"}
        with patch("server.api_server.EdaxAgent") as MockEdax:
            MockEdax.return_value.play.side_effect = EdaxNotAvailableError(
                "edax engine is not available"
            )
            response = self.client.post("/play", json=payload)
        self.assertEqual(response.status_code, 503)
        self.assertIn("edax", response.json()["detail"])
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `uv run pytest tests/server/test_api_server.py -v -k edax`
Expected: FAIL（`AttributeError: ... has no attribute 'EdaxAgent'`）

- [ ] **Step 3: サーバーに登録する**

`server/api_server.py` の try ブロック（行 39-47）に import を追加:

```python
    from agents.edax_agent import EdaxAgent
    from agents.edax_engine import EdaxNotAvailableError
```

`VALID_AGENT_TYPES`（行 51）を変更:

```python
VALID_AGENT_TYPES = frozenset(
    {"first", "random", "gain", "mcts", "negamax", "edax"}
)
```

`_select_agent()` に分岐を追加:

```python
    if agent_type == "edax":
        return EdaxAgent()
```

`/play` のエージェント実行 try ブロック（`server/api_server.py:156-164`）を、
汎用 `except Exception`（500）の**前**に `EdaxNotAvailableError` ハンドラ（503）を
挿入する形に変更する。変更前:

```python
        try:
            agent = _select_agent(agent_type)
            move = agent.play(game)
        except Exception as e:
            logger.error(f"エージェント実行エラー: {e}", exc_info=False)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error getting move."
            )
```

変更後:

```python
        try:
            agent = _select_agent(agent_type)
            move = agent.play(game)
        except EdaxNotAvailableError as e:
            logger.warning(f"Edax engine unavailable: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="edax engine is not available",
            )
        except Exception as e:
            logger.error(f"エージェント実行エラー: {e}", exc_info=False)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error getting move."
            )
```

ここで送出した `HTTPException(503)` は外側の `except HTTPException: raise`
（`server/api_server.py:169-170`）でそのまま再送出され、汎用 500 ハンドラに
飲み込まれない。`EdaxProtocolError`（不合法手）は汎用 `except Exception` 経由で
500 になる（既存挙動どおりで意図的）。

- [ ] **Step 4: テストが通ることを確認**

Run: `uv run pytest tests/server/ -v`
Expected: PASS（全件）

- [ ] **Step 5: コミット**

```bash
git add server/api_server.py tests/server/test_api_server.py
git commit -m "feat: API サーバーに agent_type=edax と 503 ハンドリングを追加"
```

---

### Task 5: GUI への登録

**Files:**
- Modify: `config/agents_config.py`（AGENT_DEFINITIONS）

- [ ] **Step 1: AGENT_DEFINITIONS に追加**

`config/agents_config.py` の最後のエントリ（Negamax 実装済みなら `'id': 5`）の後に追加:

```python
    {
        'id': 6,
        'class': ApiAgent,
        'display_name': 'API (Edax)',
        'params': {
            'api_url': 'http://127.0.0.1:5001/play',
            'agent_type': 'edax',
        }
    },
```

- [ ] **Step 2: 既存テストが全て通ることを確認**

Run: `uv run pytest tests/ --ignore=tests/integration -v`
Expected: PASS（選択肢数を固定値で検証しているテストがあれば期待値を更新する）

- [ ] **Step 3: コミット**

```bash
git add config/agents_config.py
git commit -m "feat: GUI のプレイヤー選択肢に API (Edax) を追加"
```

---

### Task 6: 導入スクリプト setup_edax.sh

**Files:**
- Create: `scripts/setup_edax.sh`
- Modify: `.gitignore`（`out/edax/` を追加。既に `out/` が無視されているなら不要）

- [ ] **Step 1: スクリプトを書く**

`scripts/setup_edax.sh` を新規作成:

```bash
#!/usr/bin/env bash
# Edax (GPL v3) をソースからビルドして out/edax/ に配置する導入スクリプト。
# Edax はライセンス上リポジトリに同梱しないため、利用者が各自実行する。
set -euo pipefail

REPO_URL="https://github.com/abulmo/edax-reversi.git"
EVAL_URL="https://github.com/abulmo/edax-reversi/releases/download/v4.4/eval.7z"
DEST="$(cd "$(dirname "$0")/.." && pwd)/out/edax"

mkdir -p "${DEST}"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

echo "==> Edax のソースを取得しています..."
git clone --depth 1 "${REPO_URL}" "${WORK}/edax-reversi"

echo "==> ビルドしています..."
cd "${WORK}/edax-reversi/src"
case "$(uname -sm)" in
    "Darwin arm64") make build ARCH=arm64-modern COMP=clang OS=osx ;;
    "Darwin x86_64") make build ARCH=x86-64-v2 COMP=clang OS=osx ;;
    "Linux x86_64") make build ARCH=x86-64-v2 COMP=gcc OS=linux ;;
    *) echo "未対応のプラットフォームです: $(uname -sm)" >&2; exit 1 ;;
esac

echo "==> バイナリと評価データを配置しています..."
mkdir -p "${DEST}/bin" "${DEST}/data"
cp "${WORK}/edax-reversi/bin/"*edax* "${DEST}/bin/edax"
chmod +x "${DEST}/bin/edax"

if ! [ -f "${DEST}/data/eval.dat" ]; then
    echo "==> eval.dat を取得しています（約 80MB）..."
    curl -L "${EVAL_URL}" -o "${WORK}/eval.7z"
    # 7z 展開には p7zip が必要（macOS: brew install p7zip）
    7z x -o"${DEST}/data" "${WORK}/eval.7z"
fi

echo ""
echo "導入が完了しました。以下の環境変数を設定してサーバーを起動してください:"
echo "  export EDAX_PATH=${DEST}/bin/edax"
```

注意（実装時の調整ポイント）:
- Edax リポジトリの Makefile のターゲット名・出力バイナリ名・eval.7z の
  リリース URL はバージョンで変わりうる。実装時に
  https://github.com/abulmo/edax-reversi の README を確認して合わせる。
- eval.dat の展開先は「エンジンの cwd 基準で `data/eval.dat`」になるように
  配置する（EdaxEngine は `cwd=バイナリのあるディレクトリ` で起動するため、
  `bin/` と `data/` の位置関係を Edax の探索仕様に合わせて調整する）。

- [ ] **Step 2: 実行権限を付与して動作確認**

```bash
chmod +x scripts/setup_edax.sh
bash scripts/setup_edax.sh
```

Expected: `out/edax/bin/edax` が生成され、`EDAX_PATH` の案内が表示される。
（ビルド環境がない場合はこのステップを保留し、Task 7 の skipif で吸収する。）

- [ ] **Step 3: コミット**

```bash
git add scripts/setup_edax.sh .gitignore
git commit -m "feat: Edax のビルド・導入スクリプトを追加"
```

---

### Task 7: 実バイナリ統合テスト（skipif 付き）

**Files:**
- Create: `tests/integration/test_edax_integration.py`

- [ ] **Step 1: テストを書く**

`tests/integration/test_edax_integration.py` を新規作成:

```python
"""Edax 実バイナリを使う統合テスト。

EDAX_PATH が未設定（CI 等）の場合は全テストを skip する。
"""
import os

import pytest
import requests

_EDAX_PATH = os.getenv("EDAX_PATH", "")

pytestmark = pytest.mark.skipif(
    not _EDAX_PATH or not os.path.isfile(_EDAX_PATH),
    reason="edax binary not installed (EDAX_PATH not set)",
)

STANDARD_BOARD = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, -1, 0, 0, 0],
    [0, 0, 0, -1, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]


def test_edax_returns_legal_move(api_server_url: str) -> None:
    """初期局面で edax が合法手を返す。"""
    response = requests.post(
        f"{api_server_url}/play",
        json={"board": STANDARD_BOARD, "turn": -1, "agent_type": "edax"},
        timeout=10,
    )
    assert response.status_code == 200
    move = response.json()["move"]
    from board import Board
    b = Board(board_size=8)
    b.board = [row[:] for row in STANDARD_BOARD]
    assert move in [list(m) for m in b.get_valid_moves(-1)]


def test_edax_x_o_mapping_is_correct(api_server_url: str) -> None:
    """黒番・白番の両方で合法手が返る（X/O マッピングの検証）。

    マッピングが逆だと Edax は相手の手を打とうとして不合法手 → 500 になる。
    """
    from board import Board
    for turn in (-1, 1):
        response = requests.post(
            f"{api_server_url}/play",
            json={"board": STANDARD_BOARD, "turn": turn, "agent_type": "edax"},
            timeout=10,
        )
        assert response.status_code == 200, f"turn={turn} で失敗"
        b = Board(board_size=8)
        b.board = [row[:] for row in STANDARD_BOARD]
        assert response.json()["move"] in [list(m) for m in b.get_valid_moves(turn)]
```

`tests/integration/conftest.py` のサーバー起動 env に `EDAX_PATH` を引き継ぐ設定を追加
（env は `os.environ.copy()` 済みなので追加変更は不要だが、レベルを下げて高速化する）:

```python
    env["EDAX_LEVEL"] = "5"   # 統合テストは強さ不要・速度優先
```

- [ ] **Step 2: skip 動作と実行を確認**

Run（EDAX_PATH なし）: `uv run pytest tests/integration/test_edax_integration.py -v`
Expected: SKIPPED（reason: edax binary not installed）

Run（導入済みの場合）: `EDAX_PATH=$PWD/out/edax/bin/edax uv run pytest tests/integration/test_edax_integration.py -v`
Expected: PASS。**X/O マッピングが逆だった場合はここで失敗する** →
`agents/edax_engine.py` の `_CELL_CHARS` の X/O を入れ替えて再実行する。

- [ ] **Step 3: コミット**

```bash
git add tests/integration/test_edax_integration.py tests/integration/conftest.py
git commit -m "test: Edax 実バイナリの統合テストを追加（未導入環境では skip）"
```

---

### Task 8: Docker・ドキュメント・全体検証

**Files:**
- Modify: `Dockerfile`（マルチステージで Edax を組み込み）
- Modify: `README.md`（エージェント一覧・環境変数・導入手順）

- [ ] **Step 1: Dockerfile をマルチステージ化**

既存の `Dockerfile` の先頭に builder ステージを追加し、最終ステージにコピーする:

```dockerfile
# --- Edax ビルドステージ（GPL v3。イメージ配布時はライセンス表記必須） ---
FROM debian:bookworm-slim AS edax-builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential curl p7zip-full ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/abulmo/edax-reversi.git /src
WORKDIR /src/src
RUN make build ARCH=x86-64-v2 COMP=gcc OS=linux
RUN mkdir -p /opt/edax/bin /opt/edax/data \
    && cp /src/bin/*edax* /opt/edax/bin/edax \
    && curl -L \
       https://github.com/abulmo/edax-reversi/releases/download/v4.4/eval.7z \
       -o /tmp/eval.7z \
    && 7z x -o/opt/edax/data /tmp/eval.7z
```

既存の最終ステージに追加:

```dockerfile
COPY --from=edax-builder /opt/edax /opt/edax
ENV EDAX_PATH=/opt/edax/bin/edax
LABEL org.opencontainers.image.licenses="MIT AND GPL-3.0-only (bundled Edax)"
```

注意: ビルドターゲット名・成果物パス・eval.7z の URL は Task 6 と同様に
実装時に上流 README で確認して合わせる。

- [ ] **Step 2: README.md を更新**

- AI エージェント一覧の表に `API (Edax)` を追加:
  「外部エンジン Edax（世界最強クラス）。要 `scripts/setup_edax.sh` での導入と `EDAX_PATH` 設定。8x8 以外は Negamax にフォールバック」
- 環境変数の表（`EDAX_PATH` / `EDAX_LEVEL` / `EDAX_MOVE_TIME` / `EDAX_TIMEOUT`）を追加
- 導入手順セクション（`bash scripts/setup_edax.sh` → `export EDAX_PATH=...`）を追加
- 未導入時の挙動（`agent_type=edax` は 503）を明記

- [ ] **Step 3: CI チェック一式を実行**

Run: `bash scripts/ci_check.sh`
Expected: ruff / mypy / pytest / カバレッジ全て成功。
Edax 統合テストは `EDAX_PATH` 未設定なら skip され、CI への影響はない。

- [ ] **Step 4: Docker ビルドを確認（任意・ローカル）**

Run: `docker build -t reversi-py:edax .`
Expected: ビルド成功。`docker run -e LOG_LEVEL=info -p 5001:5001 reversi-py:edax` で
起動し、`curl -X POST localhost:5001/play -H 'Content-Type: application/json' -d '{"board": [[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,1,-1,0,0,0],[0,0,0,-1,1,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]], "turn": -1, "agent_type": "edax"}'`
が合法手を返す。

- [ ] **Step 5: コミット**

```bash
git add Dockerfile README.md
git commit -m "feat: Docker イメージへの Edax 組み込みと README 更新"
```

"""外部のオセロエンジン Edax を子プロセスとして動かすエージェント（強さ評価用）。

Edax の標準 UI に対し、毎手「setboard <盤面> <手番>」で局面を渡し、
「go」で着手させて「Edax plays XX」の行から手を読み取る。
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .base_agent import Agent

if TYPE_CHECKING:
    from game import Game

# 盤面の値（game.py と同じ）
_BLACK = -1
_WHITE = 1
_BOARD_SIZE = 8
# Edax の着手を示す出力行の接頭辞
_PLAYS_PREFIX = "Edax plays "
# Edax がパスしたときの手の表記
_PASS_MOVE = "PS"


class EdaxError(RuntimeError):
    """Edax との通信に失敗したときの例外。"""


def board_to_edax(board: list[list[int]], turn: int) -> str:
    """盤面と手番を Edax の setboard 形式（64 文字 + 手番）に変換する。

    Args:
        board: 8x8 の盤面（-1: 黒、1: 白、0: 空き）。
        turn: 手番（-1: 黒、1: 白）。

    Returns:
        例: "---...OX...--- X"（a1 から h1、a2 … h8 の順）。
    """
    symbols = {_BLACK: "X", _WHITE: "O", 0: "-"}
    cells = "".join(symbols[cell] for row in board for cell in row)
    return f"{cells} {'X' if turn == _BLACK else 'O'}"


def parse_edax_move(text: str) -> Optional[tuple[int, int]]:
    """Edax の手の表記（例: "D3"、"PS"）を (row, col) に変換する。

    Args:
        text: 2 文字の手の表記。大文字・小文字は問わない。

    Returns:
        (row, col)。パスの場合は None。

    Raises:
        EdaxError: 表記が不正な場合。
    """
    move = text.strip().upper()
    if move == _PASS_MOVE:
        return None
    if len(move) != 2 or not ("A" <= move[0] <= "H") or not ("1" <= move[1] <= "8"):
        raise EdaxError(f"Edax の手を解釈できません: {text!r}")
    return int(move[1]) - 1, ord(move[0]) - ord("A")


class EdaxAgent(Agent):
    """Edax に手を選ばせるエージェント。

    Args:
        edax_path: Edax の実行ファイルのパス。
        level: Edax の探索レベル（0〜60。大きいほど強い）。
        working_dir: Edax の実行ディレクトリ（data/eval.dat がある場所）。
            省略時は実行ファイルと同じディレクトリ。
        use_book: 定石ブックを使うか（既定は使わない）。
    """

    def __init__(
        self,
        edax_path: Path,
        level: int,
        working_dir: Optional[Path] = None,
        use_book: bool = False,
    ) -> None:
        if working_dir is None:
            working_dir = edax_path.resolve().parent
        command = [
            str(edax_path.resolve()),
            "-level", str(level),
            "-n-tasks", "1",
            "-book-usage", "on" if use_book else "off",
        ]
        self._process = subprocess.Popen(
            command,
            cwd=working_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        # 自動で着手しないモード（mode 3: 人間対人間）にする
        self._send("mode 3")

    def _send(self, line: str) -> None:
        """Edax に 1 行のコマンドを送る。"""
        if self._process.stdin is None or self._process.poll() is not None:
            raise EdaxError("Edax のプロセスが終了しています")
        self._process.stdin.write(line + "\n")
        self._process.stdin.flush()

    def _read_move(self) -> Optional[tuple[int, int]]:
        """「Edax plays XX」の行が来るまで出力を読み、手を返す。"""
        # stdout=PIPE で起動しているので None にはならない
        assert self._process.stdout is not None
        for line in self._process.stdout:
            if line.startswith(_PLAYS_PREFIX):
                return parse_edax_move(line[len(_PLAYS_PREFIX):])
        raise EdaxError("Edax の着手を受け取る前にプロセスが終了しました")

    def play(self, game: "Game") -> Optional[tuple[int, int]]:
        """現在の局面を Edax に渡し、Edax が選んだ手を返す。

        Args:
            game: ゲーム状態。

        Returns:
            (row, col)。合法手が無い場合は None。
        """
        if not game.get_valid_moves():
            return None
        self._send(f"setboard {board_to_edax(game.board.board, game.turn)}")
        self._send("go")
        return self._read_move()

    def close(self) -> None:
        """Edax を終了させる。"""
        if self._process.poll() is None:
            try:
                self._send("quit")
                self._process.wait(timeout=5)
            except (EdaxError, BrokenPipeError, subprocess.TimeoutExpired):
                self._process.kill()
                self._process.wait()

    def __enter__(self) -> "EdaxAgent":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

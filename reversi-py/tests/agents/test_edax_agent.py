"""EdaxAgent のテスト。本物の Edax の代わりに、同じ入出力をまねる偽スクリプトを使う。"""
from __future__ import annotations

import stat
import sys
from pathlib import Path

import pytest

from agents.edax_agent import EdaxAgent, EdaxError, board_to_edax, parse_edax_move
from game import Game

# 受け取った setboard を記録し、go に対して決まった手を返す偽の Edax
_FAKE_EDAX = """\
import sys
log = open(sys.argv[-1], "w")
for line in sys.stdin:
    line = line.strip()
    log.write(line + "\\n")
    log.flush()
    if line == "go":
        print("Edax is thinking...")
        print("Edax plays {move}", flush=True)
    elif line == "quit":
        break
"""


def _make_fake_edax(tmp_path: Path, move: str, log_path: Path) -> Path:
    """偽の Edax 実行ファイルを作る（引数の最後に記録先を付けて起動する）。"""
    script = tmp_path / "fake_edax.py"
    script.write_text(_FAKE_EDAX.replace("{move}", move))
    wrapper = tmp_path / "bin" / "edax"
    wrapper.parent.mkdir()
    wrapper.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@" "{log_path}"\n')
    wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC)
    return wrapper


def test_board_to_edax_initial_position() -> None:
    """初期局面を a1〜h8 の順の 64 文字と手番に変換する。"""
    game = Game()
    text = board_to_edax(game.board.board, game.turn)
    cells, turn = text.split(" ")
    assert len(cells) == 64
    # d4 (index 27) と e5 (index 36) は白、e4 (28) と d5 (35) は黒
    assert cells[27] == "O" and cells[36] == "O"
    assert cells[28] == "X" and cells[35] == "X"
    assert cells.count("-") == 60
    assert turn == "X"
    assert board_to_edax(game.board.board, 1).endswith(" O")


@pytest.mark.parametrize(
    ("text", "expected"),
    [("D3", (2, 3)), ("a1", (0, 0)), ("H8\n", (7, 7)), ("PS", None), ("ps", None)],
)
def test_parse_edax_move(text: str, expected: tuple[int, int] | None) -> None:
    """手の表記を (row, col) に、パスを None に変換する。"""
    assert parse_edax_move(text) == expected


@pytest.mark.parametrize("text", ["", "I1", "A9", "A0", "D33"])
def test_parse_edax_move_invalid(text: str) -> None:
    """不正な表記は EdaxError になる。"""
    with pytest.raises(EdaxError):
        parse_edax_move(text)


def test_play_sends_board_and_returns_move(tmp_path: Path) -> None:
    """局面を setboard で渡し、Edax の手を返す。"""
    log_path = tmp_path / "commands.log"
    edax_path = _make_fake_edax(tmp_path, "D3", log_path)
    game = Game()
    with EdaxAgent(edax_path, level=3) as agent:
        assert agent.play(game) == (2, 3)
    commands = log_path.read_text().splitlines()
    assert commands[0] == "mode 3"
    assert commands[1] == f"setboard {board_to_edax(game.board.board, game.turn)}"
    assert commands[2] == "go"
    assert commands[-1] == "quit"


def test_play_returns_none_without_valid_moves(tmp_path: Path) -> None:
    """合法手が無ければ Edax に問い合わせず None を返す。"""
    log_path = tmp_path / "commands.log"
    edax_path = _make_fake_edax(tmp_path, "D3", log_path)
    game = Game()
    # 黒だけの盤面にすると、どちらも打てない
    game.board.board = [[-1] * 8 for _ in range(8)]
    game._invalidate_valid_moves_cache()
    with EdaxAgent(edax_path, level=1) as agent:
        assert agent.play(game) is None
    assert "go" not in log_path.read_text().splitlines()


def test_play_raises_when_process_exits(tmp_path: Path) -> None:
    """Edax が手を返さずに終了したら EdaxError になる。"""
    edax_path = tmp_path / "bin" / "edax"
    edax_path.parent.mkdir()
    edax_path.write_text("#!/bin/sh\ncat > /dev/null\n")
    edax_path.chmod(edax_path.stat().st_mode | stat.S_IEXEC)
    agent = EdaxAgent(edax_path, level=1)
    assert agent._process.stdin is not None
    agent._process.stdin.close()
    agent._process.wait(timeout=5)
    with pytest.raises(EdaxError):
        agent.play(Game())
    agent.close()


def test_read_move_raises_on_eof(tmp_path: Path) -> None:
    """出力が途切れたら EdaxError になる。"""
    edax_path = tmp_path / "bin" / "edax"
    edax_path.parent.mkdir()
    edax_path.write_text("#!/bin/sh\nread line\nread line\nread line\n")
    edax_path.chmod(edax_path.stat().st_mode | stat.S_IEXEC)
    agent = EdaxAgent(edax_path, level=1)
    with pytest.raises(EdaxError):
        agent.play(Game())
    agent.close()


def test_close_kills_unresponsive_process(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """quit に応じない Edax は強制終了する。"""
    edax_path = tmp_path / "bin" / "edax"
    edax_path.parent.mkdir()
    edax_path.write_text("#!/bin/sh\nwhile true; do sleep 1; done\n")
    edax_path.chmod(edax_path.stat().st_mode | stat.S_IEXEC)
    agent = EdaxAgent(edax_path, level=1)
    original_wait = agent._process.wait

    def fake_wait(timeout: float | None = None) -> int:
        if timeout is not None:
            import subprocess
            raise subprocess.TimeoutExpired("edax", timeout)
        return original_wait()

    monkeypatch.setattr(agent._process, "wait", fake_wait)
    agent.close()
    assert agent._process.poll() is not None

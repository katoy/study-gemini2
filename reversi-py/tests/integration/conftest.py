"""統合テスト用の pytest フィクスチャ。

実際の uvicorn サーバーを subprocess で起動し、
テスト終了後に確実に停止する session スコープのフィクスチャを提供する。
"""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Generator

import pytest

INTEGRATION_TEST_PORT = 5002
INTEGRATION_TEST_HOST = "127.0.0.1"
_SERVER_STARTUP_TIMEOUT = 15


def _wait_for_port(host: str, port: int, timeout: float) -> bool:
    """指定ポートが LISTEN 状態になるまで socket polling で待機する。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.2)
    return False


@pytest.fixture(scope="session")
def api_server_url() -> Generator[str, None, None]:
    """実際の uvicorn サーバーを port 5002 で起動し、URL を yield する。

    Notes:
        port 5002 を使用することでデフォルト port 5001 との競合を回避する。
        テスト中のログノイズを抑制するため LOG_LEVEL=warning を設定する。
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    env = os.environ.copy()
    env["API_HOST"] = INTEGRATION_TEST_HOST
    env["API_PORT"] = str(INTEGRATION_TEST_PORT)
    env["LOG_LEVEL"] = "warning"
    env["SDL_VIDEODRIVER"] = "dummy"
    env["SDL_AUDIODRIVER"] = "dummy"

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "server.api_server:app",
            "--host",
            INTEGRATION_TEST_HOST,
            "--port",
            str(INTEGRATION_TEST_PORT),
            "--log-level",
            "warning",
        ],
        cwd=str(project_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    started = _wait_for_port(
        INTEGRATION_TEST_HOST, INTEGRATION_TEST_PORT, _SERVER_STARTUP_TIMEOUT
    )

    if not started:
        proc.terminate()
        proc.wait(timeout=5)
        stdout = proc.stdout.read().decode() if proc.stdout else ""
        stderr = proc.stderr.read().decode() if proc.stderr else ""
        pytest.fail(
            f"API server failed to start on port {INTEGRATION_TEST_PORT} "
            f"within {_SERVER_STARTUP_TIMEOUT}s.\n"
            f"stdout: {stdout}\nstderr: {stderr}"
        )

    yield f"http://{INTEGRATION_TEST_HOST}:{INTEGRATION_TEST_PORT}"

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()

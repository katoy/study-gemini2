"""Lightweight Norman shim for local/CI installs.

This module provides a minimal `python -m norman` entrypoint with a `check`
subcommand that runs a set of project linters (ruff) and type checks (mypy).

It exists to provide a reproducible `norman check .` entrypoint when the
PyPI `norman` package is a placeholder or lacks a CLI.

Usage:
  python -m norman check [path]
  python -m norman --version

Note: This is intentionally small and only intended for CI/local convenience.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from typing import List

__version__ = "0.1.0"


def run_command(cmd: List[str]) -> int:
    print(f"Running: {' '.join(cmd)}")
    proc = subprocess.run(cmd)
    return proc.returncode


def do_check(path: str) -> int:
    # Use the same interpreter to run ruff and mypy modules so it uses venv-installed tools
    py = sys.executable

    # Run ruff: check selected errors/warnings, ignore long line E501, exclude tests
    ruff_cmd = [py, "-m", "ruff", "check", path, "--select=E,W,F", "--ignore=E501", "--exclude=tests"]
    rc1 = run_command(ruff_cmd)

    # Run mypy: ignore missing imports for smoother CI
    mypy_cmd = [py, "-m", "mypy", path, "--ignore-missing-imports"]
    rc2 = run_command(mypy_cmd)

    if rc1 == 0 and rc2 == 0:
        print("norman: all checks passed")
        return 0
    else:
        print("norman: one or more checks failed")
        return 1


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="norman", description="Norman shim: check code quality")
    ap.add_argument("-V", "--version", action="store_true", help="show version and exit")
    sub = ap.add_subparsers(dest="cmd")

    check = sub.add_parser("check", help="run quality checks")
    check.add_argument("path", nargs="?", default=".", help="path to check")

    return ap.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    if args.version:
        print(f"norman-shim {__version__}")
        return 0
    if args.cmd == "check":
        return do_check(args.path)

    # If no command provided, show help
    print("norman: no command given. Use 'norman check [path]' or --version")
    return 2


if __name__ == "__main__":
    sys.exit(main())

#!/bin/bash

# reversi-py アプリケーション起動スクリプト
# Docker なし環境での起動用

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "🎮 Reversi ゲーム起動中..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Python 環境確認
if ! command -v python &> /dev/null; then
    echo "❌ エラー: Python が見つかりません"
    exit 1
fi

# uv が使える場合は uv を使用
if command -v uv &> /dev/null; then
    echo "✅ uv を使用して実行します"
    uv run python main.py
else
    echo "✅ python を使用して実行します"
    python main.py
fi

#!/bin/bash

# uv で起動した Reversi アプリと API サーバーを停止するスクリプト

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

APP_PATTERN='uv run python main.py'
SERVER_PATTERN='uv run python -m server.api_server'

stop_by_pattern() {
    local label="$1"
    local pattern="$2"
    local pids=()

    while IFS= read -r pid; do
        [ -n "$pid" ] && pids+=("$pid")
    done < <(pgrep -f "$pattern" 2>/dev/null || true)

    if [ ${#pids[@]} -eq 0 ]; then
        echo "ℹ️  ${label} は見つかりませんでした"
        return 0
    fi

    echo "🛑 ${label} を停止中..."
    for pid in "${pids[@]}"; do
        kill "$pid" 2>/dev/null || true
    done

    sleep 1

    local remaining=()
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            remaining+=("$pid")
        fi
    done

    if [ ${#remaining[@]} -gt 0 ]; then
        echo "⚠️  ${label} の停止に時間がかかっています。強制終了します..."
        for pid in "${remaining[@]}"; do
            kill -9 "$pid" 2>/dev/null || true
        done
    fi

    echo "✅ ${label} を停止しました"
}

echo "🛑 Reversi アプリと API サーバーを停止中..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

stop_by_pattern "アプリケーション" "$APP_PATTERN"
stop_by_pattern "API サーバー" "$SERVER_PATTERN"

echo ""
echo "✅ 完了"

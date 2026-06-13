#!/bin/bash

# uv で起動した API サーバーを再起動するスクリプト

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-5001}"
API_LOG="${API_LOG:-/tmp/api_server.log}"
SERVER_PATTERN='uv run python -m server.api_server'

stop_server() {
    local pids=()

    while IFS= read -r pid; do
        [ -n "$pid" ] && pids+=("$pid")
    done < <(pgrep -f "$SERVER_PATTERN" 2>/dev/null || true)

    if [ ${#pids[@]} -eq 0 ]; then
        echo "ℹ️  API サーバーは見つかりませんでした"
        return 0
    fi

    echo "🛑 API サーバーを停止中..."
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
        echo "⚠️  API サーバーの停止に時間がかかっています。強制終了します..."
        for pid in "${remaining[@]}"; do
            kill -9 "$pid" 2>/dev/null || true
        done
    fi

    echo "✅ API サーバーを停止しました"
}

start_server() {
    echo "📡 API サーバーを起動中..."
    if command -v uv &> /dev/null; then
        uv run python -m server.api_server > "$API_LOG" 2>&1 &
    else
        python -m server.api_server > "$API_LOG" 2>&1 &
    fi

    SERVER_PID=$!
    echo "✅ API サーバーが起動しました (PID: $SERVER_PID)"
}

wait_for_server() {
    echo "⏳ サーバーの起動を確認中..."
    local wait_count=0

    while [ $wait_count -lt 20 ]; do
        if curl -s "http://$API_HOST:$API_PORT/docs" > /dev/null 2>&1; then
            echo "✅ API サーバーの確認完了"
            return 0
        fi
        sleep 0.5
        wait_count=$((wait_count + 1))
    done

    echo "⚠️  警告: API サーバーの起動が遅延しています"
    echo "   ログを確認してください: cat $API_LOG"
}

echo "🔄 API サーバーを再起動中..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "API Server: http://$API_HOST:$API_PORT"
echo "API ドキュメント: http://$API_HOST:$API_PORT/docs"
echo ""

stop_server
start_server
wait_for_server

echo ""
echo "✅ 完了"

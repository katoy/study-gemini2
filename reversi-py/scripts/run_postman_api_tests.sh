#!/bin/bash

# Postman/Newman を使って /play API の契約テストを実行するスクリプト

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

COLLECTION_FILE="$PROJECT_ROOT/postman/reversi-api.postman_collection.json"
ENV_FILE="$PROJECT_ROOT/postman/reversi-api.postman_environment.json"

if [ -n "${API_BASE_URL:-}" ]; then
    BASE_URL="$API_BASE_URL"
    AUTO_START="${API_AUTOSTART:-0}"
else
    API_HOST="${API_HOST:-127.0.0.1}"
    API_PORT="${API_PORT:-5001}"
    BASE_URL="http://${API_HOST}:${API_PORT}"
    AUTO_START="${API_AUTOSTART:-1}"
fi

API_LOG="${API_LOG:-/tmp/reversi-api-server.log}"
SERVER_STARTED=0

cleanup() {
    if [ "$SERVER_STARTED" -eq 1 ] && [ -n "${SERVER_PID:-}" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
        echo "🛑 API サーバーを停止中..."
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
        echo "✅ API サーバーを停止しました"
    fi
}

wait_for_server() {
    local wait_count=0
    while [ $wait_count -lt 30 ]; do
        if curl -fsS "$BASE_URL/docs" > /dev/null 2>&1; then
            return 0
        fi
        sleep 0.5
        wait_count=$((wait_count + 1))
    done

    echo "❌ API サーバーの起動を確認できませんでした"
    echo "   ログ: $API_LOG"
    return 1
}

start_server_if_needed() {
    if curl -fsS "$BASE_URL/docs" > /dev/null 2>&1; then
        echo "ℹ️  API サーバーは既に起動しています: $BASE_URL"
        return 0
    fi

    if [ "$AUTO_START" != "1" ]; then
        echo "ℹ️  API サーバーの自動起動は無効です"
        return 0
    fi

    echo "📡 API サーバーを起動中..."
    if command -v uv >/dev/null 2>&1; then
        uv run python -m server.api_server > "$API_LOG" 2>&1 &
    else
        python -m server.api_server > "$API_LOG" 2>&1 &
    fi

    SERVER_PID=$!
    SERVER_STARTED=1
    echo "✅ API サーバーが起動しました (PID: $SERVER_PID)"
    wait_for_server
}

run_newman() {
    echo "🧪 Newman で API 契約テストを実行します"
    if command -v newman >/dev/null 2>&1; then
        newman run "$COLLECTION_FILE" -e "$ENV_FILE" --env-var "baseUrl=$BASE_URL" --bail
    elif command -v npx >/dev/null 2>&1; then
        npx -y newman run "$COLLECTION_FILE" -e "$ENV_FILE" --env-var "baseUrl=$BASE_URL" --bail
    else
        echo "❌ newman も npx も見つかりません。Node.js 環境を確認してください。"
        exit 1
    fi
}

trap cleanup EXIT INT TERM

echo "================================"
echo "Postman/Newman API 契約テスト"
echo "================================"
echo "Collection: $COLLECTION_FILE"
echo "Environment: $ENV_FILE"
echo "Base URL: $BASE_URL"
echo

start_server_if_needed
run_newman

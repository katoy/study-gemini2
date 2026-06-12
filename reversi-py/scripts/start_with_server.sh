#!/bin/bash

# Reversi アプリケーション + API サーバー起動スクリプト
# API (Random) エージェントを使う場合に実行

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# デフォルト設定
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-5001}"

echo "🎮 Reversi + API サーバー起動中..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "API Server: http://$API_HOST:$API_PORT"
echo "API ドキュメント: http://$API_HOST:$API_PORT/docs"
echo ""

# API サーバー起動
echo "📡 API サーバーを起動中..."
if command -v uv &> /dev/null; then
    uv run python -m server.api_server > /tmp/api_server.log 2>&1 &
else
    python -m server.api_server > /tmp/api_server.log 2>&1 &
fi
SERVER_PID=$!
echo "✅ API サーバーが起動しました (PID: $SERVER_PID)"

# サーバーの起動を確認（最大 10 秒待機）
echo "⏳ サーバーの起動を確認中..."
WAIT_COUNT=0
while [ $WAIT_COUNT -lt 20 ]; do
    if curl -s http://$API_HOST:$API_PORT/docs > /dev/null 2>&1; then
        echo "✅ API サーバーの確認完了"
        break
    fi
    sleep 0.5
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

if [ $WAIT_COUNT -eq 20 ]; then
    echo "⚠️  警告: API サーバーの起動が遅延しています"
    echo "   ログを確認してください: cat /tmp/api_server.log"
fi

echo ""
echo "💡 ヒント:"
echo "   - ゲーム設定で 'API (Random)' を選択すると API サーバーを使用します"
echo "   - Ctrl+C で終了時、API サーバープロセス (PID: $SERVER_PID) も終了します"
echo ""

# シグナルハンドラー設定
cleanup() {
    echo ""
    echo "🛑 終了処理中..."
    if kill -0 $SERVER_PID 2>/dev/null; then
        kill $SERVER_PID 2>/dev/null || true
        echo "✅ API サーバーを停止しました"
    fi
}

trap cleanup EXIT INT TERM

# アプリケーション起動
echo "🎮 アプリケーションを起動中..."
if command -v uv &> /dev/null; then
    uv run python main.py
else
    python main.py
fi

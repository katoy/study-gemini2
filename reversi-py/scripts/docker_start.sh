#!/bin/bash

# Docker コンテナ起動スクリプト
# VNC 接続で GUI を操作

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 設定
IMAGE_NAME="reversi-py"
CONTAINER_NAME="reversi-container"
VNC_PORT="${VNC_PORT:-5901}"
API_PORT="${API_PORT:-5001}"

echo "🐳 Docker コンテナを起動中..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# イメージの存在確認
if ! docker image inspect "$IMAGE_NAME" > /dev/null 2>&1; then
    echo "📦 イメージを構築中..."
    docker build -t "$IMAGE_NAME" "$PROJECT_ROOT"
    echo "✅ イメージが構築されました"
else
    echo "✅ イメージが見つかりました"
fi

# 既存コンテナ停止
if docker ps -a | grep -q "$CONTAINER_NAME"; then
    echo "🛑 既存コンテナを停止中..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
fi

# コンテナ起動
echo "🚀 コンテナを起動中..."
docker run -d \
    --name "$CONTAINER_NAME" \
    -p "$VNC_PORT:5901" \
    -p "$API_PORT:5001" \
    -e DISPLAY=:1 \
    "$IMAGE_NAME"

echo "✅ コンテナが起動しました (ID: $(docker ps -q -f name=$CONTAINER_NAME))"
echo ""
echo "📍 接続情報:"
echo "   VNC: localhost:$VNC_PORT または 127.0.0.1:$VNC_PORT"
echo "   API: http://localhost:$API_PORT"
echo "   API ドキュメント: http://localhost:$API_PORT/docs"
echo ""
echo "💡 操作方法:"
echo "   - VNC クライアント (TightVNC, RealVNC など) で接続してください"
echo "   - VNC パスワード: reversi (Dockerfile で設定)"
echo "   - コンテナを停止: docker stop $CONTAINER_NAME"
echo "   - コンテナを削除: docker rm $CONTAINER_NAME"
echo ""
echo "🔍 ログ確認:"
echo "   docker logs -f $CONTAINER_NAME"

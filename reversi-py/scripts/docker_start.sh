#!/bin/bash

# Docker コンテナ起動スクリプト
# イメージを構築（変更がなければキャッシュで即完了）し、VNC 接続で GUI を操作できるコンテナを起動する

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 設定
IMAGE_NAME="reversi-py"
CONTAINER_NAME="reversi-container"
VNC_PORT="${VNC_PORT:-5901}"
API_PORT="${API_PORT:-5001}"
VNC_PASSWORD="${VNC_PASSWORD:-reversi}"

echo "🐳 Docker コンテナを起動中..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# イメージを構築する（毎回実行し、コードの変更を反映する。変更がない層はキャッシュされる）
echo "📦 イメージを構築中..."
docker build -t "$IMAGE_NAME" "$PROJECT_ROOT"
echo "✅ イメージを構築しました"

# 同名の既存コンテナがあれば停止・削除（名前は完全一致で判定する）
if [ -n "$(docker ps -aq -f "name=^${CONTAINER_NAME}$")" ]; then
    echo "🛑 既存コンテナを停止・削除中..."
    docker rm -f "$CONTAINER_NAME" > /dev/null
fi

# コンテナ起動
# VNC（弱いパスワード）と API（認証なし）を LAN に晒さないよう、ホストのループバックにだけ公開する
echo "🚀 コンテナを起動中..."
docker run -d \
    --name "$CONTAINER_NAME" \
    -p "127.0.0.1:$VNC_PORT:5901" \
    -p "127.0.0.1:$API_PORT:5001" \
    -e VNC_PASSWORD="$VNC_PASSWORD" \
    "$IMAGE_NAME" > /dev/null

echo "✅ コンテナが起動しました (ID: $(docker ps -q -f "name=^${CONTAINER_NAME}$"))"
echo ""
echo "📍 接続情報:"
echo "   VNC: localhost:${VNC_PORT}（macOS は Finder > 移動 > サーバーへ接続 > vnc://localhost:${VNC_PORT}）"
echo "   API: http://localhost:$API_PORT"
echo "   API ドキュメント: http://localhost:$API_PORT/docs"
echo ""
echo "💡 操作方法:"
echo "   - VNC クライアント (TightVNC, RealVNC など) で接続してください"
echo "   - VNC パスワード: ${VNC_PASSWORD}（環境変数 VNC_PASSWORD で変更可、先頭 8 文字が有効）"
echo "   - 起動完了まで数十秒かかります（docker logs に「起動完了」と出たら接続できます）"
echo "   - コンテナを停止: ./scripts/docker_stop.sh"
echo ""
echo "🔍 ログ確認:"
echo "   docker logs -f $CONTAINER_NAME"

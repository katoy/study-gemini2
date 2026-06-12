#!/bin/bash

# Docker コンテナ停止スクリプト

set -e

CONTAINER_NAME="reversi-container"

echo "🛑 Docker コンテナを停止中..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if docker ps -a | grep -q "$CONTAINER_NAME"; then
    # コンテナが実行中か確認
    if docker ps | grep -q "$CONTAINER_NAME"; then
        echo "⏹️  コンテナを停止中..."
        docker stop "$CONTAINER_NAME"
        echo "✅ コンテナが停止しました"
    else
        echo "ℹ️  コンテナは実行中ではありません"
    fi

    # 削除するか確認
    read -p "コンテナを削除しますか? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  コンテナを削除中..."
        docker rm "$CONTAINER_NAME"
        echo "✅ コンテナが削除されました"
    fi
else
    echo "ℹ️  コンテナが見つかりません"
fi

echo ""
echo "✅ 完了"

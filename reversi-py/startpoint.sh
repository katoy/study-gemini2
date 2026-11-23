#!/bin/bash
# Docker コンテナの起動スクリプト
# VNC サーバー（デスクトップ）・API サーバー・リバーシ GUI を順に起動する

set -euo pipefail

# tightvncserver は USER 環境変数を必要とする
export USER=root

VNC_PASSWORD="${VNC_PASSWORD:-reversi}"
VNC_DISPLAY=":1"
VNC_GEOMETRY="${VNC_GEOMETRY:-1280x1024}"
API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-5001}"
# 起動待ちの上限（秒）
WAIT_TIMEOUT_SECONDS=60
API_LOG=/app/api_server.log
APP_LOG=/app/app.log

# 条件が満たされるまで 1 秒ごとに確認する。上限を超えたら失敗を返す
wait_until() {
    local description="$1"
    shift
    for _ in $(seq 1 "$WAIT_TIMEOUT_SECONDS"); do
        if "$@" > /dev/null 2>&1; then
            echo "✅ ${description}"
            return 0
        fi
        sleep 1
    done
    echo "❌ ${description}: ${WAIT_TIMEOUT_SECONDS} 秒待っても準備できませんでした"
    return 1
}

# --- VNC サーバーの設定 ---
mkdir -p ~/.vnc
echo "$VNC_PASSWORD" | vncpasswd -f > ~/.vnc/passwd
chmod 600 ~/.vnc/passwd

cat <<'EOF' > ~/.vnc/xstartup
#!/bin/bash
startxfce4 &
EOF
chmod +x ~/.vnc/xstartup

# --- VNC サーバーの起動（vncserver は自身でバックグラウンド化する） ---
echo "🖥️  VNC サーバーを起動中 (display ${VNC_DISPLAY}, port 5901)..."
vncserver "$VNC_DISPLAY" -geometry "$VNC_GEOMETRY" -depth 24
wait_until "VNC サーバーの準備完了" test -S /tmp/.X11-unix/X1

# --- API サーバーの起動 ---
echo "📡 API サーバーを起動中 (${API_HOST}:${API_PORT})..."
API_HOST="$API_HOST" API_PORT="$API_PORT" \
    uv run --frozen --no-sync python -m server.api_server > "$API_LOG" 2>&1 &
wait_until "API サーバーの準備完了" \
    python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${API_PORT}/docs', timeout=2)"

# --- リバーシ GUI の起動 ---
echo "🎮 リバーシを起動中..."
# コンテナには音声デバイスがないため、SDL の音声出力は無効にする（ALSA のエラー出力を防ぐ）
DISPLAY="$VNC_DISPLAY" SDL_AUDIODRIVER=dummy \
    uv run --frozen --no-sync python main.py > "$APP_LOG" 2>&1 &

# --- コンテナの維持 ---
# docker stop の SIGTERM を受けたら速やかに終了する
# （PID 1 のプロセスはハンドラが無いとシグナルを無視し、10 秒後に強制終了されるため）
trap 'echo "🛑 停止します"; exit 0' TERM INT
echo "✅ 起動完了。VNC クライアントで localhost:5901 に接続してください"
# GUI・API サーバーのログを docker logs で見られるよう標準出力に流し続ける
tail -n +1 -F "$API_LOG" "$APP_LOG" &
wait $!

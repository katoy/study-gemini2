#!/bin/sh
# startpoint.sh - Container startup script for Pygame with Xvfb and VNC

# Exit immediately if a command exits with a non-zero status.
set -e

# 環境変数のデフォルト値（Dockerfileで設定されているが念のため）
: "${DISPLAY:=${DISPLAY}}" # DockerfileのENVから引き継ぐ
: "${SCREEN_WIDTH:=${SCREEN_WIDTH}}"
: "${SCREEN_HEIGHT:=${SCREEN_HEIGHT}}"
: "${VNC_PORT:=${VNC_PORT}}"

echo "--- Starting Virtual Framebuffer (Xvfb) ---"
# Xvfbをバックグラウンドで起動
# -nolisten tcp: TCP接続を無効化 (セキュリティ向上)
# -screen 0 ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x24: 画面サイズと色深度を指定
Xvfb "${DISPLAY}" -nolisten tcp -screen 0 "${SCREEN_WIDTH}x${SCREEN_HEIGHT}x24" &
XVFB_PID=$!
echo "Xvfb started on display ${DISPLAY} with PID ${XVFB_PID}"

# Xvfbが起動するのを少し待つ (より堅牢にするにはポートやファイルの存在を確認)
sleep 2

echo "--- Starting VNC Server (x11vnc) ---"
# x11vncをバックグラウンドで起動
# -display ${DISPLAY}: 接続するXサーバーを指定
# -rfbport ${VNC_PORT}: VNCがリッスンするポートを指定
# -nopw: パスワード認証なし (注意: セキュリティリスクあり)
# -N: 一度クライアントが接続したら新しい接続を受け付けない (オプション)
# -forever: クライアントが切断してもサーバーを終了しない
# -shared: 複数クライアントの同時接続を許可 (オプション、-Nと併用不可の場合あり)
# -localhost: ローカルホストからの接続のみ許可 (Dockerのポートフォワーディング経由でのみアクセス可能になる)
x11vnc -display "${DISPLAY}" -rfbport "${VNC_PORT}" -nopw -N -forever -localhost &
X11VNC_PID=$!
echo "x11vnc started, listening on port ${VNC_PORT} (forwarded from host) with PID ${X11VNC_PID}"
echo "Connect via VNC client to localhost:${VNC_PORT}"

# シグナルハンドリング: コンテナ停止時に子プロセスも終了させる
# trap 'echo "Caught signal, shutting down..."; kill $XVFB_PID $X11VNC_PID; exit' SIGINT SIGTERM
# execを使う場合、シグナルはexecされたプロセス(python)に直接送られるため、
# Python側で適切に処理するか、execを使わずにwaitする方法を検討する必要がある。
# ここではシンプルにexecを使用する。

echo "--- Starting Python Application (main.py) ---"
# exec python main.py: スクリプトプロセスをPythonプロセスで置き換える
# これにより、Pythonプロセスが終了するとコンテナも終了する
exec python main.py

# exec を使わない場合の代替 (python終了後もスクリプトが継続する)
# python main.py
# PYTHON_EXIT_CODE=$?
# echo "Python application exited with code ${PYTHON_EXIT_CODE}"
# echo "Shutting down Xvfb and x11vnc..."
# kill $XVFB_PID $X11VNC_PID
# exit $PYTHON_EXIT_CODE

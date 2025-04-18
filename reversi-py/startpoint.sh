#!/bin/bash

export USER=root

# --- VNCサーバーの設定 ---
# (省略...)
VNC_PASSWORD=${VNC_PASSWORD:-password}
mkdir -p ~/.vnc
echo "$VNC_PASSWORD" | vncpasswd -f > ~/.vnc/passwd
chmod 600 ~/.vnc/passwd

cat <<EOF > ~/.vnc/xstartup
#!/bin/bash
#xrdb \$HOME/.Xresources
startxfce4 &
EOF
chmod +x ~/.vnc/xstartup

# --- VNCサーバーの起動 ---
echo "Starting VNC server on display :1 (port 5901)..."
vncserver :1 -geometry  1280x1024 -depth 24 &
VNC_PID=$!

# --- アプリケーションの起動 ---
export DISPLAY=:1
echo "Waiting for VNC server and desktop environment to start..."
sleep 5 # 少し待機時間を延ばしてみる (念のため)
echo "Starting Reversi application..."
# python:slim ベースイメージを使用する場合は python コマンドを使用
# 標準出力と標準エラー出力を /app/app.log にリダイレクト
python main.py > /app/app.log 2>&1 & # <-- この行を変更

# --- コンテナの維持 ---
echo "Container is running. Keep alive with tail -f /dev/null"
tail -f /dev/null


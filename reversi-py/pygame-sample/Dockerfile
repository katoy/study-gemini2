# ベースイメージ
FROM python:3.9-slim

# 必要パッケージのインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libportmidi-dev \
    libfreetype6-dev \
    libgl1-mesa-glx \
    xvfb \
    x11vnc \
  && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ
WORKDIR /app

# アプリケーションコードをコピー
COPY main.py .

# Pythonライブラリのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# デフォルトの環境変数
ENV SCREEN_WIDTH=600
ENV SCREEN_HEIGHT=400
ENV DISPLAY=:99

# VNCポートを公開
EXPOSE 5900

# コンテナ起動時に Xvfb, x11vnc を立ち上げたうえでアプリを実行
CMD ["bash", "-c", "\
    Xvfb ${DISPLAY} -screen 0 ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x24 & \
    x11vnc -display ${DISPLAY} -rfbport 5900 -nopw -N -forever & \
    python main.py \
"]

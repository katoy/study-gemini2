# ベースイメージとして Python slim (Debianベース) を使用
# pyproject.toml の requires-python (>=3.14.2) と CI (3.14.2) に合わせる
FROM python:3.14-slim

# 環境変数を設定 (非対話モードでパッケージインストール)
ENV DEBIAN_FRONTEND=noninteractive

# 必要なOSパッケージのインストール
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    xfce4 \
    xfce4-goodies \
    tightvncserver \
    libgl1 \
    libsdl2-2.0-0 \
    libsdl2-image-2.0-0 \
    libsdl2-mixer-2.0-0 \
    libsdl2-ttf-2.0-0 \
    dbus-x11 \
    xauth \
    xfonts-base \
    build-essential \
    python3-dev \
    pkg-config \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを作成・設定
WORKDIR /app

# プロジェクトファイルをコンテナの /app にコピー
COPY . /app

# uv をインストール
RUN pip install --no-cache-dir uv

# Python の依存関係をインストール（pyproject.toml + uv 使用）
RUN uv sync --all-extras

# startpoint.sh に実行権限を付与
RUN chmod +x /app/startpoint.sh

# VNCサーバーが使用するポートを公開
EXPOSE 5901

# コンテナ起動時に実行するコマンド
CMD ["/bin/bash", "/app/startpoint.sh"]

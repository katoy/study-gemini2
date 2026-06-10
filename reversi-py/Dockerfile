# ベースイメージとして Python slim (Debianベース) を使用
FROM python:3.10-slim-bullseye

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
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを作成・設定
WORKDIR /app

# プロジェクトファイルをコンテナの /app にコピー
COPY . /app

# uv をインストール
RUN pip install --no-cache-dir uv

# Python の依存関係をインストール（pyproject.toml + uv 使用）
RUN uv sync --all-extras

# startpoint.sh をコピーして実行権限を付与
RUN chmod +x /app/startpoint.sh

# VNCサーバーが使用するポートを公開
EXPOSE 5901

# コンテナ起動時に実行するコマンド
CMD ["/startpoint.sh"]

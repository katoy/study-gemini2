# ベースイメージとして Python slim (Debianベース) を使用
# pyproject.toml の requires-python (>=3.14.2) と CI (3.14.2) に合わせる
FROM python:3.14-slim

# 環境変数を設定 (非対話モードでパッケージインストール)
ENV DEBIAN_FRONTEND=noninteractive

# 必要なOSパッケージのインストール
# - xfce4 / tightvncserver: VNC で操作するデスクトップ環境
# - SDL2 の開発パッケージ・build-essential: pygame をソースからビルドするため
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
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
    pkg-config \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# uv をインストール
RUN pip install --no-cache-dir uv

# 作業ディレクトリを作成・設定
WORKDIR /app

# 依存関係だけを先にインストールする（コード変更時もこの層はキャッシュが効く）
# GUI・API サーバー・AlphaZero に必要な extras のみ入れ、開発用 (dev) は入れない
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --extra server --extra ml --no-install-project

# プロジェクトファイルをコンテナの /app にコピーし、プロジェクト本体をインストール
COPY . /app
RUN uv sync --frozen --extra server --extra ml

# startpoint.sh に実行権限を付与
RUN chmod +x /app/startpoint.sh

# ポート公開（-p）で届くよう、コンテナ内では全インターフェースで待ち受ける
# ホスト側の公開先は docker_start.sh で 127.0.0.1 に限定している
ENV API_HOST=0.0.0.0
ENV API_PORT=5001

# VNC サーバーと API サーバーのポートを公開
EXPOSE 5901 5001

# コンテナ起動時に実行するコマンド
CMD ["/bin/bash", "/app/startpoint.sh"]

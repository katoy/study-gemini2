Reversi Pygame Docker サンプル

このリポジトリでは、Docker コンテナ内で Pygame アプリケーションを Xvfb＋x11vnc を使って実行し、VNC 経由で画面表示する手順をまとめています。
コンテナの起動時には `startpoint.sh` スクリプトが実行され、必要なサービス（Xvfb, x11vnc）の起動と Pygame アプリケーション（main.py）の実行を管理します。

---

前提条件

- macOS (M1 または Intel)
- Docker Desktop がインストール済み
- XQuartz (X11) がインストールおよび設定済み (※ VNC接続のみの場合は不要な場合があります)
  - Preferences → Security → "Allow connections from network clients" にチェック (※ X11転送を使う場合)
  - ターミナルで xhost + または xhost +127.0.0.1 を実行し、ローカルホストからの接続を許可 (※ X11転送を使う場合)

---

プロジェクト構成

```
.
├── Dockerfile          # Dockerイメージ定義
├── requirements.txt    # Python依存ライブラリ
├── main.py             # Pygameアプリケーション本体 (例)
├── startpoint.sh       # コンテナ起動スクリプト
├── .dockerignore       # ビルドコンテキスト除外ファイル
└── README.md           # このファイル
```

---

依存関係の管理 (requirements.txt)

このプロジェクトで使用する Python ライブラリは requirements.txt ファイルにリストされています。

例: requirements.txt
```
pygame==2.5.2
# 他の依存ライブラリがあればここに追加
```

---

ビルド方法

リポジトリのルートディレクトリで以下を実行します。

```sh
docker build --platform=linux/arm64 -t my-pygame-app .
```

- --platform=linux/arm64 は M1 ネイティブ実行のための指定です。Intel Mac の場合は不要な場合があります。
- -t my-pygame-app は任意のイメージ名に変更可能です。

---

実行方法

以下のコマンドでコンテナを起動します。コンテナ起動時に `Dockerfile` の `ENTRYPOINT` で指定された `startpoint.sh` が実行されます。

```sh
docker run --rm -it \
  --platform=linux/arm64 \
  -e DISPLAY=:99 \
  -e SCREEN_WIDTH=600 \
  -e SCREEN_HEIGHT=400 \
  -e VNC_PORT=5900 \
  -e SDL_AUDIODRIVER=dummy \
  -p 5900:5900 \
  my-pygame-app
```

- `startpoint.sh` が内部で Xvfb と x11vnc をバックグラウンドで立ち上げ、最後に `main.py` を実行します。
- `-p 5900:5900` でホストのポートをコンテナの VNC ポート (環境変数 `VNC_PORT` で指定されたポート) にフォワーディングします。
- 環境変数 (`-e`) で画面サイズや VNC ポートを上書きできます。

---

VNC クライアントでの接続

1. macOS 標準の「画面共有」または RealVNC/TigerVNC などの VNC クライアントを起動します。
2. 接続先ホスト: `localhost` ポート: `5900` (または `-p` オプションや `-e VNC_PORT` で指定したポート)
3. `startpoint.sh` のデフォルト設定ではパスワードは不要です。空欄で接続してください。
4. Pygame アプリのウィンドウが表示されます。

---

環境変数

`docker run -e` で指定することで、コンテナ内の動作を変更できます。`startpoint.sh` がこれらの値を使用します。

| 変数名             | 説明                        | デフォルト (Dockerfile/startpoint.sh) |
|-------------------|----------------------------|--------------------------------------|
| SCREEN_WIDTH    | 仮想画面の幅（ピクセル）      | 600                                  |
| SCREEN_HEIGHT   | 仮想画面の高さ（ピクセル）    | 400                                  |
| DISPLAY         | Xvfb が使用するディスプレイ番号 | :99                                  |
| VNC_PORT        | x11vnc がリッスンするポート   | 5900                                 |
| SDL_AUDIODRIVER | SDLのオーディオドライバ       | dummy (音声無効化)                   |

---

注意事項

- **VNCセキュリティ:** `startpoint.sh` 内の `x11vnc` はデフォルトで `-nopw` (パスワードなし) および `-localhost` (ローカルホストからの接続のみ許可) オプション付きで起動します。ポートフォワーディング (`-p`) を介してホストマシンからのみアクセス可能です。より安全にするには、`startpoint.sh` を編集して `-passwdfile` オプション等でパスワード認証を設定してください。
- **XQuartz:** このセットアップは主に VNC を使用するため、ホスト側の XQuartz (X11サーバー) は厳密には不要な場合があります。ただし、将来的に X11 転送を試す場合などに備えて記載しています。
- **トラブルシューティング:** 問題が発生した場合は、`docker logs <container_id>` でコンテナのログ (startpoint.sh の echo 出力など) を確認してください。また、Dockerfile の内容や依存関係も確認してください。

---

以上の手順で、Docker コンテナ上の Pygame アプリを VNC 経由で表示し、開発・デバッグを行えます。

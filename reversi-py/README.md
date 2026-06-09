# Reversi (リバーシ) - Python & Pygame

![Reversi Screenshot](scrennshots/000.png)

## 概要

このプロジェクトは、Python と Pygame を使用して開発されたリバーシゲームです。人間同士の対戦はもちろん、人間対AI、AI対AIの対戦も楽しめます。3種類のAIエージェントが実装されており、それぞれ異なる戦略で対戦します。

## 特徴

*   **直感的な操作:** マウス操作で簡単に石を置くことができます。
*   **多彩な対戦モード:** 人間対人間、人間対AI、AI対AIの対戦が可能です。
*   **４種類のAIエージェント:**
    *   **FirstAgent:** 合法手の中で最初に見つかった手を置くシンプルなAI。
    *   **RandomAgent:** 合法手の中からランダムに手を選ぶAI。
    *   **GainAgent:** ひっくり返せる石の数が最大になる手を選ぶ戦略的なAI。
    *   **MonteCarloTreeSearchAgent (MCTS):** モンテカルロ木探索を用いて、より強力な手を選択するAI。
*   **ゲーム履歴:** ゲームの進行を履歴として保存し、←キーと→キーで履歴を戻ったり進んだりできます。
*   **アニメーション:** 石を置く、ひっくり返すなどのアニメーションが実装されており、視覚的に楽しめます。
*   **リスタート機能:** ゲームをリスタートすることができます。
*   **ゲーム開始機能:** ゲーム開始ボタンでゲームを開始することができます。
*   **日本語対応:** 日本語のメッセージやフォントに対応しています。
*   **ユニットテスト:** ユニットテストが実装されており、コードの品質を保っています。
*   **パス機能:** 合法手がない場合、自動的にパスします。

## 変更履歴 (2026-06-06)

- UI: AI(黒)/AI(白) のバッジ表示を GUI から削除しました。AI 同士の対戦でどちらの手かはコンソールログで識別します。
  - 例: `AI (Black, First) placed stone at (6, 4).`
- ログ: AI の打ち手ログに「色」と「エージェント表示名」を追加しました。レンダリングの頻繁なログは DEBUG に落とし、同一メッセージの急速な重複を抑えるスロットリングフィルタを導入しています（utils/logging_utils.ThrottlingFilter）。
- GUI: ウィンドウ幅の自動縮小は GameGUI のコンストラクタ引数 `allow_width_shrink` で制御できます。`main.py` は既定で `allow_width_shrink=True` です。
- フォント: デフォルトフォントサイズを 24 → 20 に調整。`pygame.font` が利用できない環境では `pygame._freetype` にフォールバックする堅牢なフォントローダを実装しました。
- テスト/CI: ローカルで CI と同等のチェックを実行するスクリプト `./scripts/ci_check.sh` を用意しました。

## 動作環境

*   Python 3.14 以上
*   Pygame

## インストール

1.  リポジトリをクローンします。

    ```bash
    git clone https://github.com/your-username/reversi-py.git
    cd reversi-py
    ```

2.  依存関係をインストールします。

    ```bash
    uv sync
    ```

    API サーバーも使う場合：

    ```bash
    uv sync --all-extras
    ```

## 実行方法

プロジェクトのルートディレクトリで `main.py` を実行します。

```bash
uv run python main.py
```

または：

```bash
python main.py
```

## 使い方

*   **ゲーム開始:** 画面中央の「ゲーム開始」ボタンをクリックします。
*   **石を置く:** 合法手が表示されているマスをクリックします。
*   **リスタート:** ゲーム中またはゲームオーバー時に画面下部の「リスタート」ボタンをクリックします。
*   **ゲーム履歴:** ←キーで履歴を戻り、→キーで履歴を進みます。

## AIエージェントの詳細

このゲームには、以下の3種類のAIエージェントが実装されています。

*   **FirstAgent:** 合法手の中で最初に見つかった手を置きます。最も単純なAIです。
*   **RandomAgent:** 合法手の中からランダムに手を選びます。予測不能な動きが特徴です。
*   **GainAgent:** ひっくり返せる石の数が最大になる手を選びます。より戦略的な思考を持つAIです。

## テスト

### テスト実行

pytest を使用してテストを実行します。

```bash
uv run pytest tests/
```

### テストカバレッジの計測

カバレッジを計測付きでテストを実行：

```bash
uv run pytest tests/ --cov=. --cov-report=term-missing --cov-config=.coveragerc
```

カバレッジレポートの表示：

```bash
uv run pytest --cov=. --cov-report=term-missing --cov-config=.coveragerc
```

HTML 形式の詳細レポートを生成：

```bash
uv run pytest tests/ --cov=. --cov-report=html --cov-config=.coveragerc
```

レポートは `htmlcov/index.html` をブラウザで開いて確認できます。


## ファイル構成

```
.
├── agents/                 # AIエージェント関連のモジュール
│   ├── __init__.py         # agentsディレクトリをパッケージとして認識させるため
│   ├── api_agent.py        # APIサーバーを利用するエージェント (推測)
│   ├── base_agent.py       # エージェントの基底クラス
│   ├── first_agent.py      # 最初の有効な手を選択するエージェント
│   ├── gain_agent.py       # 獲得数が最大になる手を選択するエージェント
│   ├── mcts_agent.py       # モンテカルロ木探索エージェント
│   └── random_agent.py     # ランダムに有効な手を選択するエージェント
├── board.py                # ボードの状態管理とロジック (石の配置、合法手の判定など)
├── config/                 # 設定ファイル
│   ├── agents.py           # 使用するエージェントの設定など (推測)
│   └── theme.py            # GUIの色や画面サイズなどのテーマ設定
├── Dockerfile              # Dockerイメージをビルドするための設定ファイル
├── fonts/                  # GUIで使用するフォントファイル
│   ├── NotoSansJP-Regular.ttf
│   └── NotoSansJP-VariableFont_wght.ttf
├── game.py                 # ゲーム全体の進行管理 (ターン管理、ゲームオーバー判定、履歴管理など)
├── gui.py                  # Pygameを使用したGUIの描画とイベント処理
├── images/                 # GUIで使用する画像ファイル (石、背景など)
│   ├── black.jpg
│   ├── black.png
│   ├── hintB.jpg
│   ├── hintW.jpg
│   ├── void.jpg
│   └── white.jpg
├── LICENSE                 # プロジェクトのライセンス情報
├── main.py                 # アプリケーションのエントリーポイント (ゲームの初期化と実行)
├── README.md               # このファイル (プロジェクトの説明書)
├── requirements.txt        # プロジェクトの依存ライブラリリスト
├── reversi.pu              # PlantUMLなどで記述された設計図など (推測)
├── server/                 # APIサーバー関連のモジュール (推測)
│   └── api_server.py       # AIの手を返すAPIサーバーの実装 (推測)
├── startpoint.sh           # Dockerコンテナ起動時のエントリーポイントスクリプト (推測)
└── tests/                  # ユニットテストコード
    ├── __init__.py         # testsディレクトリをパッケージとして認識させるため
    ├── agents/             # エージェントのテスト
    │   ├── __init__.py     # agentsテストディレクトリをパッケージとして認識させるため
    │   ├── test_api_agent.py
    │   ├── test_base_agent.py
    │   ├── test_first_agent.py
    │   ├── test_gain_agent.py
    │   ├── test_mcts_agent.py
    │   └── test_random_agent.py
    ├── config/             # 設定関連のテスト
    │   └── test_agents.py
    ├── server/             # サーバー関連のテスト (タイポ修正: serverß -> server)
    │   └── test_api_server.py
    ├── test_board.py       # ボードロジックのテスト
    ├── test_game.py        # ゲームロジックのテスト
    ├── test_gui.py         # GUI関連のテスト (存在する場合)
    └── test_main.py        # mainモジュールのテスト (存在する場合)

```

## Docker を使用した実行 (VNC 接続)

Docker がインストールされていれば、以下の手順でコンテナを起動し、VNC クライアントから GUI を操作できます。

1.  **Docker イメージのビルド:**

    プロジェクトのルートディレクトリで以下のコマンドを実行し、Docker イメージをビルドします。

    ```bash
    docker build -t reversi-py .
    ```

2.  **Docker コンテナの起動:**

    ビルドしたイメージを使ってコンテナを起動します。ここでは、ホストマシンの `5901` ポートをコンテナの VNC サーバーポート (`5901`) に接続します。

    ```bash
    docker run -d -p 5901:5901 --name reversi-container reversi-py
    ```

    *   `-d`: バックグラウンドでコンテナを実行します。
    *   `-p 5901:5901`: ホストのポート 5901 をコンテナのポート 5901 にマッピングします。コンテナ側の VNC ポートが異なる場合は、`:` の右側を適宜変更してください。
    *   `--name reversi-container`: コンテナに `reversi-container` という名前を付けます。
    *   `reversi-py`: 使用する Docker イメージ名です。

3.  **VNC クライアントでの接続:**

    お使いの VNC クライアント (例: RealVNC Viewer, TightVNC Viewer, macOS の画面共有など) を起動し、以下の情報で接続します。

    *   **接続先アドレス:** `localhost:5901` または `127.0.0.1:5901`
    *   **パスワード:** (もし Dockerfile や startpoint.sh で VNC パスワードが設定されている場合は、そのパスワードを入力してください。設定されていない場合は不要な場合があります。)

    接続に成功すると、コンテナ内で実行されている Reversi ゲームの GUI が表示されます。

4.  **コンテナの停止と削除:**

    ゲームを終了したら、以下のコマンドでコンテナを停止・削除できます。

    ```bash
    # コンテナの停止
    docker stop reversi-container

    # コンテナの削除
    docker rm reversi-container
    ```

---

## テストと品質管理

### ローカルで CI チェックを実行

以下のスクリプトを実行すると、GitHub Actions と同等のチェックをローカルで実行できます：

```bash
./scripts/ci_check.sh
```

このスクリプトは以下の 4 つのチェックを実行します：

1. **Lint チェック (ruff):** コード規約違反を検出
2. **型チェック (mypy):** 型安全性を検証
3. **テスト実行:** 200+ のユニットテストを実行
4. **カバレッジ確認:** GUI 以外は 100% のカバレッジを確認

### カバレッジ

- **全体:** 96%（GUI テスト含む）
- **GUI 以外:** 99%+（CI で強制）
- **対象ファイル:** agents/, board.py, game.py, config/agents_config.py, utils/ など
- **除外ファイル:** gui.py, config/game_constants.py（設定値定義のため）

### CI/CD パイプライン

GitHub Actions で以下の CI チェックが自動実行されます（push/pull_request 時）：

1. **Lint チェック (ruff):** Python コード品質検査（E, W, F ルール、E501 除外）
2. **型チェック (mypy):** 型安全性検証
3. **テスト実行 (pytest):** 200+ のユニットテスト実行
4. **カバレッジ確認:** GUI 除外時の 99%+ カバレッジ確認

詳細は [.github/workflows/ci.yml](.github/workflows/ci.yml) を参照してください。

---

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。詳細については、LICENSE ファイルを参照してください。

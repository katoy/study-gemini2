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

## 動作環境

*   Python 3.7 以上
*   Pygame

## インストール

1.  リポジトリをクローンします。

    ```bash
    git clone https://github.com/your-username/reversi-py.git
    ```

2.  必要なライブラリをインストールします。

    ```bash
    pip install pygame
    ```

## 実行方法

1.  プロジェクトのルートディレクトリに移動します。

    ```bash
    cd reversi-py
    ```

2.  `main.py` を実行します。

    ```bash
    python3 main.py
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

テストを実行するには、以下のコマンドを使用します。

```bash
python3 -m unittest discover -s tests -t .
```

## テストカバレッジの計測
テストカバレッジを計測するには、`coverage.py` ライブラリを使用します。

1.  **`coverage.py` のインストール:** (まだインストールしていない場合)
    ```bash
    pip install coverage
    ```

2.  **カバレッジデータの削除 (任意):**
    以前の計測データ (`.coverage` ファイル) が残っている場合は、以下のコマンドで削除できます。
    ```bash
    python3 -m coverage erase
    ```

3.  **カバレッジ計測付きでテストを実行:**
    以下のコマンドでテストを実行し、その間のコードカバレッジを計測します。
    ```bash
    python3 -m coverage run -m unittest discover tests
    ```
    *   `coverage run`: カバレッジ計測を開始します。
    *   `-m unittest discover tests`: `unittest` の `discover` 機能を使って `tests` ディレクトリ内のテストを実行します。

4.  **カバレッジレポートの生成:**
    計測結果をレポートとして表示します。

    *   **テキスト形式レポート (コンソール表示):**
        ```bash
        python3 -m coverage report -m --omit="tests/*"
        ```
        *   `coverage report`: テキスト形式でレポートを表示します。
        *   `-m`: カバレッジが100%でないファイルの未実行行番号を表示します。
        *   `--omit="tests/*"`: `tests` ディレクトリ以下のファイル（テストコード自体）をレポートから除外します。

    *   **HTML形式レポート (詳細表示):**
        ```bash
        python3 -m coverage html --omit="tests/*"
        ```
        *   `coverage html`: HTML形式で詳細なレポートを生成します。
        *   レポートは `htmlcov` ディレクトリに生成されます。`htmlcov/index.html` をブラウザで開いて、ファイルごとに行単位のカバレッジ状況を確認できます。
        *   `--omit="tests/*"`: テストコード自体をレポートから除外します。

5.  **カバレッジデータの削除:**
    計測データ (`.coverage` ファイル) が不要になった場合は、以下のコマンドで削除します。
    ```bash
    python3 -m coverage erase
    ```

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

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。詳細については、LICENSE ファイルを参照してください。

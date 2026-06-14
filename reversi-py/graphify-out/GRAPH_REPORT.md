# Graph Report - reversi-py  (2026-06-14)

## Corpus Check
- 97 files · ~55,718 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1020 nodes · 1693 edges · 96 communities (56 shown, 40 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 156 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7d23d41c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]

## God Nodes (most connected - your core abstractions)
1. `Game` - 93 edges
2. `GameGUI` - 61 edges
3. `Board` - 51 edges
4. `TestGameGUI` - 50 edges
5. `TestApp` - 34 edges
6. `ApiAgent` - 31 edges
7. `App` - 31 edges
8. `TestApiServer` - 31 edges
9. `MonteCarloTreeSearchAgent` - 30 edges
10. `_t()` - 30 edges

## Surprising Connections (you probably didn't know these)
- `ApiAgent` --uses--> `Game`  [INFERRED]
  agents/api_agent.py → game.py
- `TestApiAgent` --uses--> `ApiAgent`  [INFERRED]
  tests/agents/test_api_agent.py → agents/api_agent.py
- `TestMonteCarloTreeSearchAgent` --uses--> `ApiAgent`  [INFERRED]
  tests/agents/test_mcts_agent.py → agents/api_agent.py
- `TestApiAgentIntegration` --uses--> `ApiAgent`  [INFERRED]
  tests/integration/test_api_integration.py → agents/api_agent.py
- `TestServerEndpoint` --uses--> `ApiAgent`  [INFERRED]
  tests/integration/test_api_integration.py → agents/api_agent.py

## Import Cycles
- 1-file cycle: `server/api_server.py -> server/api_server.py`
- 1-file cycle: `main.py -> main.py`

## Communities (96 total, 40 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (28): Any, Button, Color, 画面サイズやUI要素のサイズを定義するクラス。, Screen, Label, Surface, GameGUI should enlarge window height when initialized too small and place start (+20 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (17): _t(), GameGUI, Rect, Label インスタンスをキャッシュから取得する（なければ生成）, Pygame ベースのリバーシゲーム UI。      責務：     1. レイアウト計算：ウィンドウサイズ、要素の配置座標を計算     2. UI描画：盤, 同梱された日本語フォントをロードする          Prefer pygame.font when available (helps tests that, 計算: すべてのUI要素が表示されるために必要な最小ウィンドウ高さを返す          Uses a conservative estimate (pref, 盤面の描画領域(Rect)を計算する          Chooses the largest square board (multiple of 8) tha (+9 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (26): API呼び出しまたはその後の処理で予期せぬ例外が発生した場合、Noneを返すことをテスト, Exception, GameGUI, LogRecord, App, main(), Game, Pygameのイベントを処理する。         QUITイベントで実行フラグをFalseにし、左マウスクリック位置を返す。          Returns (+18 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (38): AI エージェント, AI 非同期実行の安全機構, API サーバー, Docker を使わない実行（ローカル環境）, Docker を使用した実行（コンテナ環境）, Docker イメージのビルド, Docker コンテナの起動, POST /play のリクエスト仕様 (+30 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (10): ゲーム開始前の _update_state のテスト, ゲームオーバー時の _update_state のテスト, ゲーム中の _update_state のテスト, ゲームオーバー時のリスタートボタンクリック, ゲームオーバー時のリセットボタンクリック (詳細), プレイヤー選択ラジオボタンのクリック (変更なし), AI手番での予期しない place_stone の失敗, _handle_eventsメソッドのテスト (+2 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (9): NEGAMAX_TIME_LIMIT_MS 環境変数が反映される。, VALID_AGENT_TYPES 外の文字列を渡すと None を返す（行 87 カバー）。, PlayRequest.model_dump() が RuntimeError を投げると外側 catch-all が 500 を返す（行 176-180 カバ, board が list of lists でない場合 422 を返す, board の要素が list でない場合 422 を返す, 巨大盤面（DoS 防止の上限超え）は 400 を返す, agent.play() が例外を投げると 500 を返す, _create_game() が例外を投げると 500 を返す (+1 more)

### Community 6 - "Community 6"
Cohesion: 0.09
Nodes (19): get_agent_params(), 指定されたIDに対応するエージェントの初期化パラメータを返す。     Args:         agent_id (int): エージェントID     R, get_agent_class(), get_agent_definition(), get_agent_options(), GUIのラジオボタンなどで使用するためのエージェント選択肢リストを返す。     Returns:         list[tuple[int, str]]:, 指定されたIDに対応するエージェントクラスを返す。     Args:         agent_id (int): エージェントID     Returns, 指定されたIDに対応するエージェントの完全な定義辞書を返す。     Args:         agent_id (int): エージェントID     Re (+11 more)

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (16): デフォルトのtimeout値を使用してAPIが呼び出されることをテスト, play() が agent_type を JSON ペイロードに含めて送信する, APIが {"move": null} を返した場合、None を返すことをテスト, APIがエラーステータスコード (例: 500) を返した場合、None を返すことをテスト, APIリクエストがタイムアウトした場合、None を返すことをテスト, APIサーバーへの接続に失敗した場合、None を返すことをテスト, APIリクエスト中に一般的なRequestExceptionが発生した場合、Noneを返すことをテスト, APIが不正なJSONレスポンスを返した場合、None を返すことをテスト (+8 more)

### Community 8 - "Community 8"
Cohesion: 0.11
Nodes (29): make_app(), App は _ai_generation 属性（初期値 0）を持つ, _invalidate_ai_thinking() を呼ぶと _ai_generation が増加する, _invalidate_ai_thinking() はキューに積まれた古い結果を捨てる, 世代が一致しない AI 結果は盤面に適用されない, 世代が一致する AI 結果は盤面に適用される, ゲーム中にプレイヤー設定を変更すると AI 思考が無効化される, ゲーム開始前のプレイヤー設定変更では _ai_generation が変化しない (+21 more)

### Community 9 - "Community 9"
Cohesion: 0.09
Nodes (14): MonteCarloTreeSearchAgent, Monte Carlo Tree Search エージェントを初期化します。          Args:             iterations: シミ, is_terminal_node が終端状態を正しく判定するかテスト (行 93), 有効な手がない場合にNoneを返すことを確認, 有効な手が1つしかない場合にその手を直接返すかテスト (行 107), 簡単な盤面で獲得数の多い手を選ぶ傾向があるか確認, 時間制限によってループが終了するかテスト (行 113-115), Node.expand が未試行の手がない場合に None を返すかテスト (+6 more)

### Community 10 - "Community 10"
Cohesion: 0.10
Nodes (7): エージェントが盤面に実際に手を打つことを確認するテスト, MCTSエージェントが盤面に実際に手を打つことを確認するテスト, Game, 指定されたインデックスの履歴状態に盤面と手番を復元する, 現在の履歴インデックスに対応する履歴データを取得する, リバーシゲームの制御。ゲームロジックと盤面管理を担当。      責務：     - 盤面管理：Board インスタンスを保有、石の配置     - ターン管理, main()

### Community 11 - "Community 11"
Cohesion: 0.11
Nodes (9): Node, MCTS を実行して最善の手を選択します。          Args:             game: 現在のゲーム状態。          Return, ランダムプレイアウトを実行し、勝者 (-1: 黒, 1: 白, 0: 引き分け) を返す, 勝者 (-1/1/0) をルートまで伝播させる。          各ノードの wins は「そのノードへの着手を選んだプレイヤー（親ノードの, ノードが終端状態かチェックし、勝者 (-1/1/0) を返す。終端でなければ None。, UCB1スコアが最も高い子ノードを選択する, 未試行の手から一つ選び、新しい子ノードを生成して返す, select_child がUCB1スコアが同点の訪問済みの子をシャッフルするかテスト (行 49 カバー) (+1 more)

### Community 12 - "Community 12"
Cohesion: 0.09
Nodes (22): `agents/api_agent.py`, API Design, API tests, `ApiAgent` tests, Assumptions, CI / Postman, `config/agents_config.py`, Current status (+14 more)

### Community 13 - "Community 13"
Cohesion: 0.16
Nodes (13): _disc_diff(), _evaluate(), _phase_coeffs(), Negamax（アルファベータ枝刈り + 反復深化 + 終盤読み切り）エージェント。  純 Python・依存ゼロで現 MCTS より深く読む API プレイヤ, 盤面の埋まり具合からゲームフェーズの係数組を返す。      Args:         board: 盤面（0=空, 1=白, -1=黒）。, 各角から辺に沿って連続する color の石を数える（簡易確定石カウント）。      Args:         board: 盤面。         n:, 手番側から見た石差。      Args:         board: 盤面。         turn: 手番（1=白, -1=黒）。      Retur, 終局局面の確定スコア（手番側視点）。      Args:         board: 盤面。         turn: 手番（1=白, -1=黒）。 (+5 more)

### Community 14 - "Community 14"
Cohesion: 0.16
Nodes (14): _deterministic_agent(), _initial_board(), _make_game(), 探索に必要な最小限の Game モックを作る。, 時間制限を実質無効化した決定論的エージェント。, NegamaxAgent.play の振る舞いテスト。, 角が合法手なら角を選ぶ（深さ 2 で十分）。, time_limit_ms=1 でも depth 1 の結果で合法手を返す。 (+6 more)

### Community 15 - "Community 15"
Cohesion: 0.13
Nodes (15): _apply(), NegamaxAgent, _apply の逆操作で盤面を元に戻す。      Args:         board: 盤面（破壊的に変更される）。         move: 着手（行, Negamax + アルファベータ枝刈りで先読みする AI エージェント。      反復深化により常に時間内で読めた最深の結果を返す。     終盤（空きマス, NegamaxAgent を初期化します。          Args:             time_limit_ms: 思考時間の上限（ミリ秒）。, 反復深化探索で最善手を選択します。          Args:             game: 現在のゲーム状態。          Returns:, ルート局面を深さ depth で探索し最善手を返す。          Args:             board: 盤面。             n:, 手番側視点の negamax 値を返す（アルファベータ枝刈り付き）。          Args:             board: 盤面。 (+7 more)

### Community 16 - "Community 16"
Cohesion: 0.10
Nodes (5): 両者パスでゲームオーバーになる実際の盤面でテスト, エージェント初期化時に TypeError が発生するケースをテスト (行 100-104), エージェント初期化時に一般的な Exception が発生するケースをテスト (行 105-108), create_agent が人間プレイヤー(ID=0)や不明なIDに対して None を返すかテスト, TestGame

### Community 17 - "Community 17"
Cohesion: 0.13
Nodes (5): DummyBoard, PassBoard, 手番側に合法手がなく、相手側にだけ合法手がある盤面スタブ, 手番側に合法手がない（パス）場合、相手手番のノードとして扱う, TestMCTSNode

### Community 18 - "Community 18"
Cohesion: 0.17
Nodes (15): _get_translator(), 遅延初期化により、モジュール読み込み時の状態汚染を防止, Translator, locale.getlocale() が (None, ...) を返す場合のカバレッジ, _get_translator の遅延初期化をテスト, test_get_translator_lazy_initialization(), test_load_translations_invalid_format(), test_load_translations_json_decode_error() (+7 more)

### Community 19 - "Community 19"
Cohesion: 0.12
Nodes (9): ApiAgent, 外部 API サーバーから手を取得する AI エージェント。, ApiAgent を初期化します。          Args:             api_url: 接続先の API サーバーの URL。, API サーバーから次の手を取得します。          Args:             game: 現在のゲーム状態。             time, agent_type を変更後の次回 play() に新しい値が反映される, 初期化時に空のURLが渡された場合に ValueError を発生させることをテスト, timeout引数を指定した場合、その値が設定されることをテスト, __init__ で指定した agent_type が属性に保存される (+1 more)

### Community 20 - "Community 20"
Cohesion: 0.14
Nodes (6): Board, 盤面の黒石と白石の数を数えます。          Returns:             (黒石数, 白石数) のタプル。, 現在の盤面を取得します。          Returns:             2次元リスト。0: 空、-1: 黒、1: 白。, Board を初期化します。          Args:             board_size: 盤面のサイズ（デフォルトは 8×8）。, オセロ（リバーシ）の盤面管理。盤操作に特化した責務分離クラス。      責務：     - 盤面データ管理：石の配置状態（-1=黒, 0=空, 1=白）, TestBoard

### Community 21 - "Community 21"
Cohesion: 0.11
Nodes (17): 1. 背景と動機, 2.1 クラスとファイル配置, 2.2 内部探索: make/unmake 方式（deepcopy 排除）, 2.3 評価関数, 2.4 可変盤面サイズ (4-16) 対応: 重みテーブルのサイズ非依存生成, 2.5 探索と時間管理, 2.6 パス処理, 2.7 決定論 (+9 more)

### Community 22 - "Community 22"
Cohesion: 0.17
Nodes (9): GainAgent, 最も多くの石を獲得できる手を選択する AI エージェント。, 有効な手の中から、最も多くの石を獲得できる手を選択します。          複数の手が同じ数の石を獲得できる場合、その中からランダムに 1 つを選択します。, 有効な手がない場合にNoneを返すことをテストする, エージェントが盤面に実際に手を打つことを確認するテスト, 特定の盤面で、GainAgentが最も獲得数の多い有効な手を返すことをテストする。         (最大獲得数の手が1つのケース), GainAgentが盤面に実際に手を打つことを確認するテスト, 最大獲得数の手が複数ある場合に、そのいずれかを返すことをテストする。 (+1 more)

### Community 23 - "Community 23"
Cohesion: 0.12
Nodes (15): 1. 背景と動機, 2. エンジン選定, 3.1 プロセス統合方式: 常駐 subprocess + ロック（採用）, 3.2 盤面の受け渡し, 3.3 クラス設計（2 ファイル分離でテスト容易性を確保）, 3.4 8x8 以外の盤面: 内部フォールバック（採用）, 3.5 設定と運用, 3. アーキテクチャ (+7 more)

### Community 25 - "Community 25"
Cohesion: 0.21
Nodes (8): _flips_for_move(), 着手 (row, col) で反転する石のリストを返す（空なら不合法手）。      board.py の Board._get_flipped_in_dire, turn 側の合法手を row-major 順で返す。      Args:         board: 盤面（0=空, 1=白, -1=黒）。, _valid_moves(), 合法手生成と make/unmake のテスト。, モジュール内の合法手生成が Board.get_valid_moves と一致する。, _apply して _undo すると盤面が完全に元へ戻る。, TestSearchPrimitives

### Community 26 - "Community 26"
Cohesion: 0.23
Nodes (6): RandomAgent, ランダムに合法手を選択する AI エージェント。, 合法手からランダムに選択します。          Args:             game: 現在のゲーム状態。          Returns:, エージェントが盤面に実際に手を打つことを確認するテスト, RandomAgentが盤面に実際に手を打つことを確認するテスト, TestRandomAgent

### Community 27 - "Community 27"
Cohesion: 0.26
Nodes (10): BaseModel, JSONResponse, _create_game(), play(), PlayRequest, Game, ボードデータと手番から一時的な Game オブジェクトを生成する。, agent_type 文字列に対応するエージェントインスタンスを返す。 (+2 more)

### Community 28 - "Community 28"
Cohesion: 0.25
Nodes (6): _make_mock_game(), API サーバーと ApiAgent の統合テスト。  実際の uvicorn サーバープロセスに対して requests / ApiAgent で通信し、 エ, サーバーが 400 を返しても ApiAgent は None を返してクラッシュしない。, 存在しないサーバーへの接続失敗時に ApiAgent は None を返す。, ApiAgent が実際のサーバーと通信するエンドツーエンドテスト群。, TestApiAgentIntegration

### Community 29 - "Community 29"
Cohesion: 0.18
Nodes (10): NegamaxAgent 実装計画, Task 1: 位置重みテーブル `_build_weight_table`, Task 2: 探索プリミティブ（合法手・反転・make/unmake）, Task 3: 評価関数（フェーズ係数・確定石・終局スコア）, Task 4: NegamaxAgent 本体（反復深化・時間管理・パス処理）, Task 5: API サーバーへの登録, Task 6: 統合テストと conftest の環境変数, Task 7: GUI への登録 (+2 more)

### Community 30 - "Community 30"
Cohesion: 0.18
Nodes (10): API ドキュメント, Reversi API (リバーシ API), インストール, エンドポイント, テスト, ライセンス, 使い方, 依存関係 (+2 more)

### Community 31 - "Community 31"
Cohesion: 0.22
Nodes (5): 指定位置に石を配置し、反転処理を行います。          Args:             row: 行番号（0-indexed）。, 指定位置に石を配置した場合に反転する石のリストを取得します。          Args:             row: 行番号（0-indexed）。, 指定方向でひっくり返す石を取得します。          Args:             row: 開始行番号。             col: 開始列番, 指定位置への石の配置が合法手かを判定します。          Args:             row: 行番号（0-indexed）。, 指定されたプレイヤーの合法手をすべて取得します。          Args:             turn: プレイヤー（-1: 黒、1: 白）。

### Community 32 - "Community 32"
Cohesion: 0.20
Nodes (9): EdaxAgent（外部エンジン統合）実装計画, Task 1: 盤面変換の純粋関数, Task 2: EdaxEngine プロセス管理クラス, Task 3: 共有エンジンシングルトンと EdaxAgent, Task 4: API サーバーへの登録と 503 ハンドリング, Task 5: GUI への登録, Task 6: 導入スクリプト setup_edax.sh, Task 7: 実バイナリ統合テスト（skipif 付き） (+1 more)

### Community 33 - "Community 33"
Cohesion: 0.33
Nodes (4): Agent, 現在のゲーム状態から最善の手を選択します。          Args:             game: ゲーム状態。          Returns:, AI エージェントの基本インターフェース。, TestBaseAgent

### Community 34 - "Community 34"
Cohesion: 0.33
Nodes (4): FirstAgent, 最初に見つかった合法手を選択する単純な AI エージェント。, 合法手の中から最初に見つかった手を返します。          Args:             game: 現在のゲーム状態。          Retur, TestFirstAgent

### Community 35 - "Community 35"
Cohesion: 0.33
Nodes (4): _build_weight_table(), サイズ n の位置重みテーブルをマスの役割から生成する。      最寄りの辺までの距離 (er, ec) で役割を判定するため、     どの盤面サイズでも一, テーブルは 90 度回転で不変（4 回回転対称）。, TestBuildWeightTable

### Community 36 - "Community 36"
Cohesion: 0.22
Nodes (5): 4x4 の残り 1 マスを埋める唯一の合法手を完全読みで選ぶ。, 手番側に合法手がなく相手にある局面では手番交代して探索を続ける。          パス処理は深さを消費しない（深さ 2 で黒パス → 白着手 → 黒評価値が返, 双方に合法手がない局面は終局として確定スコアを返す。, depth が空きマス数に達したら完全読み切り済みとして break する（行 354 カバー）。          board: 4x4、空きマス 2 つ（(, TestEndgameAndPass

### Community 37 - "Community 37"
Cohesion: 0.39
Nodes (6): Namespace, do_check(), main(), parse_args(), Lightweight Norman shim for local/CI installs.  This module provides a minimal `, run_command()

### Community 38 - "Community 38"
Cohesion: 0.25
Nodes (7): devDependencies, newman, name, private, scripts, newman:run, version

### Community 40 - "Community 40"
Cohesion: 0.40
Nodes (5): api_server_url(), 統合テスト用の pytest フィクスチャ。  実際の uvicorn サーバーを subprocess で起動し、 テスト終了後に確実に停止する sessio, 指定ポートが LISTEN 状態になるまで socket polling で待機する。, 実際の uvicorn サーバーを port 5002 で起動し、URL を yield する。      Notes:         port 5002 を, _wait_for_port()

### Community 41 - "Community 41"
Cohesion: 0.53
Nodes (4): run_newman(), start_server_if_needed(), wait_for_server(), run_postman_api_tests.sh script

### Community 42 - "Community 42"
Cohesion: 0.50
Nodes (4): CellState, GameConstants, Player, IntEnum

### Community 43 - "Community 43"
Cohesion: 0.70
Nodes (4): start_server(), stop_server(), wait_for_server(), restart_server.sh script

### Community 44 - "Community 44"
Cohesion: 0.50
Nodes (3): Localization (i18n) Implementation Plan, Task 1: Create `config/i18n.py`, Task 2: Update Translation Files

### Community 45 - "Community 45"
Cohesion: 0.50
Nodes (3): DISPLAY, USER, startpoint.sh script

## Knowledge Gaps
- **123 isolated node(s):** `GameConstants`, `Namespace`, `check.sh script`, `ci_check.sh script`, `docker_start.sh script` (+118 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **40 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Game` connect `Community 10` to `Community 0`, `Community 1`, `Community 2`, `Community 4`, `Community 6`, `Community 8`, `Community 9`, `Community 11`, `Community 13`, `Community 15`, `Community 16`, `Community 19`, `Community 20`, `Community 22`, `Community 24`, `Community 26`, `Community 27`, `Community 33`, `Community 34`?**
  _High betweenness centrality (0.382) - this node is a cross-community bridge._
- **Why does `Board` connect `Community 20` to `Community 35`, `Community 36`, `Community 5`, `Community 6`, `Community 9`, `Community 10`, `Community 11`, `Community 13`, `Community 14`, `Community 16`, `Community 51`, `Community 52`, `Community 53`, `Community 22`, `Community 19`, `Community 25`, `Community 27`, `Community 31`?**
  _High betweenness centrality (0.145) - this node is a cross-community bridge._
- **Why does `TestGameGUI` connect `Community 24` to `Community 0`, `Community 1`, `Community 10`, `Community 34`, `Community 61`, `Community 62`, `Community 63`, `Community 64`, `Community 65`, `Community 66`, `Community 67`, `Community 68`, `Community 69`, `Community 70`, `Community 71`, `Community 72`, `Community 73`, `Community 74`, `Community 75`, `Community 76`, `Community 77`, `Community 78`, `Community 79`, `Community 80`, `Community 81`, `Community 82`, `Community 83`, `Community 84`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `Game` (e.g. with `ApiAgent` and `Agent`) actually correct?**
  _`Game` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `GameGUI` (e.g. with `GameGUI` and `Color`) actually correct?**
  _`GameGUI` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `Board` (e.g. with `TestGainAgent` and `TestMonteCarloTreeSearchAgent`) actually correct?**
  _`Board` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `TestGameGUI` (e.g. with `FirstAgent` and `Color`) actually correct?**
  _`TestGameGUI` has 6 INFERRED edges - model-reasoned connections that need verification._
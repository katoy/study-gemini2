# Graph Report - reversi-py  (2026-11-24)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1727 nodes · 3917 edges · 113 communities (47 shown, 66 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 655 edges (avg confidence: 0.88)
- Token cost: 105,154 input · 1,605 output

## Graph Freshness
- Built from commit: `b8538cdb`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ラジオボタン描画
- GUI 描画メソッド
- App メインループ
- README プロジェクト概要
- App 状態更新テスト
- AlphaZero MCTS 探索
- エージェント設定定義
- 置換表 Negamax エージェント
- AI 思考世代管理テスト
- OthelloNNet と損失関数
- ゲーム進行と自己対戦
- MCTS エージェント
- API 設計プラン
- Negamax 評価関数
- パターン評価関数
- αβ 探索コア
- ビットボード教師エージェント
- MCTS ノード UCB1
- 多言語化 i18n
- API 統合テスト
- 盤面ロジック Board
- API サーバーテスト
- GainAgent
- ReversiNet ResNet モデル
- 盤面テンソル変換
- RandomAgent
- GameGUI レイアウトテスト
- パターン学習とベンチマーク
- 教師データ生成テスト
- サーバー README
- AlphaZeroAgent
- リプレイバッファ
- AI エージェントモジュール群
- エージェント基底と Game
- 位置重みテーブル
- Negamax と強さ検証
- PatternAgent 探索
- AlphaZero MCTS テスト
- Minimax 探索エージェント
- Postman テストスクリプト
- ゲーム定数
- サーバー再起動スクリプト
- CI ワークフロー
- AlphaZero-Minimax 訓練スクリプト
- サーバー付き起動スクリプト
- サーバー停止スクリプト
- アプリ起動とカバレッジ
- GameGUI 寸法計算
- エージェント生成
- Edax 統合設計とエージェント選択
- 盤面座標とクリック判定
- ハイブリッド訓練 CLI
- Gemini 設定ドキュメント
- Copilot 指示書
- チェックスクリプト
- CI チェックスクリプト
- Docker 起動スクリプト
- Docker 停止スクリプト
- 起動スクリプト
- ApiAgent 初期化
- ログ抑制フィルタ
- 評価結果と信頼区間
- AlphaZero 評価スクリプト
- Zobrist ハッシュ
- GUI テーマと UI 要素
- 置換表エージェント基本テスト
- D4 データ拡張
- 置換表とキラームーブ
- AlphaZero 着手と make/unmake
- プロジェクト構成概要
- Negamax 終盤パステスト
- Button テスト
- Label と UI 部品
- 時間制限テスト
- Negamax 実装計画
- Edax 統合設計書
- 置換表エージェント初期化テスト
- パス盤面スタブ
- Edax 実装計画
- 探索プリミティブテスト
- オンボーディングガイド
- Newman API テスト設定
- Negamax 仕様
- API エンドポイント実装
- Negamax 設計書
- サーバーエンドポイントテスト
- GUI 高さ調整テスト
- GUI 幅テスト
- reversi-pyプロジェクトルート

## God Nodes (most connected - your core abstractions)
1. `Game` - 139 edges
2. `GameGUI` - 75 edges
3. `NegamaxAgent` - 58 edges
4. `TestGameGUI` - 54 edges
5. `Board` - 52 edges
6. `TranspositionNegamaxAgent` - 51 edges
7. `Agent` - 44 edges
8. `OthelloNNet` - 44 edges
9. `TestApiServer` - 39 edges
10. `App` - 37 edges

## Surprising Connections (you probably didn't know these)
- `1. 背景と動機` --references--> `MonteCarloTreeSearchAgent`  [INFERRED]
  docs/superpowers/specs/2026-06-13-edax-agent-design.md → agents/mcts_agent.py
- `7. 案 A（Negamax）との関係` --references--> `NegamaxAgent`  [INFERRED]
  docs/superpowers/specs/2026-06-13-edax-agent-design.md → agents/negamax_agent.py
- `3.1 プロセス統合方式: 常駐 subprocess + ロック（採用）` --references--> `ApiAgent`  [INFERRED]
  docs/superpowers/specs/2026-06-13-edax-agent-design.md → agents/api_agent.py
- ``ApiAgent` tests` --references--> `ApiAgent`  [INFERRED]
  plan.md → agents/api_agent.py
- `Assumptions` --references--> `ApiAgent`  [INFERRED]
  plan.md → agents/api_agent.py

## Import Cycles
- None detected.

## Communities (113 total, 66 thin omitted)

### Community 0 - "ラジオボタン描画"
Cohesion: 0.16
Nodes (3): TestRadioButtonDraw, TestRadioButton, RadioButton

### Community 2 - "App メインループ"
Cohesion: 0.13
Nodes (3): App, TestAILogging, TestMainLoggingThrottle

### Community 3 - "README プロジェクト概要"
Cohesion: 0.05
Nodes (41): AI エージェント, AI 強さ検証テスト, AI 非同期実行の安全機構, AlphaZero 訓練, API サーバー, Docker を使わない実行（ローカル環境）, Docker を使用した実行（コンテナ環境）, Docker イメージのビルド (+33 more)

### Community 5 - "AlphaZero MCTS 探索"
Cohesion: 0.12
Nodes (5): MCTS, MCTSNode, _make_dummy_net(), TestMCTSPassPosition, TestPUCT

### Community 6 - "エージェント設定定義"
Cohesion: 0.09
Nodes (3): get_agent_params(), get_agent_definition(), TestConfigAgents

### Community 8 - "AI 思考世代管理テスト"
Cohesion: 0.09
Nodes (19): make_app(), test_app_has_ai_generation_attribute(), test_apply_ai_move_success_and_invalid(), test_fresh_ai_result_is_applied(), test_handle_ai_or_pass_respects_retry_backoff(), test_handle_click_in_game_calls_player_settings_click(), test_handle_click_in_game_undo(), test_handle_human_move_ignores_when_ai_thinking() (+11 more)

### Community 9 - "OthelloNNet と損失関数"
Cohesion: 0.09
Nodes (6): OthelloNNet, TestAlphaZeroLoss, TestCheckpoint, load_checkpoint(), save_best(), alphazero_loss()

### Community 10 - "ゲーム進行と自己対戦"
Cohesion: 0.18
Nodes (4): play_one_game(), play_self_play_game(), evaluate_against_agent(), _generate_opening_board()

### Community 12 - "API 設計プラン"
Cohesion: 0.12
Nodes (16): API Design, API tests, `ApiAgent` tests, Assumptions, CI / Postman, Current status, GUI / game flow tests, Next steps (+8 more)

### Community 13 - "Negamax 評価関数"
Cohesion: 0.15
Nodes (6): _disc_diff(), _evaluate(), _phase_coeffs(), _stable_edge_count(), _terminal_score(), TestEvaluation

### Community 14 - "パターン評価関数"
Cohesion: 0.06
Nodes (8): PatternEvaluator, main(), test_pattern_evaluator_evaluates_board(), test_pattern_evaluator_initializes(), test_pattern_evaluator_pattern_index(), TestPatternEvaluator, api_server_url(), _wait_for_port()

### Community 16 - "ビットボード教師エージェント"
Cohesion: 0.09
Nodes (11): TestBitboardPrimitives, TestBitboardTeacherAgent, apply_move_bitboard(), bitboards_to_board(), BitboardTeacherAgent, board_to_bitboards(), _build_edge_stable_table(), _build_masks() (+3 more)

### Community 17 - "MCTS ノード UCB1"
Cohesion: 0.12
Nodes (3): Node, DummyBoard, TestMCTSNode

### Community 18 - "多言語化 i18n"
Cohesion: 0.13
Nodes (16): _get_translator(), Translator, Localization (i18n) Implementation Plan, Task 1: Create `config/i18n.py`, Task 2: Update Translation Files, test_get_translator_lazy_initialization(), test_global_t_helper(), test_load_translations_invalid_format() (+8 more)

### Community 20 - "盤面ロジック Board"
Cohesion: 0.09
Nodes (3): Board, 2.2 内部探索: make/unmake 方式（deepcopy 排除）, TestBoard

### Community 23 - "ReversiNet ResNet モデル"
Cohesion: 0.07
Nodes (5): ResBlock, ReversiNet, TestAlphaZeroAgent, TestAlphaZeroAgentEndgameSolver, TestReversiNet

### Community 28 - "パターン学習とベンチマーク"
Cohesion: 0.19
Nodes (3): main(), make_opponent(), get_final_value()

### Community 30 - "サーバー README"
Cohesion: 0.18
Nodes (10): API ドキュメント, Reversi API (リバーシ API), インストール, エンドポイント, テスト, ライセンス, 使い方, 依存関係 (+2 more)

### Community 32 - "リプレイバッファ"
Cohesion: 0.12
Nodes (4): TestReplayBuffer, _normalize_board(), _normalize_pi(), ReplayBuffer

### Community 34 - "エージェント基底と Game"
Cohesion: 0.18
Nodes (7): Agent, FirstAgent, 2.1 クラスとファイル配置, Game, _create_game(), TestBaseAgent, TestFirstAgent

### Community 37 - "Negamax と強さ検証"
Cohesion: 0.08
Nodes (9): NegamaxAgent, 5. 強さの検証, _gui_opponent_agent_types(), play_one_game(), TestAlphaZeroMinimax80BeatsGuiAgents, TestAlphaZeroMinimax80VsTransposition, TestNegamaxBeatsGainAgent, TestNegamaxWithPatternEvaluator (+1 more)

### Community 38 - "PatternAgent 探索"
Cohesion: 0.09
Nodes (10): _SearchTimeout, PatternAgent, test_pattern_agent_evaluator_initialized(), test_pattern_agent_initializes(), test_pattern_agent_mocked_play(), test_play_does_not_mutate_game_board_on_timeout(), test_play_keeps_move_from_last_completed_depth(), test_play_respects_time_limit() (+2 more)

### Community 39 - "AlphaZero MCTS テスト"
Cohesion: 0.13
Nodes (5): node_terminal_value(), TestActionEncoding, TestMCTSDoesNotMutateInput, TestMCTSVisitCounts, TestNodeTerminalValue

### Community 40 - "Minimax 探索エージェント"
Cohesion: 0.07
Nodes (13): MinimaxAgent, _make_game(), TestMinimaxAgent, create_mock_agents(), mock_from_net(), mock_negamax_init(), mock_negamax_play(), TestEvaluateAgainstNegamax (+5 more)

### Community 41 - "Postman テストスクリプト"
Cohesion: 0.53
Nodes (4): run_newman(), run_postman_api_tests.sh script, start_server_if_needed(), wait_for_server()

### Community 42 - "ゲーム定数"
Cohesion: 0.40
Nodes (3): CellState, GameConstants, Player

### Community 43 - "サーバー再起動スクリプト"
Cohesion: 0.70
Nodes (4): restart_server.sh script, start_server(), stop_server(), wait_for_server()

### Community 44 - "CI ワークフロー"
Cohesion: 0.10
Nodes (23): jobs, lint-and-typecheck, tests, name, runs-on, steps, name, on (+15 more)

### Community 45 - "AlphaZero-Minimax 訓練スクリプト"
Cohesion: 0.10
Nodes (17): board_to_perspective_int8(), build_opponent_factory(), collect_dagger_games(), collect_selfplay_games(), _dagger_game_worker(), _evaluate_model(), evaluate_policy_top1(), HybridTrainConfig (+9 more)

### Community 48 - "アプリ起動とカバレッジ"
Cohesion: 0.14
Nodes (6): main(), main(), make_app_simple(), test_handle_ai_or_pass_ignores_when_ai_thinking(), test_run_ai_agent_puts_move_on_queue(), TestMainFunction

### Community 51 - "Edax 統合設計とエージェント選択"
Cohesion: 0.10
Nodes (7): 3.1 プロセス統合方式: 常駐 subprocess + ロック（採用）, 3.2 盤面の受け渡し, 3.3 クラス設計（2 ファイル分離でテスト容易性を確保）, 3.4 8x8 以外の盤面: 内部フォールバック（採用）, 3.5 設定と運用, 3. アーキテクチャ, _select_agent()

### Community 53 - "ハイブリッド訓練 CLI"
Cohesion: 0.12
Nodes (11): certification_passed(), collect_pretrain_samples(), DualLogger, is_better_eval(), main(), parse_args(), _run_stage0_baseline(), select_device() (+3 more)

### Community 66 - "AlphaZero 評価スクリプト"
Cohesion: 0.21
Nodes (3): build_opponent_factory(), evaluate_model_for_target(), main()

### Community 68 - "GUI テーマと UI 要素"
Cohesion: 0.34
Nodes (4): get_agent_options(), Color, Screen, Button

### Community 70 - "D4 データ拡張"
Cohesion: 0.20
Nodes (3): TestD4Augmentation, augment_batch_d4(), transform_board_and_policy()

### Community 71 - "置換表とキラームーブ"
Cohesion: 0.18
Nodes (3): TTEntry, TestKillerMoveHeuristic, TestTranspositionTable

### Community 75 - "プロジェクト構成概要"
Cohesion: 0.22
Nodes (9): AI エージェント, AlphaZero 訓練・評価モジュール, アプリケーション, サーバー, スクリプト, テストと CI, 主要ファイル, 学習済みデータ (+1 more)

### Community 76 - "Negamax 終盤パステスト"
Cohesion: 0.15
Nodes (4): _deterministic_agent(), _make_game(), TestEndgameAndPass, TestNegamaxAgentPlay

### Community 80 - "Negamax 実装計画"
Cohesion: 0.18
Nodes (10): NegamaxAgent 実装計画, Task 1: 位置重みテーブル `_build_weight_table`, Task 2: 探索プリミティブ（合法手・反転・make/unmake）, Task 3: 評価関数（フェーズ係数・確定石・終局スコア）, Task 4: NegamaxAgent 本体（反復深化・時間管理・パス処理）, Task 5: API サーバーへの登録, Task 6: 統合テストと conftest の環境変数, Task 7: GUI への登録 (+2 more)

### Community 81 - "Edax 統合設計書"
Cohesion: 0.18
Nodes (9): 1. 背景と動機, 2. エンジン選定, 4. テスト計画, 5. リスクと対策, 6. 変更ファイル一覧と実装順序, 7. 案 A（Negamax）との関係, 代替候補（参考）, 第一候補: Edax 4.x (abulmo/edax-reversi) (+1 more)

### Community 85 - "Edax 実装計画"
Cohesion: 0.20
Nodes (9): EdaxAgent（外部エンジン統合）実装計画, Task 1: 盤面変換の純粋関数, Task 2: EdaxEngine プロセス管理クラス, Task 3: 共有エンジンシングルトンと EdaxAgent, Task 4: API サーバーへの登録と 503 ハンドリング, Task 5: GUI への登録, Task 6: 導入スクリプト setup_edax.sh, Task 7: 実バイナリ統合テスト（skipif 付き） (+1 more)

### Community 89 - "探索プリミティブテスト"
Cohesion: 0.15
Nodes (5): _flips_for_move(), _initial_board(), TestSearchPrimitives, TestTimeManagement, flaky()

### Community 90 - "オンボーディングガイド"
Cohesion: 0.22
Nodes (8): Codebases, Get Started, How We Use Claude, MCP Servers to Activate, Skills to Know About, Team Tips, Welcome to Reversi AI Development, Your Setup Checklist

### Community 91 - "Newman API テスト設定"
Cohesion: 0.25
Nodes (8): newman, devDependencies, newman@^5.3.0, name, private, scripts, newman:run, version

### Community 92 - "Negamax 仕様"
Cohesion: 0.29
Nodes (6): 2.3 評価関数, 2.4 可変盤面サイズ (4-16) 対応: 重みテーブルのサイズ非依存生成, 2.5 探索と時間管理, 2.6 パス処理, 2.7 決定論, 2. 仕様

### Community 93 - "API エンドポイント実装"
Cohesion: 0.17
Nodes (8): `agents/api_agent.py`, `config/agents_config.py`, Implementation Changes, `main.py`, `server/api_server.py`, State / Concurrency Policy, play(), PlayRequest

### Community 94 - "Negamax 設計書"
Cohesion: 0.25
Nodes (8): 1. 背景と動機, 3. 変更ファイル一覧（実装フェーズ用）, 4. テスト計画（カバレッジ 100% 目標）, 6. 実装順序, 7. リスクと対策, 8. 案 B（外部エンジン）との関係, 現 MCTS との比較, 設計書: Negamax エージェント（案 A — 純 Python・依存ゼロの強い API プレイヤー）

## Knowledge Gaps
- **1 isolated node(s):** `reversi-py`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 752 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **66 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Game` connect `エージェント基底と Game` to `GUI 描画メソッド`, `App メインループ`, `App 状態更新テスト`, `AI 思考世代管理テスト`, `ゲーム進行と自己対戦`, `MCTS エージェント`, `パターン評価関数`, `ビットボード教師エージェント`, `盤面ロジック Board`, `GainAgent`, `ReversiNet ResNet モデル`, `RandomAgent`, `GameGUI レイアウトテスト`, `パターン学習とベンチマーク`, `AlphaZeroAgent`, `AI エージェントモジュール群`, `Negamax と強さ検証`, `PatternAgent 探索`, `Minimax 探索エージェント`, `AlphaZero-Minimax 訓練スクリプト`, `アプリ起動とカバレッジ`, `エージェント生成`, `App クリック処理と設定`, `AlphaZero 評価スクリプト`, `GUI テーマと UI 要素`, `置換表エージェント基本テスト`, `置換表とキラームーブ`, `AlphaZero 着手と make/unmake`, `履歴リプレイ`, `時間制限テスト`, `置換表エージェント初期化テスト`?**
  _High betweenness centrality (0.311) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `Game` (e.g. with `MinimaxAgent` and `2.1 クラスとファイル配置`) actually correct?**
  _`Game` has 26 INFERRED edges - model-reasoned connections that need verification._
- **What connects `reversi-py` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `App メインループ` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._
- **Why does `TestGameGUI` connect `GameGUI レイアウトテスト` to `GUI 描画メソッド`, `エージェント基底と Game`, `盤面描画`, `GUI テーマと UI 要素`, `App クリック処理と設定`, `プレイヤー設定スクロール`, `GameGUI 寸法計算`, `盤面座標とクリック判定`, `フォント読み込みとアニメーション`, `メッセージ位置計算`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `GameGUI` (e.g. with `Color` and `Screen`) actually correct?**
  _`GameGUI` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Should `README プロジェクト概要` be split into smaller, more focused modules?**
  _Cohesion score 0.047619047619047616 - nodes in this community are weakly interconnected._
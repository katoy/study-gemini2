# Graph Report - reversi-py  (2026-11-24)

## Corpus Check
- 144 files · ~142,392 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: (none) 6, .ttf 2, .pth 1)

## Summary
- 1906 nodes · 4508 edges · 124 communities (63 shown, 61 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 761 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `321d7d2e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ラジオボタン描画
- GUI 描画メソッド
- App
- Reversi (リバーシ) - Python / Pygame
- App 状態更新テスト
- test_alphazero_mcts.py
- test_agents.py
- 置換表 Negamax エージェント
- AI 思考世代管理テスト
- OthelloNNet と損失関数
- .get_valid_moves
- TestMonteCarloTreeSearchAgent
- API 設計プラン
- GameGUI
- パターン評価関数
- αβ 探索コア
- ビットボード教師エージェント
- MCTS ノード UCB1
- 多言語化 i18n
- TestApiAgentIntegration
- 盤面ロジック Board
- API サーバーテスト
- GainAgent
- ReversiNet ResNet モデル
- TestGameGUI
- explanation.py
- test_analysis_validity.py
- analyze_game
- test_main_analysis.py
- サーバー README
- AlphaZeroAgent
- リプレイバッファ
- AI エージェントモジュール群
- エージェント基底と Game
- 位置重みテーブル
- play_one_game
- PatternAgent 探索
- skipif
- Minimax 探索エージェント
- Postman テストスクリプト
- ゲーム定数
- サーバー再起動スクリプト
- CI ワークフロー
- AlphaZero-Minimax 訓練スクリプト
- サーバー付き起動スクリプト
- サーバー停止スクリプト
- main.py
- ._calculate_button_height
- MCTS
- Edax 統合設計とエージェント選択
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
- EvalResult
- bitboard_teacher.py
- game_analyzer.py
- Zobrist ハッシュ
- gui.py
- テストと CI
- D4 データ拡張
- 置換表とキラームーブ
- TestNegamaxBeatsGainAgent
- アーキテクチャ
- プロジェクト構成概要
- test_negamax_agent.py
- Button テスト
- Label と UI 部品
- Docker での実行
- Negamax 実装計画
- Edax 統合設計書
- 置換表エージェント初期化テスト
- MonteCarloTreeSearchAgent
- パス盤面スタブ
- Edax 実装計画
- node_terminal_value
- 実行方法と使い方
- NegamaxAgent
- オンボーディングガイド
- Newman API テスト設定
- Negamax 仕様
- API エンドポイント実装
- Negamax 設計書
- TestAILogging
- API サーバー
- startpoint.sh
- TestMCTSDoesNotMutateInput
- サーバーエンドポイントテスト
- GUI 高さ調整テスト
- test_main_more.py
- GUI 幅テスト
- reversi-pyプロジェクトルート

## God Nodes (most connected - your core abstractions)
1. `Game` - 156 edges
2. `GameGUI` - 99 edges
3. `NegamaxAgent` - 59 edges
4. `Board` - 59 edges
5. `App` - 57 edges
6. `TestGameGUI` - 54 edges
7. `TranspositionNegamaxAgent` - 52 edges
8. `Agent` - 44 edges
9. `OthelloNNet` - 44 edges
10. `ApiAgent` - 39 edges

## Surprising Connections (you probably didn't know these)
- `動作環境` --references--> `AlphaZeroAgent`  [INFERRED]
  README.md → agents/alpha_zero_agent.py
- ``ApiAgent` tests` --references--> `ApiAgent`  [INFERRED]
  plan.md → agents/api_agent.py
- `Assumptions` --references--> `ApiAgent`  [INFERRED]
  plan.md → agents/api_agent.py
- ``config/agents_config.py`` --references--> `ApiAgent`  [INFERRED]
  plan.md → agents/api_agent.py
- `統合テスト` --references--> `ApiAgent`  [INFERRED]
  README.md → agents/api_agent.py

## Import Cycles
- None detected.

## Communities (124 total, 61 thin omitted)

### Community 0 - "ラジオボタン描画"
Cohesion: 0.26
Nodes (3): TestRadioButtonDraw, TestRadioButton, RadioButton

### Community 2 - "App"
Cohesion: 0.07
Nodes (3): App, main(), TestMainLoggingThrottle

### Community 3 - "Reversi (リバーシ) - Python / Pygame"
Cohesion: 0.25
Nodes (7): Reversi (リバーシ) - Python / Pygame, インストール, ライセンス, 動作環境, 動作環境とインストール, 概要, 目次

### Community 5 - "test_alphazero_mcts.py"
Cohesion: 0.19
Nodes (4): MCTSNode, _make_dummy_net(), TestMCTSPassPosition, TestPUCT

### Community 6 - "test_agents.py"
Cohesion: 0.06
Nodes (5): get_agent_params(), get_agent_class(), get_agent_definition(), get_agent_options(), TestConfigAgents

### Community 7 - "置換表 Negamax エージェント"
Cohesion: 0.13
Nodes (3): _SearchTimeout, TranspositionNegamaxAgent, TestTranspositionNegamaxAgentBasic

### Community 8 - "AI 思考世代管理テスト"
Cohesion: 0.09
Nodes (19): make_app(), test_app_has_ai_generation_attribute(), test_apply_ai_move_success_and_invalid(), test_fresh_ai_result_is_applied(), test_handle_ai_or_pass_respects_retry_backoff(), test_handle_click_in_game_calls_player_settings_click(), test_handle_click_in_game_undo(), test_handle_human_move_ignores_when_ai_thinking() (+11 more)

### Community 9 - "OthelloNNet と損失関数"
Cohesion: 0.07
Nodes (9): board_to_tensor(), OthelloNNet, evaluate_model_for_target(), main(), TestAlphaZeroLoss, TestCheckpoint, load_checkpoint(), save_best() (+1 more)

### Community 10 - ".get_valid_moves"
Cohesion: 0.08
Nodes (14): play_one_game(), main(), play_self_play_game(), _random_position(), _playout_from(), test_explicit_win_draw_loss_branch_patterns(), find_corner_gift_game(), _play_scripted_game() (+6 more)

### Community 12 - "API 設計プラン"
Cohesion: 0.12
Nodes (16): API Design, API tests, `ApiAgent` tests, Assumptions, CI / Postman, Current status, GUI / game flow tests, Next steps (+8 more)

### Community 14 - "パターン評価関数"
Cohesion: 0.07
Nodes (7): PatternEvaluator, test_pattern_evaluator_evaluates_board(), test_pattern_evaluator_initializes(), test_pattern_evaluator_pattern_index(), TestPatternEvaluator, api_server_url(), _wait_for_port()

### Community 15 - "αβ 探索コア"
Cohesion: 0.14
Nodes (4): _apply(), _flips_for_move(), _undo(), _valid_moves()

### Community 16 - "ビットボード教師エージェント"
Cohesion: 0.17
Nodes (5): _evaluate_after_move(), TestBitboardTeacherAgent, apply_move_bitboard(), BitboardTeacherAgent, legal_moves_mask()

### Community 17 - "MCTS ノード UCB1"
Cohesion: 0.12
Nodes (3): Node, DummyBoard, TestMCTSNode

### Community 18 - "多言語化 i18n"
Cohesion: 0.13
Nodes (16): _get_translator(), Translator, Localization (i18n) Implementation Plan, Task 1: Create `config/i18n.py`, Task 2: Update Translation Files, test_get_translator_lazy_initialization(), test_global_t_helper(), test_load_translations_invalid_format() (+8 more)

### Community 20 - "盤面ロジック Board"
Cohesion: 0.10
Nodes (4): Board, 2.2 内部探索: make/unmake 方式（deepcopy 排除）, test_real_game_invariants_across_all_analyzed_moves(), TestBoard

### Community 22 - "GainAgent"
Cohesion: 0.11
Nodes (4): GainAgent, make_opponent(), TestGainAgent, TestNegamaxWithPatternEvaluator

### Community 23 - "ReversiNet ResNet モデル"
Cohesion: 0.14
Nodes (3): ResBlock, ReversiNet, TestReversiNet

### Community 25 - "explanation.py"
Cohesion: 0.15
Nodes (17): build_headline(), build_move_explanation(), coord_to_label(), detect_reason_codes(), format_pv(), _is_edge_non_c(), _outcome_tag_label(), _post_move_stats() (+9 more)

### Community 26 - "test_analysis_validity.py"
Cohesion: 0.11
Nodes (8): RandomAgent, get_final_value(), TestRandomAgent, _play_game_with_agents(), test_counterfactual_endgame_best_move_wins_played_move_loses(), test_endgame_12_empties_exact_solve_default(), test_no_false_positive_decisive_and_garbage_time_ranking(), test_tactical_scenarios_golden()

### Community 28 - "analyze_game"
Cohesion: 0.13
Nodes (11): analyze_game(), _EvalGame, _extract_pv(), _initial_board(), test_analyze_game_all_winners_and_fallback_worst(), test_analyze_game_edge_cases(), test_analyze_game_finds_decisive_endgame_blunder_and_progress(), test_eval_game_valid_moves_cache() (+3 more)

### Community 29 - "test_main_analysis.py"
Cohesion: 0.24
Nodes (11): GameAnalysis, MoveAnalysis, 終局後解析（`analysis/`）, _empty_board(), _make_app_with_real_game(), _make_sample_analysis(), test_analysis_navigation_pv_keys_scroll_and_render(), test_invalidate_analysis_drains_queue_and_resets_on_restart_reset() (+3 more)

### Community 30 - "サーバー README"
Cohesion: 0.18
Nodes (10): API ドキュメント, Reversi API (リバーシ API), インストール, エンドポイント, テスト, ライセンス, 使い方, 依存関係 (+2 more)

### Community 31 - "AlphaZeroAgent"
Cohesion: 0.12
Nodes (4): AlphaZeroAgent, TestAlphaZeroAgent, TestAlphaZeroAgentEndgameSolver, TestAlphaZeroAgent

### Community 32 - "リプレイバッファ"
Cohesion: 0.12
Nodes (4): TestReplayBuffer, _normalize_board(), _normalize_pi(), ReplayBuffer

### Community 34 - "エージェント基底と Game"
Cohesion: 0.18
Nodes (7): Agent, FirstAgent, 2.1 クラスとファイル配置, Game, _create_game(), TestBaseAgent, TestFirstAgent

### Community 37 - "play_one_game"
Cohesion: 0.10
Nodes (5): play_one_game(), TestAlphaZeroMinimax80BeatsGuiAgents, TestAlphaZeroMinimax80VsTransposition, TestTranspositionBeatsNegamax, TestTranspositionBeatsPattern

### Community 38 - "PatternAgent 探索"
Cohesion: 0.12
Nodes (9): _SearchTimeout, PatternAgent, test_pattern_agent_evaluator_initialized(), test_pattern_agent_initializes(), test_pattern_agent_mocked_play(), test_play_does_not_mutate_game_board_on_timeout(), test_play_keeps_move_from_last_completed_depth(), test_play_respects_time_limit() (+1 more)

### Community 39 - "skipif"
Cohesion: 0.18
Nodes (3): TestActionEncoding, TestMakeUnmake, TestMCTSVisitCounts

### Community 40 - "Minimax 探索エージェント"
Cohesion: 0.10
Nodes (10): create_mock_agents(), mock_from_net(), mock_negamax_init(), mock_negamax_play(), TestEvaluateAgainstNegamax, mock_from_net(), play(), mock_negamax_play() (+2 more)

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
Cohesion: 0.08
Nodes (17): board_to_perspective_int8(), build_opponent_factory(), collect_dagger_games(), collect_selfplay_games(), _dagger_game_worker(), HybridTrainConfig, _initial_board(), make_smoothed_policy() (+9 more)

### Community 51 - "Edax 統合設計とエージェント選択"
Cohesion: 0.12
Nodes (7): Task 4: API サーバーへの登録と 503 ハンドリング, 3.2 盤面の受け渡し, 3.3 クラス設計（2 ファイル分離でテスト容易性を確保）, 3.4 8x8 以外の盤面: 内部フォールバック（採用）, 3.5 設定と運用, 3. アーキテクチャ, _select_agent()

### Community 53 - "ハイブリッド訓練 CLI"
Cohesion: 0.18
Nodes (7): collect_pretrain_samples(), DualLogger, evaluate_policy_top1(), main(), select_device(), train_on_buffer(), _train_step_with_fallback()

### Community 62 - "ApiAgent 初期化"
Cohesion: 0.10
Nodes (3): ApiAgent, 3.1 プロセス統合方式: 常駐 subprocess + ロック（採用）, TestApiAgent

### Community 63 - "ログ抑制フィルタ"
Cohesion: 0.16
Nodes (3): test_play_respects_time_limit_on_real_positions(), TestThrottlingFilter, ThrottlingFilter

### Community 64 - "EvalResult"
Cohesion: 0.11
Nodes (8): certification_passed(), _evaluate_model(), _format_eval(), is_better_eval(), parse_args(), _run_stage0_baseline(), should_trigger_certification(), EvalResult

### Community 65 - "bitboard_teacher.py"
Cohesion: 0.17
Nodes (5): TestBitboardPrimitives, _build_edge_stable_table(), _build_masks(), _edge_stability_score(), evaluate_bitboard()

### Community 66 - "game_analyzer.py"
Cohesion: 0.20
Nodes (3): _EvalBoard, _win_prob(), bitboards_to_board()

### Community 68 - "gui.py"
Cohesion: 0.34
Nodes (3): Color, Screen, TestPlayerBadgeRendering

### Community 69 - "テストと CI"
Cohesion: 0.25
Nodes (8): AI 強さ検証テスト, Tier 1: 強さテスト（CI 組み込み、8x8 盤面）, Tier 2: 詳細ベンチマーク（ローカル検証）, サーバー単体テスト, テストと CI, ローカル CI チェック, 単体テスト（通常実行）, 統合テスト

### Community 70 - "D4 データ拡張"
Cohesion: 0.19
Nodes (3): TestD4Augmentation, augment_batch_d4(), transform_board_and_policy()

### Community 71 - "置換表とキラームーブ"
Cohesion: 0.18
Nodes (3): TTEntry, TestKillerMoveHeuristic, TestTranspositionTable

### Community 74 - "アーキテクチャ"
Cohesion: 0.29
Nodes (7): AI 非同期実行の安全機構, アーキテクチャ, クラス責務の分離, ゲーム進行シーケンス, コード構成の工夫, 将来の最適化, 構成図

### Community 75 - "プロジェクト構成概要"
Cohesion: 0.20
Nodes (10): AI エージェント, AlphaZero 訓練・評価モジュール, アプリケーション, サーバー, スクリプト, テストと CI, ドキュメント・その他, 主要ファイル (+2 more)

### Community 76 - "test_negamax_agent.py"
Cohesion: 0.07
Nodes (12): _disc_diff(), _evaluate(), _phase_coeffs(), _stable_edge_count(), _terminal_score(), _deterministic_agent(), _initial_board(), _make_game() (+4 more)

### Community 79 - "Docker での実行"
Cohesion: 0.29
Nodes (7): Docker での実行, VNC での GUI 接続, コンテナの停止・削除, トラブルシューティング, 手動でビルド・起動する場合, 環境変数, 起動（推奨: スクリプト）

### Community 80 - "Negamax 実装計画"
Cohesion: 0.18
Nodes (10): NegamaxAgent 実装計画, Task 1: 位置重みテーブル `_build_weight_table`, Task 2: 探索プリミティブ（合法手・反転・make/unmake）, Task 3: 評価関数（フェーズ係数・確定石・終局スコア）, Task 4: NegamaxAgent 本体（反復深化・時間管理・パス処理）, Task 5: API サーバーへの登録, Task 6: 統合テストと conftest の環境変数, Task 7: GUI への登録 (+2 more)

### Community 81 - "Edax 統合設計書"
Cohesion: 0.22
Nodes (9): 1. 背景と動機, 2. エンジン選定, 4. テスト計画, 5. リスクと対策, 6. 変更ファイル一覧と実装順序, 7. 案 A（Negamax）との関係, 代替候補（参考）, 第一候補: Edax 4.x (abulmo/edax-reversi) (+1 more)

### Community 85 - "Edax 実装計画"
Cohesion: 0.22
Nodes (8): EdaxAgent（外部エンジン統合）実装計画, Task 1: 盤面変換の純粋関数, Task 2: EdaxEngine プロセス管理クラス, Task 3: 共有エンジンシングルトンと EdaxAgent, Task 5: GUI への登録, Task 6: 導入スクリプト setup_edax.sh, Task 7: 実バイナリ統合テスト（skipif 付き）, Task 8: Docker・ドキュメント・全体検証

### Community 87 - "実行方法と使い方"
Cohesion: 0.33
Nodes (6): クイックスタート, ゲームの遊び方, ローカル環境での実行, 実行方法と使い方, 方法 1: アプリのみを起動（シンプル）, 方法 2: API サーバーとアプリを一緒に起動（AI エージェント使用）

### Community 89 - "NegamaxAgent"
Cohesion: 0.09
Nodes (14): MinimaxAgent, NegamaxAgent, 5. 強さの検証, AI エージェント, AlphaZero の訓練と評価, GUI での使用と注記, 対 Minimax 勝率 80% 超ハイブリッド訓練（純粋 NN + MCTS）, 評価結果 (+6 more)

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
Cohesion: 0.20
Nodes (8): 1. 背景と動機, 3. 変更ファイル一覧（実装フェーズ用）, 4. テスト計画（カバレッジ 100% 目標）, 6. 実装順序, 7. リスクと対策, 8. 案 B（外部エンジン）との関係, 現 MCTS との比較, 設計書: Negamax エージェント（案 A — 純 Python・依存ゼロの強い API プレイヤー）

### Community 98 - "API サーバー"
Cohesion: 0.50
Nodes (4): API サーバー, API ドキュメントとエンドポイント, POST /play のリクエスト仕様, 環境変数

### Community 99 - "startpoint.sh"
Cohesion: 0.67
Nodes (3): startpoint.sh script, USER, wait_until()

### Community 103 - "test_main_more.py"
Cohesion: 0.83
Nodes (3): make_app_simple(), test_handle_ai_or_pass_ignores_when_ai_thinking(), test_run_ai_agent_puts_move_on_queue()

## Knowledge Gaps
- **2 isolated node(s):** `reversi-py`, `USER`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 816 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **61 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Game` connect `エージェント基底と Game` to `GUI 描画メソッド`, `App`, `App 状態更新テスト`, `test_agents.py`, `置換表 Negamax エージェント`, `AI 思考世代管理テスト`, `.get_valid_moves`, `TestMonteCarloTreeSearchAgent`, `ビットボード教師エージェント`, `盤面ロジック Board`, `GainAgent`, `ReversiNet ResNet モデル`, `TestGameGUI`, `test_analysis_validity.py`, `analyze_game`, `test_main_analysis.py`, `AlphaZeroAgent`, `AI エージェントモジュール群`, `ApiAgent 通信テスト`, `play_one_game`, `PatternAgent 探索`, `AlphaZero-Minimax 訓練スクリプト`, `main.py`, `bitboard_teacher.py`, `gui.py`, `置換表とキラームーブ`, `置換表エージェント初期化テスト`, `MonteCarloTreeSearchAgent`, `NegamaxAgent`, `TestAILogging`, `test_main_more.py`?**
  _High betweenness centrality (0.304) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `Game` (e.g. with `MinimaxAgent` and `2.1 クラスとファイル配置`) actually correct?**
  _`Game` has 26 INFERRED edges - model-reasoned connections that need verification._
- **What connects `reversi-py`, `USER` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `App` be split into smaller, more focused modules?**
  _Cohesion score 0.07077922077922078 - nodes in this community are weakly interconnected._
- **Why does `GameGUI` connect `GameGUI` to `ラジオボタン描画`, `GUI 描画メソッド`, `App`, `gui.py`, `App 状態更新テスト`, `test_main_more.py`, `プレイヤー設定スクロール`, `AI 思考世代管理テスト`, `プロジェクト構成概要`, `Button テスト`, `Label と UI 部品`, `main.py`, `._calculate_button_height`, `test_main_analysis.py`, `._calculate_board_rect`, `TestGameGUI`, `._calculate_player_settings_height`, `メッセージ位置計算`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `GameGUI` (e.g. with `Color` and `Screen`) actually correct?**
  _`GameGUI` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Should `App 状態更新テスト` be split into smaller, more focused modules?**
  _Cohesion score 0.045454545454545456 - nodes in this community are weakly interconnected._
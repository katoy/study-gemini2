# main.py
import copy
import pygame
import sys
import logging
from typing import Any, Optional
from utils.logging_utils import ThrottlingFilter
import threading
import queue
from analysis.game_analyzer import _initial_board, analyze_game, solve_position_disc_diff
from analysis.models import GameAnalysis, MoveAnalysis
from board import Board
from game import Game
from gui import GameGUI
from config.i18n import _t
from config.theme import Screen
# For resolving agent display names in logs
from config.agents_config import get_agent_definition

# AI が手を返せなかった場合（API 障害など）に再試行するまでの待機時間（ミリ秒）
AI_RETRY_DELAY_MS = 1000

class App:
    """リバーシゲームアプリケーション。メインループとゲーム制御を担当。

    責務：
    1. メインループ：イベント処理 → ゲーム更新 → 描画
    2. ゲーム状態管理：プレイヤー設定、ゲーム開始/終了
    3. AI 実行管理：スレッド管理、AI 出力キュー、世代 ID で古い出力を破棄
    4. UI イベント処理：ボタン・ラジオボタン・盤面クリックの処理

    設計上の注記：
    - 単一責務原則（SRP）に向けて、将来的に以下の分離を検討：
      * GameController: ゲーム状態管理専用
      * AIManager: AI 実行スレッド・キュー・世代管理専用
      * App: メインループのみ
    - 現在は実装の簡潔性とテスト容易性のため単一クラス

    属性：
        game (Game): ゲームロジック
        gui (GameGUI): UI 描画
        black_player_id, white_player_id: プレイヤー設定
        game_started: ゲーム開始フラグ
        ai_thread, ai_queue: AI 非同期実行
        _ai_generation: 古い AI 出力を破棄するための世代 ID
    """
    def __init__(self, game: Game, gui: GameGUI):
        """Appクラスのコンストラクタ。

        Args:
            game (Game): ゲームロジックを管理するGameインスタンス。
            gui (GameGUI): GUI描画を管理するGameGUIインスタンス。
        """
        self.game = game
        self.gui = gui
        self.clock = pygame.time.Clock()

        # --- プレイヤー設定 ---
        # デフォルトは両プレイヤーとも人間 (ID=0)
        self.black_player_id = 0
        self.white_player_id = 0
        # Gameインスタンスに初期プレイヤー設定を適用
        self.game.set_players(self.black_player_id, self.white_player_id)

        # --- ゲーム状態 ---
        self.game_started = False # ゲームが開始されているか
        self.running = True       # メインループが実行中か

        # --- AI非同期処理用 ---
        self.ai_thread = None
        self.ai_queue: queue.Queue = queue.Queue()
        self.is_ai_thinking = False
        self._ai_generation: int = 0
        # AI が手を返せなかった場合の再試行抑制（この時刻まで再起動しない）
        self._ai_retry_not_before: int = 0

        # --- 終局後解説モード用 ---
        self.is_analyzing: bool = False
        self.analysis_progress: tuple[int, int] = (0, 0)
        self.analysis_result: Optional[GameAnalysis] = None
        self.analysis_mode: bool = False
        self.analysis_move_index: int = 0
        self.analysis_pv_step: int = 0
        self.analysis_thread: Optional[threading.Thread] = None
        self.analysis_queue: queue.Queue[tuple[str, Any, int]] = queue.Queue()
        self._analysis_generation: int = 0
        self.resume_pending: bool = False
        # 打ち直し準備中に盤面上へ表示する補足（人間への切り替え・推奨手・勝敗確定など）
        self.resume_notices: list[str] = []
        # 打ち直しの 1 手だけ人間が打つ側（画面のプレイヤー設定は変えない。None なら無し）
        self._resume_human_override: Optional[int] = None

    def run(self):
        """
        ゲームのメインループを実行する。
        イベント処理、状態更新、描画を繰り返す。
        """
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        # Attach throttling filter to reduce repeated identical log messages
        try:
            root_logger = logging.getLogger()
            root_logger.addFilter(ThrottlingFilter(interval_seconds=0.5))
        except Exception:
            # if filter cannot be attached for any reason, continue without failing
            pass
        logging.info("Starting Reversi game...") # pragma: no cover

        while self.running: # pragma: no cover
            self.clock.tick(60) # pragma: no cover

            # 1. イベント処理
            mouse_click_pos = self._handle_events() # pragma: no cover

            # 2. 状態更新
            #    - マウスクリックに基づく更新 (ボタンクリック、セルクリック)
            #    - AIの手番、パス処理
            self._update_state(mouse_click_pos) # pragma: no cover

            # 3. 描画処理
            self._render() # pragma: no cover

        # --- ループ終了後の後処理 ---
        logging.info("Exiting Reversi game.") # pragma: no cover
        pygame.quit() # pragma: no cover
        sys.exit() # pragma: no cover

    # === イベント処理 ===

    def _handle_events(self) -> tuple[int, int] | None:
        """
        Pygameのイベントを処理する。
        QUITイベントで実行フラグをFalseにし、左マウスクリック位置を返す。

        Returns:
            tuple[int, int] | None: 左クリックがあった場合はその座標、なければ None。
        """
        mouse_click_pos = None
        # 同一フレームに QUIT とクリックが混在しても取りこぼさないよう、
        # 途中で return せずキュー内の全イベントを処理する
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 左クリック (ボタン番号 1) のみ処理（最初のクリックを採用）
                if event.button == 1 and mouse_click_pos is None:
                    mouse_click_pos = event.pos
                elif event.button in (4, 5):
                    self._handle_player_settings_scroll(1 if event.button == 5 else -1)
            elif event.type == pygame.MOUSEWHEEL:
                self._handle_player_settings_scroll(-event.y)
            elif event.type == pygame.KEYDOWN:
                if self.analysis_mode and self.game_started and self.game.game_over:
                    self._handle_analysis_key(event.key)
        return mouse_click_pos

    def _handle_player_settings_scroll(self, wheel_delta: int) -> None:
        """プレイヤー設定（または解説パネル）のホイールスクロールを処理する"""
        if wheel_delta == 0:
            return

        player_settings_top = self.gui._calculate_player_settings_top()
        mouse_pos = pygame.mouse.get_pos()
        scroll_delta = wheel_delta * Screen.PLAYER_SETTINGS_SCROLL_STEP
        if self.analysis_mode and self.game_started and self.game.game_over:
            if self.gui.is_analysis_panel_point(mouse_pos, player_settings_top):
                self.gui.scroll_analysis_panel(scroll_delta, player_settings_top)
            return
        if not self.gui.is_player_settings_point(mouse_pos, player_settings_top):
            return

        self.gui.scroll_player_settings(scroll_delta, player_settings_top)

    # === 状態管理 ===

    def _invalidate_ai_thinking(self) -> None:
        """AI 思考結果を無効化する。プレイヤー設定変更時に呼ぶ。"""
        self._ai_generation += 1
        self.is_ai_thinking = False
        while not self.ai_queue.empty():
            self.ai_queue.get_nowait()

    def _update_state(self, mouse_click_pos: tuple[int, int] | None):
        """
        ゲームの状態を更新する。
        マウスクリックイベントや、現在のゲーム状況 (AIの手番、パス) に基づいて処理を行う。

        Args:
            mouse_click_pos: マウスのクリック位置 (クリックがなければ None)。
        """
        self._poll_analysis_queue()

        # --- AIの思考結果をチェック ---
        if self.is_ai_thinking:
            try:
                while True:
                    move, gen = self.ai_queue.get_nowait()
                    if gen == self._ai_generation:
                        # 現行世代の結果のみ適用。古い世代の結果で
                        # is_ai_thinking を解除すると同一世代のスレッドが
                        # 二重起動するため、世代一致時だけ解除する
                        self.is_ai_thinking = False
                        self._apply_ai_move(move)
                        break
                    # 古い世代の結果は破棄して次のエントリを確認
            except queue.Empty:
                pass  # まだ考え中

        # === クリック処理のディスパッチ ===
        if mouse_click_pos:
            if not self.game_started:
                # ゲーム開始前のクリック処理 (スタートボタン、プレイヤー選択)
                self._handle_click_before_start(mouse_click_pos)
            elif self.game.game_over:
                # ゲームオーバー時のクリック処理 (リスタート、リセット、終了)
                self._handle_click_game_over(mouse_click_pos)
            elif self.resume_pending:
                self._handle_click_resume_pending(mouse_click_pos)
            else:  # ゲーム中
                # ゲーム中のクリック処理 (リスタート、リセット、終了、盤面クリック)
                self._handle_click_in_game(mouse_click_pos)

        # === AI・パス処理 ===
        # ゲームが開始していて、かつゲームオーバーでない場合にのみ処理
        if self.game_started and not self.game.game_over and not self.resume_pending:
            self._handle_ai_or_pass()

    def _handle_click_before_start(self, mouse_click_pos: tuple[int, int]):
        """ゲーム開始前のクリック処理"""
        # --- 修正: gui の is_start_button_clicked を呼び出す ---
        if self.gui.is_start_button_clicked(mouse_click_pos):
        # ----------------------------------------------------
            self.game_started = True
            self.game.set_message("") # 開始時にメッセージをクリア
            logging.info("Game started.") # pragma: no cover
        else:
            self._handle_player_settings_click(mouse_click_pos)

    def _handle_click_game_over(self, mouse_click_pos: tuple[int, int]):
        """ゲームオーバー時のクリック処理"""
        if self.analysis_mode and self.analysis_result is not None:
            self._handle_analysis_click(mouse_click_pos)
            return

        # --- 修正: gui の is_*_button_clicked を呼び出す ---
        if self.gui.is_restart_button_clicked(mouse_click_pos, game_over=True):
            self._invalidate_ai_thinking() # 思考中の古い AI 結果を無効化
            self._invalidate_analysis()
            self.game.reset()
            self._resume_human_override = None  # 打ち直しの一時的な人間化を解除
            # 現在のプレイヤー設定を引き継いでリセット
            self.game.set_players(self.black_player_id, self.white_player_id)
            self.game_started = True # ゲーム開始状態にする
            logging.info("Game restarted.") # pragma: no cover
        elif self.gui.is_reset_button_clicked(mouse_click_pos, game_over=True):
            self._invalidate_ai_thinking() # 思考中の古い AI 結果を無効化
            self._invalidate_analysis()
            self.game.reset()
            self._resume_human_override = None  # 打ち直しの一時的な人間化を解除
            # プレイヤー設定も初期化 (両者人間)
            self.black_player_id = 0
            self.white_player_id = 0
            self.game.set_players(self.black_player_id, self.white_player_id)
            self.game_started = False # ゲーム開始前の状態に戻す
            logging.info("Game reset to initial state.") # pragma: no cover
        elif self.gui.is_quit_button_clicked(mouse_click_pos, game_over=True):
            self.running = False # メインループを終了
        elif self.gui.is_analyze_button_clicked(mouse_click_pos, game_over=True) is True:
            if not self.is_analyzing:
                self._start_analysis()
        else:
            self._handle_player_settings_click(mouse_click_pos)
        # else: pragma: no cover
        #     pass # pragma: no cover
        # ----------------------------------------------------

    def _handle_player_settings_click(self, mouse_click_pos: tuple[int, int]):
        """プレイヤー設定ラジオボタンのクリック処理"""
        player_settings_top = self.gui._calculate_player_settings_top()
        clicked_player, clicked_agent_id = self.gui.get_clicked_radio_button(
            mouse_click_pos, player_settings_top
        )
        if clicked_player is None:
            return

        player_changed = False
        if clicked_player == -1 and self.black_player_id != clicked_agent_id:
            self.black_player_id = clicked_agent_id
            player_changed = True
        elif clicked_player == 1 and self.white_player_id != clicked_agent_id:
            self.white_player_id = clicked_agent_id
            player_changed = True

        if player_changed:
            self.game.set_players(self.black_player_id, self.white_player_id)
            if self._resume_human_override is not None:
                if clicked_player == self._resume_human_override:
                    # 打ち直しの 1 手を担当する側を選び直した場合は、その選択を優先する
                    self._resume_human_override = None
                else:
                    self.game.agents[self._resume_human_override] = None
            if self.game_started and not self.game.game_over:
                self._invalidate_ai_thinking()
            logging.info(
                f"Player settings changed: Black={self.black_player_id}, White={self.white_player_id}"
            ) # pragma: no cover

    def _handle_click_in_game(self, mouse_click_pos: tuple[int, int]):
        """ゲーム中のクリック処理"""
        # --- 修正: gui の is_*_button_clicked を呼び出す ---
        if self.gui.is_restart_button_clicked(mouse_click_pos, game_over=False):
            self._invalidate_ai_thinking() # 思考中の古い AI 結果を無効化
            self.game.reset()
            self._resume_human_override = None  # 打ち直しの一時的な人間化を解除
            self.game.set_players(self.black_player_id, self.white_player_id) # 設定引き継ぎ
            self.game_started = True # ゲームは開始状態のまま
            logging.info("Game restarted.") # pragma: no cover
        elif self.gui.is_reset_button_clicked(mouse_click_pos, game_over=False):
            self._invalidate_ai_thinking() # 思考中の古い AI 結果を無効化
            self.game.reset()
            self._resume_human_override = None  # 打ち直しの一時的な人間化を解除
            self.black_player_id = 0 # 設定リセット
            self.white_player_id = 0
            self.game.set_players(self.black_player_id, self.white_player_id)
            self.game_started = False # 開始前に戻る
            logging.info("Game reset to initial state.") # pragma: no cover
        elif self.gui.is_quit_button_clicked(mouse_click_pos, game_over=False):
            self.running = False
            logging.info("Game exited from in-game screen.") # pragma: no cover
        elif self.gui.is_undo_button_clicked(mouse_click_pos, game_over=False):
            # 1手戻る
            if self.game.history_index >= 0:
                self._invalidate_ai_thinking() # 思考中の古い AI 結果を無効化
                current_index = self.game.history_index
                self.game.replay(current_index - 1)
                # AIが相手ならもう1手戻る (自分が打つ直前の状態に戻す)
                if self.game.agents[self.game.turn] is not None and current_index >= 1:
                    self.game.replay(current_index - 2)
                self.game.set_message("") # メッセージをクリア
                logging.info("Game state undone.") # pragma: no cover

        # ----------------------------------------------------
        else:
            # ゲーム中のプレイヤー設定クリックを処理する
            player_settings_top = self.gui._calculate_player_settings_top()
            clicked_player, _ = self.gui.get_clicked_radio_button(
                mouse_click_pos, player_settings_top
            )
            if clicked_player is not None:
                self._handle_player_settings_click(mouse_click_pos)
            elif self.game.agents[self.game.turn] is None:
                self._handle_human_move(mouse_click_pos)

    def _handle_human_move(self, mouse_click_pos: tuple[int, int]):
        """人間の手番での盤面クリック処理"""
        # AIが思考中の場合は入力を無視
        if self.is_ai_thinking:
            return

        # クリックされたセル座標を取得
        row, col = self.gui.get_clicked_cell(mouse_click_pos)
        # 現在のプレイヤーの合法手を取得
        valid_moves = self.game.get_valid_moves()
        # クリックされたセルが合法手か判定
        if (row, col) in valid_moves:
            mover = self.game.turn
            # 石を置く処理を実行
            if self.game.place_stone(row, col):
                # 打ち直しの 1 手を打ったら、以後は画面のプレイヤー設定で進める
                if self._resume_human_override == mover:
                    self._restore_screen_players()
                logging.info(f"Human player placed stone at ({row}, {col}).") # pragma: no cover
                self.game.set_message("") # メッセージをクリア
                self.game.switch_turn()   # 手番を交代
                self.game.check_game_over() # ゲームオーバーかチェック
                if self.game.game_over:
                    logging.info("Game over detected after human move.") # pragma: no cover
            else: # pragma: no cover
                # 通常、valid_moves チェックがあるのでここには来ないはず
                # place_stone が予期せず False を返した場合のエラーログ
                logging.error(f"Error: place_stone({row}, {col}) returned False unexpectedly for human player.") # pragma: no cover

        # else: 合法手以外がクリックされた場合は何もしない

    # === AI・パス処理 ===

    def _handle_ai_or_pass(self):
        """AIの手番またはパスの処理"""
        # AIが思考中の場合は何もしない
        if self.is_ai_thinking:
            return

        current_turn = self.game.turn
        current_agent = self.game.agents[current_turn]
        valid_moves = self.game.get_valid_moves()

        if not valid_moves:
            # 合法手がない場合はパス
            self._handle_pass(current_turn)
        elif current_agent is not None:
            # AI 失敗直後の再試行抑制期間中は起動しない（リトライストーム防止）
            if pygame.time.get_ticks() < self._ai_retry_not_before:
                return
            # AIの手番の場合
            self.is_ai_thinking = True
            self.game.set_message(_t("game.thinking", default="Thinking..."))
            # メインスレッドが Undo / Reset で盤面を書き換えても影響しないよう、
            # ゲーム状態のスナップショットを渡す
            game_snapshot = copy.deepcopy(self.game)
            self.ai_thread = threading.Thread(
                target=self._run_ai_agent,
                args=(current_agent, game_snapshot, self._ai_generation),
            )
            self.ai_thread.daemon = True
            self.ai_thread.start()
        # else: 人間の手番の場合は何もしない (クリック待ち)

    def _run_ai_agent(self, agent, game_snapshot, generation: int) -> None:
        """AIエージェントを実行するスレッドワーカー"""
        try:
            move = agent.play(game_snapshot)
            self.ai_queue.put((move, generation))
        except Exception as e:
            logging.error(f"Error in AI thread: {e}")
            self.ai_queue.put((None, generation))

    def _handle_pass(self, current_turn: int):
        """パス処理"""
        pass_message = _t("game.black_pass") if current_turn == -1 else _t("game.white_pass")
        self.game.set_message(pass_message)
        logging.info(f"Player {'Black' if current_turn == -1 else 'White'} passed.") # pragma: no cover
        self.game.switch_turn() # 手番を交代
        # 相手もパスかチェック
        opponent_valid_moves = self.game.get_valid_moves()
        if not opponent_valid_moves:
            # 相手もパスならゲームオーバー
            self.game.game_over = True
            logging.info("Both players passed. Game over.") # pragma: no cover
            # 勝敗メッセージの設定は _render で行う

    def _apply_ai_move(self, move: tuple[int, int] | None):
        """AIの手番結果を適用する"""
        valid_moves = self.game.get_valid_moves()
        # AIが有効な手を返したか確認
        if move and move in valid_moves:
            # 石を置く処理を実行
            if self.game.place_stone(move[0], move[1]):
                # Determine player color and agent display name for clearer logs
                player_color = "Black" if self.game.turn == -1 else "White"
                # Try to resolve the agent id from App-level stored ids if available
                try:
                    agent_id = self.black_player_id if self.game.turn == -1 else self.white_player_id
                    agent_def = get_agent_definition(agent_id)
                    agent_name = agent_def.get('display_name') if agent_def else None
                except Exception:  # pragma: no cover - defensive fallback; tested via unit tests that exercise normal path
                    agent_name = None
                if agent_name:
                    logging.info(f"AI ({player_color}, {agent_name}) placed stone at {move}.") # pragma: no cover
                else:
                    logging.info(f"AI ({player_color}) placed stone at {move}.") # pragma: no cover
                self.game.set_message("") # メッセージをクリア
                self.game.switch_turn()   # 手番を交代
                self.game.check_game_over() # ゲームオーバーかチェック
                if self.game.game_over:
                    logging.info("Game over detected after AI move.") # pragma: no cover
            else: # pragma: no cover
                # 通常、AIがvalid_moves内の手を返すのでここには来ないはず
                logging.error(f"Error: place_stone{move} returned False unexpectedly for AI agent.") # pragma: no cover
        else:
            # AIが None を返した、または無効な手を返した場合
            if move is not None: # パス（None）以外で無効な手の場合
                log_message = f"AI returned invalid move: {move}. Valid moves: {valid_moves}"
                logging.warning(log_message) # pragma: no cover
            # 合法手があるのに手を返せなかった場合は API 障害などの失敗。
            # 毎フレーム再起動するリトライストームを防ぐため、一定時間待ってから再試行する
            if valid_moves:
                self._ai_retry_not_before = pygame.time.get_ticks() + AI_RETRY_DELAY_MS
                self.game.set_message(
                    _t("game.ai_error", default="AI エラー: 再試行します...")
                )

    # === 解説モード ===

    def _invalidate_analysis(self) -> None:
        """進行中の解析とキャッシュ済み解説結果を無効化する。"""
        self._analysis_generation += 1
        self.is_analyzing = False
        self.analysis_progress = (0, 0)
        self.analysis_result = None
        self.analysis_mode = False
        self.resume_pending = False
        self.resume_notices = []
        self.analysis_move_index = 0
        self.analysis_pv_step = 0
        while not self.analysis_queue.empty():
            self.analysis_queue.get_nowait()

    def _start_analysis(self) -> None:
        """終局後の敗着解説を開始する（キャッシュがあれば即座に表示）。"""
        if self.analysis_result is not None:
            self._enter_analysis_mode()
            return
        if not self.game.history:
            return
        self.is_analyzing = True
        self.analysis_progress = (0, 0)
        history_snapshot = [
            (move, turn, [row[:] for row in board])
            for move, turn, board in self.game.history
        ]
        gen = self._analysis_generation
        self.analysis_thread = threading.Thread(
            target=self._run_analysis_worker,
            args=(history_snapshot, self.game.board_size, gen),
        )
        self.analysis_thread.daemon = True
        self.analysis_thread.start()

    def _run_analysis_worker(
        self,
        history_snapshot: list[tuple[tuple[int, int], int, list[list[int]]]],
        board_size: int,
        generation: int,
    ) -> None:
        """バックグラウンドスレッドで対局解析を実行する。"""
        try:
            result = analyze_game(
                history=history_snapshot,
                board_size=board_size,
                on_progress=lambda done, total: self.analysis_queue.put(
                    ("progress", (done, total), generation)
                ),
            )
            self.analysis_queue.put(("done", result, generation))
        except Exception as e:
            logging.error(f"Error in analysis thread: {e}")
            self.analysis_queue.put(("error", str(e), generation))

    def _poll_analysis_queue(self) -> None:
        """解析スレッドからの進捗・完了イベントを処理する。"""
        while True:
            try:
                kind, payload, gen = self.analysis_queue.get_nowait()
            except queue.Empty:
                break
            if gen != self._analysis_generation:
                continue
            if kind == "progress":
                self.analysis_progress = payload
            elif kind == "done":
                self.is_analyzing = False
                self.analysis_result = payload
                logging.info(f"Game analysis completed: {payload.headline}")  # pragma: no cover
                if payload.missed_win_move_index is not None:  # pragma: no cover
                    mw = payload.moves_by_index[payload.missed_win_move_index]  # pragma: no cover
                    logging.info(f"Missed win: {mw.summary}")  # pragma: no cover
                if payload.loss_sealed_move_index is not None:  # pragma: no cover
                    ls = payload.moves_by_index[payload.loss_sealed_move_index]  # pragma: no cover
                    logging.info(f"Loss sealed: {ls.summary}")  # pragma: no cover
                if payload.draw_sealed_move_index is not None:  # pragma: no cover
                    ds = payload.moves_by_index[payload.draw_sealed_move_index]  # pragma: no cover
                    logging.info(f"Draw sealed: {ds.summary}")  # pragma: no cover
                for m in payload.key_mistakes:
                    logging.info(m.summary)  # pragma: no cover
                self._enter_analysis_mode()
            elif kind == "error":
                self.is_analyzing = False

    def _enter_analysis_mode(self) -> None:
        """解説モードに入り、決定的敗着（または最大悪手）を初期表示する。"""
        if self.analysis_result is None or not self.game.history:
            return
        self.analysis_mode = True
        self.analysis_pv_step = 0
        if self.analysis_result.key_mistakes:
            self.analysis_move_index = self.analysis_result.key_mistakes[0].move_index
        else:
            self.analysis_move_index = len(self.game.history) - 1
        self.gui.reset_analysis_scroll()

    def _set_analysis_move_index(self, move_index: int) -> None:
        """解説対象の手数インデックスを移動する。"""
        if not self.game.history:
            return
        clamped = max(0, min(len(self.game.history) - 1, move_index))
        self.analysis_move_index = clamped
        self.analysis_pv_step = 0
        self.gui.reset_analysis_scroll()

    def _step_analysis_mistake(self, direction: int) -> None:
        """主な悪手（key_mistakes）間を前後移動する。"""
        if self.analysis_result is None or not self.analysis_result.key_mistakes:
            return
        indices = [m.move_index for m in self.analysis_result.key_mistakes]
        if self.analysis_move_index in indices:
            cur_pos = indices.index(self.analysis_move_index)
            next_pos = (cur_pos + direction) % len(indices)
            self._set_analysis_move_index(indices[next_pos])
        else:
            self._set_analysis_move_index(indices[0])

    def _advance_analysis_pv(self) -> None:
        """推奨手順（PV）のコマ送りステップを進める（末尾に達したら 0 に戻る）。"""
        if self.analysis_result is None:
            return
        ma = self.analysis_result.moves_by_index.get(self.analysis_move_index)
        if ma is None or not ma.pv:
            return
        self.analysis_pv_step = (self.analysis_pv_step + 1) % (len(ma.pv) + 1)

    def _resume_from_analysis_move(self, move_index: int) -> None:
        """解説中の任意局面へ巻き戻し、継続プレイヤーを指定できる打ち直し準備状態へ入る。"""
        if not (0 <= move_index < len(self.game.history)):
            return
        ma = (
            self.analysis_result.moves_by_index.get(move_index)
            if self.analysis_result is not None
            else None
        )
        target_turn = self.game.history[move_index][1]
        # 巻き戻すと最終盤面が失われるため、負けた側は巻き戻す前に求める
        human_side = self._resume_human_side(target_turn)

        self.game.replay(move_index - 1)
        self.game.turn = target_turn
        self.game._invalidate_valid_moves_cache()

        self._invalidate_ai_thinking()
        self.analysis_mode = False
        self.resume_pending = True
        self.game.game_over = False
        self.game_started = True

        # 前回の打ち直しの上書きが残っていれば、画面の設定に戻してから適用し直す
        self._restore_screen_players()
        notices: list[str] = []
        if self._apply_resume_human_override(human_side):
            notices.append(
                _t(
                    "game.resume_switched_to_human",
                    default="{color}は 1 手だけ人間が打ちます（以後は画面の設定で進行）",
                    color=self._color_name(human_side),
                )
            )
        if ma is not None:
            r, c = ma.best_move
            notices.append(
                _t(
                    "game.resume_recommended",
                    default="推奨手: {move}",
                    move=f"{chr(ord('A') + c)}{r + 1}",
                )
            )
        sealed = self._resume_sealed_notice(ma, target_turn, human_side)
        if sealed is not None:
            # 長い文言は改行で 2 行に分けて表示する
            notices.extend(sealed.split("\n"))
        if self.game.agents[target_turn] is None:
            notices.append(
                _t("game.resume_instruction", default="盤面をクリックするか「対局再開」で再開")
            )
        else:
            notices.append(
                _t("game.resume_instruction_ai", default="「対局再開」で AI の手番から再開")
            )
        self.resume_notices = notices

        self.game.set_message(
            _t(
                "game.resumed_from_move",
                default="第{move}手から打ち直し",
                move=move_index + 1,
            )
        )

    def _resume_human_side(self, target_turn: int) -> int:
        """打ち直しで人間が担当する側を返す（負けた側。引き分けなら打ち直す手番の側）。"""
        if self.analysis_result is not None:
            loser = self.analysis_result.loser
        else:
            final_board = self.game.history[-1][2]
            black = sum(row.count(-1) for row in final_board)
            white = sum(row.count(1) for row in final_board)
            loser = 1 if black > white else (-1 if white > black else 0)
        return loser if loser != 0 else target_turn

    def _apply_resume_human_override(self, side: int) -> bool:
        """打ち直しの 1 手だけ、指定した側を人間が打つようにする。

        画面のプレイヤー設定（black_player_id / white_player_id）は変えず、
        その側のエージェントだけを一時的に人間（None）にする。

        Returns:
            その側が AI で、人間に切り替えた場合 True。もともと人間なら False。
        """
        if self.game.agents[side] is None:
            return False
        self.game.agents[side] = None
        self._resume_human_override = side
        return True

    def _restore_screen_players(self) -> None:
        """打ち直しの一時的な人間化を解除し、画面のプレイヤー設定どおりのエージェントに戻す。"""
        if self._resume_human_override is None:
            return
        self._resume_human_override = None
        self.game.set_players(self.black_player_id, self.white_player_id)

    @staticmethod
    def _color_name(side: int) -> str:
        """手番の値（黒 -1、白 1）を表示用の色名に変換する。"""
        if side == -1:
            return _t("game.color_black", default="黒")
        return _t("game.color_white", default="白")

    def _resume_sealed_notice(
        self, ma: Optional[MoveAnalysis], target_turn: int, human_side: int
    ) -> Optional[str]:
        """打ち直す局面が完全読み切りで、人間側の勝ちが無くなっていれば、その旨の文言を返す。

        Args:
            ma: 打ち直す手の解析結果（解析対象外の手なら None）。
            target_turn: 打ち直す局面の手番。
            human_side: 人間が担当する側。

        Returns:
            負け確定・引き分けまでの文言。勝ちの可能性が残る・読み切れない場合は None。
        """
        if ma is not None and ma.is_exact and ma.best_disc_diff is not None:
            mover_diff: Optional[int] = ma.best_disc_diff
        else:
            # 解析対象外の手（勝った側の手・合法手 1 手の局面など）は、終盤ならその場で読み切る
            mover_diff = solve_position_disc_diff(self.game.board.board, target_turn)
        if mover_diff is None:
            return None

        human_diff = mover_diff if human_side == target_turn else -mover_diff
        color = self._color_name(human_side)
        if human_diff < 0:
            return _t(
                "game.resume_loss_sealed",
                default="完全読み切り: 相手が最善なら{color}に勝ち目なし\n（最善でも {diff} 石差負け）",
                color=color,
                diff=-human_diff,
            )
        if human_diff == 0:
            return _t(
                "game.resume_draw_sealed",
                default="完全読み切り: 相手が最善なら{color}に勝ち目なし\n（最善でも引き分け）",
                color=color,
            )
        return None

    def _confirm_resume_play(self) -> None:
        """打ち直し準備状態を確定し、選択中のプレイヤー設定で対局を再開する。"""
        self.resume_pending = False
        self.resume_notices = []
        self._invalidate_analysis()
        self.game.set_message("")

    def _back_to_analysis_from_resume(self) -> None:
        """打ち直し準備状態から解説画面へ戻る。"""
        self.resume_pending = False
        self.resume_notices = []
        self._restore_screen_players()
        if self.game.history:
            self.game.replay(len(self.game.history) - 1)
        self.game.game_over = True
        self.analysis_mode = True

    def _handle_click_resume_pending(self, mouse_click_pos: tuple[int, int]) -> None:
        """打ち直し準備状態（プレイヤー選択待ち）でのクリックを処理する。"""
        action = self.gui.get_clicked_resume_pending_button(mouse_click_pos)
        if action == "back_to_analysis":
            self._back_to_analysis_from_resume()
            return
        if action == "confirm_resume":
            self._confirm_resume_play()
            return
        if action == "reset":
            self._invalidate_ai_thinking()
            self._invalidate_analysis()
            self.game.reset()
            self._resume_human_override = None  # 打ち直しの一時的な人間化を解除
            self.black_player_id = 0
            self.white_player_id = 0
            self.game.set_players(self.black_player_id, self.white_player_id)
            self.game_started = False
            return
        if action == "quit":
            self.running = False
            return

        player_settings_top = self.gui._calculate_player_settings_top()
        clicked_player, _ = self.gui.get_clicked_radio_button(
            mouse_click_pos, player_settings_top
        )
        if clicked_player is not None:
            self._handle_player_settings_click(mouse_click_pos)
            return

        if self.game.agents[self.game.turn] is None:
            cell = self.gui.get_clicked_cell(mouse_click_pos)
            if cell in self.game.get_valid_moves():
                self._confirm_resume_play()
                self._handle_human_move(mouse_click_pos)

    def _handle_analysis_click(self, mouse_click_pos: tuple[int, int]) -> None:
        """解説モード中のマウスクリックを処理する。"""
        action = self.gui.get_clicked_analysis_button(mouse_click_pos)
        if action == "prev_mistake":
            self._step_analysis_mistake(-1)
            return
        if action == "next_mistake":
            self._step_analysis_mistake(1)
            return
        if action == "resume":
            self._resume_from_analysis_move(self.analysis_move_index)
            return
        if action == "close":
            self.analysis_mode = False
            return

        if self.analysis_result is None or not self.game.history:
            return
        ma = self.analysis_result.moves_by_index.get(self.analysis_move_index)
        has_pv = bool(ma is not None and ma.pv)
        panel_top = self.gui._calculate_player_settings_top()
        nav_action, nav_idx = self.gui.get_clicked_analysis_nav(
            mouse_click_pos, panel_top, len(self.game.history), has_pv
        )
        if nav_action == "step_prev":
            self._set_analysis_move_index(self.analysis_move_index - 1)
        elif nav_action == "step_next":
            self._set_analysis_move_index(self.analysis_move_index + 1)
        elif nav_action == "toggle_pv":
            self._advance_analysis_pv()
        elif nav_action == "jump_move" and nav_idx is not None:
            self._set_analysis_move_index(nav_idx)

    def _handle_analysis_key(self, key: int) -> None:
        """解説モード中のキーボード操作を処理する。"""
        if key == pygame.K_LEFT:
            self._set_analysis_move_index(self.analysis_move_index - 1)
        elif key == pygame.K_RIGHT:
            self._set_analysis_move_index(self.analysis_move_index + 1)
        elif key == pygame.K_UP:
            self._step_analysis_mistake(-1)
        elif key == pygame.K_DOWN:
            self._step_analysis_mistake(1)
        elif key == pygame.K_SPACE:
            self._advance_analysis_pv()
        elif key == pygame.K_ESCAPE:
            self.analysis_mode = False

    def _get_analysis_board_view(
        self,
    ) -> tuple[
        list[list[int]],
        int,
        int,
        Optional[tuple[int, int]],
        Optional[tuple[int, int]],
        Optional[tuple[int, int]],
    ]:
        """解説画面に表示する盤面・石数・ハイライト座標を返す。"""
        assert self.analysis_result is not None
        idx = self.analysis_move_index
        played_move, move_turn, _ = self.game.history[idx]
        ma = self.analysis_result.moves_by_index.get(idx)
        if ma is not None:
            base_board = [row[:] for row in ma.board_before]
        elif idx == 0:
            base_board = _initial_board(self.game.board_size)
        else:
            base_board = [row[:] for row in self.game.history[idx - 1][2]]

        board_obj = Board(self.game.board_size)
        board_obj.board = [row[:] for row in base_board]

        if self.analysis_pv_step > 0 and ma is not None and ma.pv:
            cur_turn = move_turn
            last_pv: Optional[tuple[int, int]] = None
            for step_move in ma.pv[: self.analysis_pv_step]:
                if step_move not in board_obj.get_valid_moves(cur_turn):
                    cur_turn = -cur_turn
                board_obj.place_stone(step_move[0], step_move[1], cur_turn)
                last_pv = step_move
                cur_turn = -cur_turn
            b_cnt, w_cnt = board_obj.count_stones()
            return board_obj.get_board(), b_cnt, w_cnt, None, None, last_pv

        b_cnt, w_cnt = board_obj.count_stones()
        best_move = ma.best_move if ma is not None else None
        return board_obj.get_board(), b_cnt, w_cnt, played_move, best_move, None

    def _render_analysis(self, player_settings_top: int) -> None:
        """解説モード画面を描画する。"""
        assert self.analysis_result is not None
        board_data, b_cnt, w_cnt, played_move, best_move, last_pv = (
            self._get_analysis_board_view()
        )
        self.gui.draw_analysis_board(
            board_data,
            b_cnt,
            w_cnt,
            played_move=played_move,
            best_move=best_move,
            last_pv_move=last_pv,
        )
        self.gui.draw_analysis_buttons()
        raw_played, move_turn, _ = self.game.history[self.analysis_move_index]
        self.gui.draw_analysis_panel(
            analysis=self.analysis_result,
            move_index=self.analysis_move_index,
            pv_step=self.analysis_pv_step,
            total_moves=len(self.game.history),
            move_turn=move_turn,
            played_move=raw_played,
            panel_top=player_settings_top,
        )

    # === 描画 ===

    def _render(self):
        """画面を描画する"""
        # 背景クリアは draw_board (_draw_board_background) が全画面 fill で行うため、
        # ここでの fill は二重描画になるので行わない
        # プレイヤー設定UIの上端Y座標を計算 (描画要素の位置決めに使う)
        player_settings_top = self.gui._calculate_player_settings_top()

        # ゲームの状態に応じて描画内容を切り替え
        if not self.game_started:
            self._render_before_start(player_settings_top)
        elif self.game.game_over:
            self._render_game_over(player_settings_top)
        else: # ゲーム中
            self._render_in_game(player_settings_top)

        # 描画内容を画面に反映
        pygame.display.flip()

    def _render_before_start(self, player_settings_top: int):
        """ゲーム開始前の画面を描画"""
        self.gui.draw_board(self.game)
        self.gui.draw_start_button()
        # プレイヤー設定UIを描画 (操作可能 enabled=True)
        self.gui.draw_player_settings(self.game, player_settings_top, enabled=True)

    def _render_game_over(self, player_settings_top: int):
        """ゲームオーバー画面を描画"""
        if self.analysis_mode and self.analysis_result is not None:
            self._render_analysis(player_settings_top)
            return

        # 勝敗結果を取得
        winner = self.game.get_winner()
        # 勝敗メッセージを作成
        winner_message = ""
        if winner == -1:
            winner_message = _t("game.black_win") # pragma: no cover
        elif winner == 1:
            winner_message = _t("game.white_win") # pragma: no cover
        else:
            winner_message = _t("game.draw") # pragma: no cover
        # game.message がパスなどで上書きされている可能性があるので、ここで最終的な勝敗メッセージを設定
        if self.is_analyzing:
            done, total = self.analysis_progress
            self.game.set_message(
                _t("game.analyzing", default="解析中... ({done}/{total})", done=done, total=total)
            )
        else:
            self.game.set_message(winner_message)

        # 画面要素を描画
        self.gui.draw_board(self.game)
        # 勝敗メッセージを描画 (is_game_over=True で位置調整)
        self.gui.draw_message(self.game.get_message(), is_game_over=True)
        # プレイヤー設定UIを描画 (リセット用に操作可能 enabled=True)
        self.gui.draw_player_settings(self.game, player_settings_top, enabled=True)
        # 各ボタンを描画 (game_over=True で位置調整)
        self.gui.draw_analyze_button(game_over=True)
        self.gui.draw_restart_button(game_over=True)
        self.gui.draw_reset_button(game_over=True)
        self.gui.draw_quit_button(game_over=True)
        logging.debug("Rendered game over screen.") # pragma: no cover

    def _render_in_game(self, player_settings_top: int):
        """ゲーム中の画面を描画"""
        self.gui.draw_board(self.game)
        # 人間の手番の場合、合法手マーカーを描画
        if self.game.agents[self.game.turn] is None:
            self.gui.draw_valid_moves(self.game)
        # 手番表示を描画
        self.gui.draw_turn_message(self.game)
        # 各ボタンを描画 (game_over=False)
        if self.resume_pending:
            self.gui.draw_resume_pending_buttons()
            # 人間の手番なら合法手が帯に隠れないようにする
            human_moves = (
                self.game.get_valid_moves() if self.game.agents[self.game.turn] is None else []
            )
            self.gui.draw_resume_notices(self.resume_notices, human_moves)
        else:
            self.gui.draw_undo_button(game_over=False)
            self.gui.draw_restart_button(game_over=False)
            self.gui.draw_reset_button(game_over=False)
            self.gui.draw_quit_button(game_over=False)
        # パスメッセージなどを描画
        self.gui.draw_message(self.game.get_message())
        # プレイヤー設定UIを描画 (ゲーム中も操作可能 enabled=True)
        self.gui.draw_player_settings(self.game, player_settings_top, enabled=True)
        logging.debug("Rendered in-game screen.") # pragma: no cover


def main():
    """
    アプリケーションのエントリーポイント。
    Pygameの初期化、Game, GameGUI, App のインスタンス生成を行い、
    Appのメインループを実行する。
    """
    pygame.init()
    game_instance = Game()
    # Allow the application to shrink window width to reduce side padding by default
    gui_instance = GameGUI(allow_width_shrink=True)
    app = App(game_instance, gui_instance)
    app.run()

if __name__ == "__main__": # pragma: no cover
    main()

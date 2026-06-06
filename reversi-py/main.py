# main.py
import pygame
import sys
import logging
import threading
import queue
from game import Game
from gui import GameGUI
from config.theme import Color
# --- config.i18n からインポート ---
from config.i18n import _t
# -----------------------------

class App:
    """
    リバーシゲームアプリケーション全体を管理するクラス。
    イベント処理、状態更新、描画のメインループを担当する。
    """
    def __init__(self, game: Game, gui: GameGUI):
        """
        Appクラスのコンストラクタ。

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

    def run(self):
        """
        ゲームのメインループを実行する。
        イベント処理、状態更新、描画を繰り返す。
        """
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

    def _handle_events(self) -> tuple[int, int] | None:
        """
        Pygameのイベントを処理する。
        QUITイベントで実行フラグをFalseにし、左マウスクリック位置を返す。

        Returns:
            tuple[int, int] | None: 左クリックがあった場合はその座標、なければ None。
        """
        mouse_click_pos = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 左クリック (ボタン番号 1) のみ処理
                if event.button == 1:
                    mouse_click_pos = event.pos
                    return mouse_click_pos
        return mouse_click_pos

    def _update_state(self, mouse_click_pos: tuple[int, int] | None):
        """
        ゲームの状態を更新する。
        マウスクリックイベントや、現在のゲーム状況 (AIの手番、パス) に基づいて処理を行う。

        Args:
            mouse_click_pos: マウスのクリック位置 (クリックがなければ None)。
        """
        # --- AIの思考結果をチェック ---
        if self.is_ai_thinking:
            try:
                move = self.ai_queue.get_nowait()
                self.is_ai_thinking = False
                self._apply_ai_move(move)
            except queue.Empty:
                pass # まだ考え中

        # --- 1. マウスクリックに基づく更新 ---
        if mouse_click_pos:
            if not self.game_started:
                # ゲーム開始前のクリック処理 (スタートボタン、プレイヤー選択)
                self._handle_click_before_start(mouse_click_pos)
            elif self.game.game_over:
                # ゲームオーバー時のクリック処理 (リスタート、リセット、終了)
                self._handle_click_game_over(mouse_click_pos)
            else:  # ゲーム中
                # ゲーム中のクリック処理 (リスタート、リセット、終了、盤面クリック)
                self._handle_click_in_game(mouse_click_pos)

        # --- 2. AIの手番、パス処理 (クリックがない場合でも実行される) ---
        # ゲームが開始していて、かつゲームオーバーでない場合にのみ処理
        if self.game_started and not self.game.game_over:
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
            # プレイヤー選択ラジオボタンがクリックされたか判定
            player_settings_top = self.gui._calculate_player_settings_top()
            clicked_player, clicked_agent_id = self.gui.get_clicked_radio_button(
                mouse_click_pos, player_settings_top
            )
            # ラジオボタンがクリックされた場合
            if clicked_player is not None:
                player_changed = False
                # 黒プレイヤーの選択が変更されたか
                if clicked_player == -1 and self.black_player_id != clicked_agent_id:
                    self.black_player_id = clicked_agent_id
                    player_changed = True
                # 白プレイヤーの選択が変更されたか
                elif clicked_player == 1 and self.white_player_id != clicked_agent_id:
                    self.white_player_id = clicked_agent_id
                    player_changed = True

                # プレイヤー設定が変更された場合、Gameオブジェクトに反映
                if player_changed:
                    self.game.set_players(self.black_player_id, self.white_player_id)
                    logging.info(f"Player settings changed: Black={self.black_player_id}, White={self.white_player_id}") # pragma: no cover

    def _handle_click_game_over(self, mouse_click_pos: tuple[int, int]):
        """ゲームオーバー時のクリック処理"""
        # --- 修正: gui の is_*_button_clicked を呼び出す ---
        if self.gui.is_restart_button_clicked(mouse_click_pos, game_over=True):
            self.game.reset()
            # 現在のプレイヤー設定を引き継いでリセット
            self.game.set_players(self.black_player_id, self.white_player_id)
            self.game_started = True # ゲーム開始状態にする
            logging.info("Game restarted.") # pragma: no cover
        elif self.gui.is_reset_button_clicked(mouse_click_pos, game_over=True):
            self.game.reset()
            # プレイヤー設定も初期化 (両者人間)
            self.black_player_id = 0
            self.white_player_id = 0
            self.game.set_players(self.black_player_id, self.white_player_id)
            self.game_started = False # ゲーム開始前の状態に戻す
            logging.info("Game reset to initial state.") # pragma: no cover
        elif self.gui.is_quit_button_clicked(mouse_click_pos, game_over=True):
            self.running = False # メインループを終了
        # else: pragma: no cover
        #     pass # pragma: no cover
        # ----------------------------------------------------

    def _handle_click_in_game(self, mouse_click_pos: tuple[int, int]):
        """ゲーム中のクリック処理"""
        # --- 修正: gui の is_*_button_clicked を呼び出す ---
        if self.gui.is_restart_button_clicked(mouse_click_pos, game_over=False):
            self.game.reset()
            self.game.set_players(self.black_player_id, self.white_player_id) # 設定引き継ぎ
            self.game_started = True # ゲームは開始状態のまま
            logging.info("Game restarted.") # pragma: no cover
        elif self.gui.is_reset_button_clicked(mouse_click_pos, game_over=False):
            self.game.reset()
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
                self.game.replay(self.game.history_index - 1)
                # AIが相手ならもう1手戻る (自分が打つ直前の状態に戻す)
                if self.game.agents[self.game.turn] is not None and self.game.history_index >= 0:
                    self.game.replay(self.game.history_index - 1)
                self.game.set_message("") # メッセージをクリア
                logging.info("Game state undone.") # pragma: no cover

        # ----------------------------------------------------
        # プレイヤーが人間の手番の場合、盤面クリックを処理
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
            # 石を置く処理を実行
            if self.game.place_stone(row, col):
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
            # AIの手番の場合
            self.is_ai_thinking = True
            self.game.set_message(_t("game.thinking", default="Thinking..."))
            self.ai_thread = threading.Thread(target=self._run_ai_agent, args=(current_agent,))
            self.ai_thread.daemon = True
            self.ai_thread.start()
        # else: 人間の手番の場合は何もしない (クリック待ち)

    def _run_ai_agent(self, agent):
        """AIエージェントを実行するスレッドワーカー"""
        try:
            move = agent.play(self.game)
            self.ai_queue.put(move)
        except Exception as e:
            logging.error(f"Error in AI thread: {e}")
            self.ai_queue.put(None)

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
                logging.info(f"AI placed stone at {move}.") # pragma: no cover
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

    def _render(self):
        """画面を描画する"""
        # 背景色で画面をクリア
        self.gui.screen.fill(Color.BACKGROUND)
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
        self.game.set_message(winner_message)

        # 画面要素を描画
        self.gui.draw_board(self.game)
        # 勝敗メッセージを描画 (is_game_over=True で位置調整)
        self.gui.draw_message(self.game.get_message(), is_game_over=True)
        # プレイヤー設定UIを描画 (リセット用に操作可能 enabled=True)
        self.gui.draw_player_settings(self.game, player_settings_top, enabled=True)
        # 各ボタンを描画 (game_over=True で位置調整)
        self.gui.draw_restart_button(game_over=True)
        self.gui.draw_reset_button(game_over=True)
        self.gui.draw_quit_button(game_over=True)
        logging.info("Rendered game over screen.") # pragma: no cover

    def _render_in_game(self, player_settings_top: int):
        """ゲーム中の画面を描画"""
        self.gui.draw_board(self.game)
        # 人間の手番の場合、合法手マーカーを描画
        if self.game.agents[self.game.turn] is None:
            self.gui.draw_valid_moves(self.game)
        # 手番表示を描画
        self.gui.draw_turn_message(self.game)
        # 各ボタンを描画 (game_over=False)
        self.gui.draw_undo_button(game_over=False)
        self.gui.draw_restart_button(game_over=False)
        self.gui.draw_reset_button(game_over=False)
        self.gui.draw_quit_button(game_over=False)
        # パスメッセージなどを描画
        self.gui.draw_message(self.game.get_message())
        # プレイヤー設定UIを描画 (ゲーム中は操作不可 enabled=False)
        self.gui.draw_player_settings(self.game, player_settings_top, enabled=False)
        logging.info("Rendered in-game screen.") # pragma: no cover


def main():
    """
    アプリケーションのエントリーポイント。
    Pygameの初期化、Game, GameGUI, App のインスタンス生成を行い、
    Appのメインループを実行する。
    """
    pygame.init()
    game_instance = Game()
    gui_instance = GameGUI()
    app = App(game_instance, gui_instance)
    app.run()

if __name__ == "__main__": # pragma: no cover
    main()

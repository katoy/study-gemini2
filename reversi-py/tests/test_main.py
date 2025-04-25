# tests/test_main.py
import unittest
import sys
import os
from unittest.mock import MagicMock, patch, call, ANY

# プロジェクトルートへのパスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# テスト対象のモジュールをインポート (main 関数自体を直接呼び出すわけではない)
# import main # main自体は使わないのでコメントアウトしても良い

# モックする可能性のあるモジュールやクラス
import pygame # pygame の関数をモック化

class TestMain(unittest.TestCase):

    @patch('main.pygame', spec=pygame)
    @patch('main.Game')
    @patch('main.GameGUI')
    @patch('main.logging')
    @patch('main.sys')
    @patch('builtins.print') # print出力を抑制
    def setUp(self, mock_print, mock_sys, mock_logging, MockGameGUI, MockGame, mock_pygame):
        """各テストの前にモックを設定"""
        # Pygame のモック設定
        self.mock_pygame = mock_pygame
        self.mock_pygame.time.Clock.return_value.tick.return_value = 16 # 60 FPS相当
        self.mock_pygame.event.get.return_value = [] # デフォルトではイベントなし
        self.mock_pygame.QUIT = pygame.QUIT
        self.mock_pygame.MOUSEBUTTONDOWN = pygame.MOUSEBUTTONDOWN
        self.mock_pygame.K_LEFT = pygame.K_LEFT

        # Game のモック設定
        self.MockGame = MockGame
        self.mock_game_instance = self.MockGame.return_value
        self.mock_game_instance.turn = -1
        self.mock_game_instance.game_over = False
        self.mock_game_instance.agents = {-1: None, 1: None}
        self.mock_game_instance.get_valid_moves.return_value = [(2, 3), (3, 2)]
        self.mock_game_instance.place_stone.return_value = True
        self.mock_game_instance.get_winner.return_value = 0
        # self.mock_game_instance.get_message.return_value = "" # ← 削除

        # メッセージ状態を保持する変数 (テストクラスの属性として)
        self._current_message = ""

        # set_message が呼ばれたら _current_message を更新する side_effect
        def set_message_side_effect(msg):
            # print(f"DEBUG: set_message called with '{msg}'") # デバッグ用
            self._current_message = msg
        # get_message が呼ばれたら _current_message を返す side_effect
        def get_message_side_effect():
            # print(f"DEBUG: get_message called, returning '{self._current_message}'") # デバッグ用
            return self._current_message

        # MagicMock インスタンスに side_effect を設定
        self.mock_game_instance.set_message = MagicMock(side_effect=set_message_side_effect)
        self.mock_game_instance.get_message = MagicMock(side_effect=get_message_side_effect)

        # 他の主要なメソッドを明示的にモック化
        self.mock_game_instance.reset = MagicMock()
        self.mock_game_instance.switch_turn = MagicMock()
        self.mock_game_instance.check_game_over = MagicMock()
        self.mock_game_instance.set_players = MagicMock()

        # GameGUI のモック設定 (変更なし)
        self.MockGameGUI = MockGameGUI
        self.mock_gui_instance = self.MockGameGUI.return_value
        self.mock_gui_instance.screen = MagicMock()
        self.mock_gui_instance.is_button_clicked.return_value = False
        self.mock_gui_instance.get_clicked_cell.return_value = (-1, -1)
        self.mock_gui_instance.get_clicked_radio_button.return_value = (None, None)
        self.mock_gui_instance._calculate_button_rect.return_value = pygame.Rect(0, 0, 10, 10)
        self.mock_gui_instance._calculate_player_settings_top.return_value = 500
        self.mock_gui_instance.draw_board = MagicMock()
        self.mock_gui_instance.draw_start_button = MagicMock()
        self.mock_gui_instance.draw_player_settings = MagicMock()
        self.mock_gui_instance.draw_message = MagicMock()
        self.mock_gui_instance.draw_restart_button = MagicMock()
        self.mock_gui_instance.draw_reset_button = MagicMock()
        self.mock_gui_instance.draw_quit_button = MagicMock()
        self.mock_gui_instance.draw_valid_moves = MagicMock()
        self.mock_gui_instance.draw_turn_message = MagicMock()

        # logging, sys, print のモック (変更なし)
        self.mock_logging = mock_logging
        self.mock_sys = mock_sys
        self.mock_print = mock_print

        # main 関数内で使われるグローバル変数を模倣 (変更なし)
        self.game_started = False
        self.running = True
        self.black_player_id = 0
        self.white_player_id = 0

        # --- main() の初期化部分に相当する呼び出し ---
        self.mock_pygame.init()
        self.MockGame()
        self.MockGameGUI()
        self.mock_logging.basicConfig(level=ANY, format=ANY)
        self.mock_game_instance.set_players(self.black_player_id, self.white_player_id)
        self.mock_pygame.time.Clock()
        # 初期メッセージを設定
        self.mock_game_instance.set_message("") # 初期状態は空メッセージ


    def tearDown(self):
        """テスト後のクリーンアップ (特に不要だが念のため)"""
        patch.stopall() # すべてのパッチを停止

    # simulate_main_loop_iteration は変更なし
    def simulate_main_loop_iteration(self, events=None):
        """メインループの1イテレーションをシミュレートするヘルパー"""
        if events is None:
            events = []
        self.mock_pygame.event.get.return_value = events

        # --- イベント処理 ---
        mouse_click_pos = None
        for event in self.mock_pygame.event.get():
            if event.type == self.mock_pygame.QUIT:
                self.running = False
            if event.type == self.mock_pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # 左クリックのみ処理
                    mouse_click_pos = event.pos

        # --- 状態更新 (イベントに基づく) ---
        if mouse_click_pos:
            if not self.game_started:
                # ゲーム開始前
                start_button_rect = self.mock_gui_instance._calculate_button_rect(is_start_button=True)
                if self.mock_gui_instance.is_button_clicked(mouse_click_pos, start_button_rect):
                    self.game_started = True
                    self.mock_game_instance.set_message("")
                else:
                    player_settings_top = self.mock_gui_instance._calculate_player_settings_top()
                    clicked_player, clicked_agent_id = self.mock_gui_instance.get_clicked_radio_button(
                        mouse_click_pos, player_settings_top
                    )
                    if clicked_player is not None:
                        if clicked_player == -1: self.black_player_id = clicked_agent_id
                        elif clicked_player == 1: self.white_player_id = clicked_agent_id
                        self.mock_game_instance.set_players(self.black_player_id, self.white_player_id)

            elif self.mock_game_instance.game_over:
                # ゲームオーバー時
                # 引数を main.py の実装に合わせる (game_over=True)
                restart_rect = self.mock_gui_instance._calculate_button_rect(is_start_button=False, game_over=True, is_reset_button=False, is_quit_button=False)
                reset_rect = self.mock_gui_instance._calculate_button_rect(is_start_button=False, game_over=True, is_reset_button=True, is_quit_button=False)
                quit_rect = self.mock_gui_instance._calculate_button_rect(is_start_button=False, game_over=True, is_reset_button=False, is_quit_button=True)

                if self.mock_gui_instance.is_button_clicked(mouse_click_pos, restart_rect):
                    self.mock_game_instance.reset()
                    self.mock_game_instance.set_players(self.black_player_id, self.white_player_id)
                    self.game_started = True # ゲーム再開
                    self.mock_game_instance.game_over = False # game_over フラグもリセット
                elif self.mock_gui_instance.is_button_clicked(mouse_click_pos, reset_rect):
                    self.mock_game_instance.reset()
                    self.black_player_id = 0
                    self.white_player_id = 0
                    self.mock_game_instance.set_players(self.black_player_id, self.white_player_id)
                    self.game_started = False # 開始前に戻る
                    self.mock_game_instance.game_over = False # game_over フラグもリセット
                elif self.mock_gui_instance.is_button_clicked(mouse_click_pos, quit_rect):
                    self.running = False

            else: # ゲーム中 (game_started=True, game_over=False)
                # 引数を main.py の実装に合わせる (game_over=False)
                restart_rect = self.mock_gui_instance._calculate_button_rect(is_start_button=False, game_over=False, is_reset_button=False, is_quit_button=False)
                reset_rect = self.mock_gui_instance._calculate_button_rect(is_start_button=False, game_over=False, is_reset_button=True, is_quit_button=False)
                quit_rect = self.mock_gui_instance._calculate_button_rect(is_start_button=False, game_over=False, is_reset_button=False, is_quit_button=True)

                if self.mock_gui_instance.is_button_clicked(mouse_click_pos, restart_rect):
                    self.mock_game_instance.reset()
                    self.mock_game_instance.set_players(self.black_player_id, self.white_player_id)
                    self.game_started = True # 状態維持 (リスタートなので)
                elif self.mock_gui_instance.is_button_clicked(mouse_click_pos, reset_rect):
                    self.mock_game_instance.reset()
                    self.black_player_id = 0
                    self.white_player_id = 0
                    self.mock_game_instance.set_players(self.black_player_id, self.white_player_id)
                    self.game_started = False # 開始前に戻る
                elif self.mock_gui_instance.is_button_clicked(mouse_click_pos, quit_rect):
                    self.running = False
                # 人間の手番の場合、セルクリックを処理
                elif self.mock_game_instance.agents[self.mock_game_instance.turn] is None:
                    row, col = self.mock_gui_instance.get_clicked_cell(mouse_click_pos)
                    valid_moves = self.mock_game_instance.get_valid_moves()
                    if (row, col) in valid_moves:
                        # place_stone が成功したらターン交代などを行う
                        if self.mock_game_instance.place_stone(row, col):
                            self.mock_game_instance.set_message("")
                            self.mock_game_instance.switch_turn()
                            self.mock_game_instance.check_game_over()
                        # else: # place_stone が False を返した場合の処理 (main.py に依存)
                            # 必要ならエラーメッセージ表示など
                            # self.mock_game_instance.set_message("Invalid move (returned False)")

        # --- 状態更新 (AIの手番、パス) ---
        # AI/パス処理はゲーム中のみ
        if self.game_started and not self.mock_game_instance.game_over:
            current_turn = self.mock_game_instance.turn
            current_agent = self.mock_game_instance.agents[current_turn]
            valid_moves = self.mock_game_instance.get_valid_moves()

            if not valid_moves:
                # パス処理
                # 相手もパスかチェックするためにターンを切り替える前にメッセージ設定
                self.mock_game_instance.set_message(f"{'Black' if current_turn == -1 else 'White'} passed.")
                self.mock_game_instance.switch_turn()
                # 相手の有効手を取得
                opponent_valid_moves = self.mock_game_instance.get_valid_moves()
                if not opponent_valid_moves:
                    # 相手もパスならゲームオーバー
                    self.mock_game_instance.game_over = True
                    self.mock_game_instance.set_message("Both players passed. Game over.")
                # else: # 相手に手があれば、相手のターンへ (メッセージはそのまま)
                    # pass
            elif current_agent is not None:
                # AIの手番
                move = current_agent.play(self.mock_game_instance)
                if move and move in valid_moves:
                    if self.mock_game_instance.place_stone(move[0], move[1]):
                        self.mock_game_instance.set_message("") # AIが打ったらメッセージクリア
                        self.mock_game_instance.switch_turn()
                        self.mock_game_instance.check_game_over()
                    # else: # AI の place_stone が False を返すケース (通常はないはずだが)
                        # self.mock_logging.warning(f"AI returned valid move {move} but place_stone failed.")
                        # self.mock_game_instance.set_message("AI Error: Invalid move.")
                else:
                    # AI が無効な手や None を返した場合
                    self.mock_logging.warning(f"AI agent for {'Black' if current_turn == -1 else 'White'} returned invalid move: {move}. Valid moves: {valid_moves}")
                    # エラーメッセージを表示
                    self.mock_game_instance.set_message("AI Error: Invalid move returned.")
                    # self.running = False # エラーで終了させる場合

        # --- 描画処理 ---
        # 描画処理はループの最後に必ず行われる
        self.mock_gui_instance.screen.fill(ANY) # 背景色で塗りつぶし
        player_settings_top = self.mock_gui_instance._calculate_player_settings_top()

        if not self.game_started:
            # ゲーム開始前
            self.mock_gui_instance.draw_board(self.mock_game_instance)
            self.mock_gui_instance.draw_start_button()
            self.mock_gui_instance.draw_player_settings(self.mock_game_instance, player_settings_top, enabled=True)
        elif self.mock_game_instance.game_over:
            # ゲームオーバー時
            winner = self.mock_game_instance.get_winner()
            # 勝敗メッセージ取得 (simulate内で設定されているはず -> get_message() で取得)
            message = self.mock_game_instance.get_message()
            # 描画
            self.mock_gui_instance.draw_board(self.mock_game_instance)
            # is_game_over=True を draw_message に渡す
            self.mock_gui_instance.draw_message(message, is_game_over=True)
            # ゲームオーバー時はプレイヤー設定は操作不可
            self.mock_gui_instance.draw_player_settings(self.mock_game_instance, player_settings_top, enabled=False)
            self.mock_gui_instance.draw_restart_button(game_over=True)
            self.mock_gui_instance.draw_reset_button(game_over=True)
            self.mock_gui_instance.draw_quit_button(game_over=True)
        else:
            # ゲーム中
            self.mock_gui_instance.draw_board(self.mock_game_instance)
            # 人間の手番なら有効手を表示
            if self.mock_game_instance.agents[self.mock_game_instance.turn] is None:
                self.mock_gui_instance.draw_valid_moves(self.mock_game_instance)
            self.mock_gui_instance.draw_turn_message(self.mock_game_instance)
            self.mock_gui_instance.draw_restart_button(game_over=False)
            self.mock_gui_instance.draw_reset_button(game_over=False)
            self.mock_gui_instance.draw_quit_button(game_over=False)
            # 通常のメッセージ表示 (パスなど -> get_message() で取得)
            self.mock_gui_instance.draw_message(self.mock_game_instance.get_message())
            # ゲーム中はプレイヤー設定は操作不可
            self.mock_gui_instance.draw_player_settings(self.mock_game_instance, player_settings_top, enabled=False)

        # 画面更新
        self.mock_pygame.display.flip()
        # FPS 制御
        self.mock_pygame.time.Clock().tick(60) # main.py に合わせる


    # --- テストケース (変更なしのテストは省略) ---

    def test_initialization(self):
        """main 関数冒頭の初期化処理が正しく呼ばれるか"""
        self.mock_pygame.init.assert_called_once()
        self.MockGame.assert_called_once_with()
        self.MockGameGUI.assert_called_once_with()
        self.mock_logging.basicConfig.assert_called_once_with(level=ANY, format=ANY)
        # setUp 内で set_players が呼ばれる
        self.mock_game_instance.set_players.assert_called_with(0, 0)
        self.assertEqual(self.mock_game_instance.set_players.call_count, 1)
        # setUp 内で set_message("") が呼ばれる
        self.mock_game_instance.set_message.assert_called_with("")
        self.assertEqual(self.mock_game_instance.set_message.call_count, 1)
        self.mock_pygame.time.Clock.assert_called_once()

    # ... (他のテストケースは変更なし) ...

    def test_drawing_game_over(self):
        """ゲームオーバー時の描画呼び出し"""
        self.game_started = True
        self.mock_game_instance.game_over = True
        player_settings_top = 500
        self.mock_gui_instance._calculate_player_settings_top.return_value = player_settings_top
        self.mock_game_instance.get_winner.return_value = -1 # 黒勝ち
        expected_message = "Game Over Message"
        # ★ get_message.return_value の代わりに set_message を使う
        # self.mock_game_instance.get_message.return_value = expected_message
        self.mock_game_instance.set_message(expected_message) # 事前にメッセージを設定

        # 描画メソッドの呼び出し回数をリセット
        self.mock_gui_instance.reset_mock()
        self.mock_pygame.display.flip.reset_mock()

        self.simulate_main_loop_iteration()

        self.mock_gui_instance.draw_board.assert_called_once_with(self.mock_game_instance)
        # get_message() が expected_message を返すはず
        self.mock_gui_instance.draw_message.assert_called_once_with(expected_message, is_game_over=True)
        self.mock_gui_instance.draw_player_settings.assert_called_once_with(self.mock_game_instance, player_settings_top, enabled=False)
        self.mock_gui_instance.draw_restart_button.assert_called_once_with(game_over=True)
        self.mock_gui_instance.draw_reset_button.assert_called_once_with(game_over=True)
        self.mock_gui_instance.draw_quit_button.assert_called_once_with(game_over=True)
        self.mock_gui_instance.draw_turn_message.assert_not_called()
        self.mock_gui_instance.draw_valid_moves.assert_not_called()
        self.mock_gui_instance.draw_start_button.assert_not_called()
        self.mock_pygame.display.flip.assert_called_once()

    def test_drawing_in_game_human(self):
        """ゲーム中 (人間) の描画呼び出し"""
        self.game_started = True
        self.mock_game_instance.game_over = False
        self.mock_game_instance.turn = -1 # 人間の番
        self.mock_game_instance.agents = {-1: None, 1: None}
        player_settings_top = 500
        self.mock_gui_instance._calculate_player_settings_top.return_value = player_settings_top
        current_message = "Test Message"
        # ★ get_message.return_value の代わりに set_message を使う
        # self.mock_game_instance.get_message.return_value = current_message
        self.mock_game_instance.set_message(current_message) # 事前にメッセージを設定
        self.mock_game_instance.get_valid_moves.return_value = [(1,2)]

        # 描画メソッドの呼び出し回数をリセット
        self.mock_gui_instance.reset_mock()
        self.mock_pygame.display.flip.reset_mock()

        self.simulate_main_loop_iteration()

        self.mock_gui_instance.draw_board.assert_called_once_with(self.mock_game_instance)
        self.mock_gui_instance.draw_valid_moves.assert_called_once_with(self.mock_game_instance)
        self.mock_gui_instance.draw_turn_message.assert_called_once_with(self.mock_game_instance)
        self.mock_gui_instance.draw_restart_button.assert_called_once_with(game_over=False)
        self.mock_gui_instance.draw_reset_button.assert_called_once_with(game_over=False)
        self.mock_gui_instance.draw_quit_button.assert_called_once_with(game_over=False)
        # get_message() が current_message を返すはず
        self.mock_gui_instance.draw_message.assert_called_once_with(current_message)
        self.mock_gui_instance.draw_player_settings.assert_called_once_with(self.mock_game_instance, player_settings_top, enabled=False)
        self.mock_gui_instance.draw_start_button.assert_not_called()
        self.mock_pygame.display.flip.assert_called_once()

    def test_drawing_in_game_ai(self):
        """ゲーム中 (AI) の描画呼び出し"""
        self.game_started = True
        self.mock_game_instance.game_over = False
        self.mock_game_instance.turn = 1 # AIの番
        mock_ai_agent = MagicMock()
        ai_move = (3,4)
        mock_ai_agent.play.return_value = ai_move
        self.mock_game_instance.agents = {-1: None, 1: mock_ai_agent}
        player_settings_top = 500
        self.mock_gui_instance._calculate_player_settings_top.return_value = player_settings_top
        # ★ get_message.return_value の代わりに set_message を使う
        # current_message = "AI Thinking..." # 不要
        # self.mock_game_instance.get_message.return_value = current_message # 不要
        self.mock_game_instance.set_message("AI Thinking...") # 事前にメッセージを設定

        self.mock_game_instance.get_valid_moves.return_value = [ai_move]
        self.mock_game_instance.place_stone.return_value = True

        # 描画メソッドの呼び出し回数をリセット
        self.mock_gui_instance.reset_mock()
        self.mock_pygame.display.flip.reset_mock()

        # AIターンをシミュレート
        self.simulate_main_loop_iteration()

        # --- アサーション ---
        self.mock_gui_instance.draw_board.assert_called_once_with(self.mock_game_instance)
        self.mock_gui_instance.draw_valid_moves.assert_not_called()
        self.mock_gui_instance.draw_turn_message.assert_called_once_with(self.mock_game_instance)
        self.mock_gui_instance.draw_restart_button.assert_called_once_with(game_over=False)
        self.mock_gui_instance.draw_reset_button.assert_called_once_with(game_over=False)
        self.mock_gui_instance.draw_quit_button.assert_called_once_with(game_over=False)

        # ★ AI処理後にメッセージが "" に設定され、それが描画されることを確認
        # simulate_main_loop_iteration 内で set_message("") が呼ばれ、
        # その後の描画処理で get_message() が "" を返すはず。
        self.mock_gui_instance.draw_message.assert_called_once_with("")

        self.mock_gui_instance.draw_player_settings.assert_called_once_with(self.mock_game_instance, player_settings_top, enabled=False)
        self.mock_pygame.display.flip.assert_called_once()


if __name__ == '__main__':
    unittest.main(verbosity=2)

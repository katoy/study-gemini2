import unittest
from unittest.mock import MagicMock, patch
import pygame
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import main
from game import Game
from gui import GameGUI

class TestApp(unittest.TestCase):

    def setUp(self):
        """各テストメソッドの前に実行"""
        # Pygameの初期化、Game、GameGUIのモックを作成
        self.mock_game = MagicMock(spec=Game)
        self.mock_gui = MagicMock(spec=GameGUI)
        
        # モックに必要な属性とメソッドを追加
        self.mock_game.turn = -1
        self.mock_game.game_over = False
        self.mock_game.is_ai_turn = MagicMock(return_value=False)
        self.mock_game.should_pass = MagicMock(return_value=False)
        self.mock_game.is_human_turn = MagicMock(return_value=True)
        self.mock_game.make_move = MagicMock(return_value=True)
        self.mock_game.make_ai_move = MagicMock()
        self.mock_game.pass_turn = MagicMock()
        self.mock_game.agents = {-1: None, 1: None}
        
        self.mock_gui.screen = MagicMock(spec=pygame.Surface)
        self.mock_gui.get_board_click_pos = MagicMock(return_value=None)
        self.mock_gui.get_clicked_cell = MagicMock(return_value=(0, 0))
        self.mock_gui.draw_game_over = MagicMock()
        self.mock_gui._calculate_player_settings_top = MagicMock(return_value=400)
        self.mock_gui.is_start_button_clicked = MagicMock(return_value=False)
        self.mock_gui.is_restart_button_clicked = MagicMock(return_value=False)
        self.mock_gui.is_reset_button_clicked = MagicMock(return_value=False)
        self.mock_gui.is_quit_button_clicked = MagicMock(return_value=False)
        self.mock_gui.is_settings_button_clicked = MagicMock(return_value=False)

        pygame.init()
        # display.set_mode を呼ばないと flip で落ちる場合があるため、パッチを検討
        self.patcher_flip = patch('pygame.display.flip')
        self.mock_flip = self.patcher_flip.start()

        # Appインスタンスを作成
        self.app = main.App(self.mock_game, self.mock_gui)

    def tearDown(self):
        self.patcher_flip.stop()

    def test_run(self):
        """runメソッドのテスト"""
        # 実行フラグをFalseに設定してループを終了させる
        self.app.running = False

        # sys.exit() が呼ばれるのを防ぐために、モックする
        with patch('sys.exit') as mock_sys_exit:
            # runメソッドを実行
            self.app.run()

            # sys.exit() が呼ばれたか確認
            mock_sys_exit.assert_called_once()

    def test_handle_events(self):
        """_handle_eventsメソッドのテスト"""
        # QUITイベントを発生させる
        event_quit = pygame.event.Event(pygame.QUIT)

        # pygame.event.get()の戻り値をモック
        with patch('pygame.event.get', return_value=[event_quit]):
            # 実行フラグをTrueに設定
            self.app.running = True

            # _handle_eventsメソッドを実行
            result = self.app._handle_events()

            # 実行フラグがFalseになったか確認
            self.assertEqual(self.app.running, False)
            # マウスクリック位置が返されたか確認
            self.assertIsNone(result)

    @patch('sys.exit')
    def test_handle_events_no_quit(self, mock_sys_exit):
        """_handle_eventsメソッドのテスト (QUITイベントなし)"""
        # MOUSEBUTTONDOWNイベントを発生させる
        event_mouse = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': (100, 200)})

        # pygame.event.get()の戻り値をモック (QUITイベントなし)
        with patch('pygame.event.get', return_value=[event_mouse]):
            # _handle_eventsメソッドを実行
            result = self.app._handle_events()

            # 実行フラグがTrueのままか確認
            self.assertEqual(self.app.running, True)
            # マウスクリック位置が返されたか確認
            self.assertEqual(result, (100, 200))

    def test_update_state_before_start(self):
        """ゲーム開始前の _update_state のテスト"""
        self.app.game_started = False
        with patch.object(self.app, '_handle_click_before_start') as mock_handle:
            self.app._update_state((100, 100))
            mock_handle.assert_called_once_with((100, 100))

    def test_update_state_game_over(self):
        """ゲームオーバー時の _update_state のテスト"""
        self.app.game_started = True
        self.mock_game.game_over = True
        with patch.object(self.app, '_handle_click_game_over') as mock_handle:
            self.app._update_state((100, 100))
            mock_handle.assert_called_once_with((100, 100))

    def test_update_state_in_game(self):
        """ゲーム中の _update_state のテスト"""
        self.app.game_started = True
        self.mock_game.game_over = False
        with patch.object(self.app, '_handle_click_in_game') as mock_handle:
            self.app._update_state((100, 100))
            mock_handle.assert_called_once_with((100, 100))

    def test_handle_click_before_start_start_button(self):
        """ゲーム開始前のスタートボタンクリック"""
        self.mock_gui.is_start_button_clicked.return_value = True
        self.app._handle_click_before_start((100, 100))
        self.assertTrue(self.app.game_started)

    def test_handle_click_before_start_radio_button(self):
        """ゲーム開始前のラジオボタンクリック"""
        self.mock_gui.is_start_button_clicked.return_value = False
        self.mock_gui._calculate_player_settings_top.return_value = 400
        # 黒プレイヤーを ID=1 に変更
        self.mock_gui.get_clicked_radio_button.return_value = (-1, 1)
        self.app._handle_click_before_start((100, 450))
        self.assertEqual(self.app.black_player_id, 1)
        self.mock_game.set_players.assert_called_with(1, 0)

    def test_handle_click_game_over_restart(self):
        """ゲームオーバー時のリスタートボタンクリック"""
        self.mock_gui.is_restart_button_clicked.return_value = True
        self.app._handle_click_game_over((100, 100))
        self.mock_game.reset.assert_called_once()
        self.assertTrue(self.app.game_started)

    def test_handle_click_game_over_reset(self):
        """ゲームオーバー時のリセットボタンクリック"""
        self.mock_gui.is_restart_button_clicked.return_value = False
        self.mock_gui.is_reset_button_clicked.return_value = True
        self.app._handle_click_game_over((100, 100))
        self.mock_game.reset.assert_called_once()
        self.assertFalse(self.app.game_started)
        self.assertEqual(self.app.black_player_id, 0)

    def test_handle_click_game_over_quit(self):
        """ゲームオーバー時の終了ボタンクリック"""
        self.mock_gui.is_restart_button_clicked.return_value = False
        self.mock_gui.is_reset_button_clicked.return_value = False
        self.mock_gui.is_quit_button_clicked.return_value = True
        self.app._handle_click_game_over((100, 100))
        self.assertFalse(self.app.running)

    def test_handle_click_in_game_restart(self):
        """ゲーム中のリスタートボタンクリック"""
        self.mock_gui.is_restart_button_clicked.return_value = True
        self.app._handle_click_in_game((100, 100))
        self.mock_game.reset.assert_called_once()

    def test_handle_click_in_game_board(self):
        """ゲーム中の盤面クリック"""
        self.mock_gui.is_restart_button_clicked.return_value = False
        self.mock_gui.is_reset_button_clicked.return_value = False
        self.mock_gui.is_quit_button_clicked.return_value = False
        self.mock_gui.get_clicked_cell.return_value = (3, 3)
        self.mock_game.is_human_turn.return_value = True
        self.mock_game.get_valid_moves.return_value = [(3, 3)]
        self.mock_game.place_stone.return_value = True

        self.app._handle_click_in_game((100, 100))
        self.mock_game.place_stone.assert_called_with(3, 3)

    def test_handle_ai_or_pass(self):
        """AI手番とパス処理のテスト"""
        self.app.game_started = True
        self.mock_game.game_over = False
        self.mock_game.turn = -1
        mock_agent = MagicMock()
        self.mock_game.agents = {-1: mock_agent, 1: None}
        self.mock_game.get_valid_moves.return_value = [(3, 3)]
        mock_agent.play.return_value = (3, 3)
        self.mock_game.place_stone.return_value = True

        self.app._handle_ai_or_pass()
        self.mock_game.place_stone.assert_called_with(3, 3)

        # パス処理のテスト
        self.mock_game.get_valid_moves.return_value = []
        self.app._handle_ai_or_pass()
        self.mock_game.switch_turn.assert_called()

    def test_render_before_start(self):
        """開始前の描画テスト"""
        self.app.game_started = False
        self.app._render()
        self.mock_gui.draw_board.assert_called()
        self.mock_gui.draw_player_settings.assert_called()
        self.mock_gui.draw_start_button.assert_called()
        self.mock_flip.assert_called()

    def test_render_in_game(self):
        """ゲーム中の描画テスト"""
        self.app.game_started = True
        self.mock_game.game_over = False
        self.app._render()
        self.mock_gui.draw_board.assert_called()
        self.mock_gui.draw_turn_message.assert_called()
        self.mock_gui.draw_restart_button.assert_called_with(game_over=False)
        self.mock_flip.assert_called()

    def test_handle_click_game_over_reset_all(self):
        """ゲームオーバー時のリセットボタンクリック (詳細)"""
        self.mock_gui.is_restart_button_clicked.return_value = False
        self.mock_gui.is_reset_button_clicked.return_value = True
        self.app.black_player_id = 1
        self.app.white_player_id = 2
        self.app._handle_click_game_over((100, 100))
        self.assertEqual(self.app.black_player_id, 0)
        self.assertEqual(self.app.white_player_id, 0)
        self.assertFalse(self.app.game_started)

    def test_handle_ai_or_pass_double_pass(self):
        """ダブルパスによるゲームオーバーのテスト"""
        self.app.game_started = True
        self.mock_game.game_over = False
        self.mock_game.get_valid_moves.side_effect = [[], []] # 自分も相手もパス
        self.app._handle_ai_or_pass()
        self.assertTrue(self.mock_game.game_over)

    def test_handle_click_in_game_restart_button(self):
        """ゲーム中のリスタートボタンクリック"""
        self.mock_gui.is_restart_button_clicked.return_value = True
        self.app._handle_click_in_game((100, 100))
        self.mock_game.reset.assert_called_once()
        self.assertTrue(self.app.game_started)

    def test_handle_click_in_game_reset_button(self):
        """ゲーム中のリセットボタンクリック"""
        self.mock_gui.is_restart_button_clicked.return_value = False
        self.mock_gui.is_reset_button_clicked.return_value = True
        self.app._handle_click_in_game((100, 100))
        self.mock_game.reset.assert_called_once()
        self.assertFalse(self.app.game_started)

    def test_handle_click_in_game_quit_button(self):
        """ゲーム中の終了ボタンクリック"""
        self.mock_gui.is_restart_button_clicked.return_value = False
        self.mock_gui.is_reset_button_clicked.return_value = False
        self.mock_gui.is_quit_button_clicked.return_value = True
        self.app._handle_click_in_game((100, 100))
        self.assertFalse(self.app.running)

    def test_handle_click_in_game_settings_button(self):
        """ゲーム中の設定ボタンクリック"""
        self.mock_gui.is_restart_button_clicked.return_value = False
        self.mock_gui.is_reset_button_clicked.return_value = False
        self.mock_gui.is_quit_button_clicked.return_value = False
        self.mock_gui.is_settings_button_clicked.return_value = True
        self.app._handle_click_in_game((100, 100))
        # 現状、ログ出力のみ
        
    def test_render_winner_white(self):
        """白の勝ちの描画テスト"""
        self.app.game_started = True
        self.mock_game.game_over = True
        self.mock_game.get_winner.return_value = 1
        self.app._render()
        self.mock_game.set_message.assert_called_with("白の勝ちです！")

    def test_handle_click_before_start_radio_button_no_change(self):
        """プレイヤー選択ラジオボタンのクリック (変更なし)"""
        self.mock_gui.is_start_button_clicked.return_value = False
        self.mock_gui.get_clicked_radio_button.return_value = (-1, 0)
        self.app.black_player_id = 0
        self.app._handle_click_before_start((100, 450))
        self.assertEqual(self.app.black_player_id, 0)

    def test_handle_click_before_start_radio_button_white(self):
        """白プレイヤー選択ラジオボタンのクリック"""
        self.mock_gui.is_start_button_clicked.return_value = False
        self.mock_gui.get_clicked_radio_button.return_value = (1, 1)
        self.app.white_player_id = 0
        self.app._handle_click_before_start((100, 450))
        self.assertEqual(self.app.white_player_id, 1)

    def test_handle_ai_move_unexpected_failure(self):
        """AI手番での予期しない place_stone の失敗"""
        self.app.game_started = True
        mock_agent = MagicMock()
        self.mock_game.get_valid_moves.return_value = [(3, 3)]
        mock_agent.play.return_value = (3, 3)
        self.mock_game.place_stone.return_value = False
        with patch('main.logging.error') as mock_log_error:
            self.app._handle_ai_move(mock_agent, [(3, 3)])
            mock_log_error.assert_called()

class TestMainFunction(unittest.TestCase):
    @patch('main.App')
    @patch('main.GameGUI')
    @patch('main.Game')
    @patch('main.pygame')
    def test_main(self, mock_pygame, mock_game, mock_gui, mock_app):
        """main関数のテスト"""
        # main関数を実行
        main.main()

        # 各インスタンスが生成されたか確認
        mock_game.assert_called_once()
        mock_gui.assert_called_once()
        mock_app.assert_called_once()
        mock_app_instance = mock_app.return_value
        mock_app_instance.run.assert_called_once()

if __name__ == '__main__':
    unittest.main(verbosity=2)

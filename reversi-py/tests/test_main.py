import unittest
from unittest.mock import MagicMock, patch
import pygame
import sys
import os

# プロジェクトルートへのパスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# テスト対象と依存モジュール
import main
from game import Game
from gui import GameGUI

class TestApp(unittest.TestCase):

    def setUp(self):
        """各テストメソッドの前に実行"""
        # Pygameの初期化、Game、GameGUIのモックを作成
        self.mock_pygame = MagicMock()
        self.mock_game = MagicMock(spec=Game)
        self.mock_gui = MagicMock(spec=GameGUI)

        pygame.init()

        # Appインスタンスを作成
        self.app = main.App(self.mock_game, self.mock_gui)

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

    @unittest.skip("スキップ")
    def test_handle_events(self):
        """_handle_eventsメソッドのテスト"""
        # QUITイベントを発生させる
        event_quit = pygame.event.Event(pygame.QUIT)

        # pygame.event.get()の戻り値を設定
        self.mock_pygame.event.get.return_value = [event_quit]

        # 実行フラグをTrueに設定
        self.app.running = True

        # _handle_eventsメソッドを実行
        result = self.app._handle_events()

        # 実行フラグがFalseになったか確認
        self.assertEqual(self.app.running, False)
        # マウスクリック位置が返されたか確認
        self.assertIsNone(result)

    @unittest.skip("スキップ")
    @patch('sys.exit')
    def test_handle_events_no_quit(self, mock_sys_exit):
        """_handle_eventsメソッドのテスト (QUITイベントなし)"""
        # MOUSEBUTTONDOWNイベントを発生させる
        event_mouse = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': (100, 200)})

        # pygame.event.get()の戻り値を設定 (QUITイベントなし)
        self.mock_pygame.event.get.return_value = [event_mouse]

        # _handle_eventsメソッドを実行
        result = self.app._handle_events()

        # 実行フラグがTrueのままか確認
        self.assertEqual(self.app.running, True)
        # マウスクリック位置が返されたか確認
        self.assertEqual(result, (100, 200))

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

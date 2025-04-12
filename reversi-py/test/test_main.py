# test/test_main.py
import unittest
from unittest.mock import patch, MagicMock, call
import pygame
import sys
import os

# プロジェクトルートへのパスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# テスト対象の main モジュール（関数自体は呼び出さない）
import main

# 依存するクラスや定数をインポート (モックまたは実際の値を使用)
from game import Game
from gui import GameGUI # GUI のレイアウト計算メソッドを使うためインポート
from config.theme import Screen, Color
# config.agents は main モジュール内で import されているものを patch する

# --- Pygame の初期化と終了をクラスレベルで行う ---
# @classmethod # <<< クラスの外側にあるため削除
# def setUpClass(cls):
#     pygame.display.init()
#     cls.screen = pygame.display.set_mode((Screen.WIDTH, Screen.HEIGHT))

# @classmethod # <<< クラスの外側にあるため削除
# def tearDownClass(cls):
#     pygame.display.quit()
# -------------------------------------------------

class TestMainEventHandling(unittest.TestCase):
    """main.py のイベント処理ロジック（特にラジオボタン）をテストする"""

    # --- クラスメソッドをクラス内に移動 ---
    @classmethod
    def setUpClass(cls):
        # Pygame の display モジュールだけ初期化 (イベント等はモックする)
        pygame.display.init()
        cls.screen = pygame.display.set_mode((Screen.WIDTH, Screen.HEIGHT))

    @classmethod
    def tearDownClass(cls):
        pygame.display.quit()
    # ------------------------------------

    def setUp(self):
        # テスト用の Game と GameGUI インスタンスを作成
        # GameGUI はレイアウト計算のために実際のインスタンスを使う
        self.gui = GameGUI()
        # Game は set_players メソッドをモックするために MagicMock を使う
        self.game = MagicMock(spec=Game)
        # GameGUI の screen 属性を設定
        # クラス変数 screen を参照 (TestMainEventHandling.screen または self.__class__.screen)
        self.gui.screen = TestMainEventHandling.screen
        # GameGUI のフォントもモックしておく (レイアウト計算に影響しないように)
        font_mock = MagicMock(spec=pygame.font.Font)
        font_mock.get_height.return_value = 24 # 適当な高さ
        self.gui.font = font_mock

        # テスト用のエージェントオプション
        self.test_agent_options = [
            (0, '人間'),
            (1, 'First'),
            (2, 'Random'),
            (3, 'Gain'),
            (4, 'MCTS')
        ]
        # main モジュール内の get_agent_options をパッチ
        self.patcher_get_options = patch('main.get_agent_options', return_value=self.test_agent_options)
        self.mock_get_options = self.patcher_get_options.start()
        self.addCleanup(self.patcher_get_options.stop)

        # main 関数内の変数を初期化
        self.black_player_type = 0
        self.white_player_type = 0
        self.game_started = False
        self.radio_button_size = Screen.RADIO_BUTTON_SIZE

    # ... (simulate_click とテストメソッドは変更なし) ...

if __name__ == '__main__':
    unittest.main()

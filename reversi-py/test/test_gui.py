# test/test_gui.py
import unittest
import pygame
from unittest.mock import MagicMock, patch, call # call をインポート
import sys
import os

# プロジェクトルートへのパスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from gui import GameGUI


from config.theme import Color, Screen
from game import Game
# テスト対象のモジュールが依存するクラスをインポート (isinstance チェック用)
from agents import FirstAgent, RandomAgent

class TestGameGUI(unittest.TestCase):

    # --- クラスメソッドをクラス内に移動 ---
    @classmethod
    def setUpClass(cls):
        pygame.init()
        # テスト用のスクリーンを作成 (実際の描画は行わないことが多いが、一部テストで必要)
        cls.screen = pygame.display.set_mode((Screen.WIDTH, Screen.HEIGHT))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        # 各テストメソッドの前に実行
        self.gui = GameGUI()
        self.game = Game()
        self.gui.screen = self.__class__.screen

        # --- フォントのモック ---
        self.font_mock = MagicMock(spec=pygame.font.Font)
        # render が実際の Surface を返すように設定 (blit でエラーにならないように)
        real_surface = pygame.Surface((10, 10))
        self.font_mock.render.return_value = real_surface
        # get_height はレイアウト計算に必要
        self.font_mock.get_height.return_value = 24
        self.gui.font = self.font_mock
        # -----------------------

        # --- config.agents のモック設定 ---
        # テスト用のエージェントオプション
        self.test_agent_options = [
            (0, '人間'),
            (1, 'First'),
            (2, 'Random')
        ]
        # get_agent_options がテスト用オプションを返すようにモック
        # gui モジュール内の get_agent_options をパッチする
        self.patcher_get_options = patch('gui.get_agent_options', return_value=self.test_agent_options)
        self.mock_get_options = self.patcher_get_options.start()
        self.addCleanup(self.patcher_get_options.stop) # テスト終了時にパッチを解除

        # get_agent_class が ID に応じてクラスを返すようにモック
        # gui モジュール内の get_agent_class をパッチする
        def mock_get_class(agent_id):
            if agent_id == 0: return None
            if agent_id == 1: return FirstAgent
            if agent_id == 2: return RandomAgent
            return None
        self.patcher_get_class = patch('gui.get_agent_class', side_effect=mock_get_class)
        self.mock_get_class = self.patcher_get_class.start()
        self.addCleanup(self.patcher_get_class.stop)

        # GUIインスタンスの agent_options をモックされた値で上書き
        # (setUp で GameGUI が初期化された後にモックを適用するため)
        self.gui.agent_options = self.test_agent_options

    # === ロジック系のテスト (維持・修正) ===

    def test_draw_message_calls_render(self):
        """draw_message が font.render を正しく呼び出すか"""
        self.gui.draw_message("Test Message")
        self.font_mock.render.assert_called_once_with("Test Message", True, Color.WHITE)

    def test_draw_message_game_start_calls_render(self):
        self.gui.draw_message("Test Message", is_game_start=True)
        self.font_mock.render.assert_called_once_with("Test Message", True, Color.WHITE)

    def test_draw_message_game_over_calls_render(self):
        self.gui.draw_message("Test Message", is_game_over=True)
        self.font_mock.render.assert_called_once_with("Test Message", True, Color.WHITE)

    def test_get_clicked_cell(self):
        """get_clicked_cell が正しいセル座標を返すか"""
        cell_size = Screen.CELL_SIZE
        board_left = (Screen.WIDTH - Screen.BOARD_SIZE) // 2
        board_top = Screen.BOARD_TOP_MARGIN
        # セル (4, 3) の中心付近をクリック
        click_x = board_left + cell_size * 3 + cell_size // 2
        click_y = board_top + cell_size * 4 + cell_size // 2
        row, col = self.gui.get_clicked_cell((click_x, click_y))
        self.assertEqual(row, 4)
        self.assertEqual(col, 3)
        # 盤面外をクリック
        row, col = self.gui.get_clicked_cell((0, 0))
        self.assertEqual(row, -1)
        self.assertEqual(col, -1)

    def test_is_button_clicked(self):
        """is_button_clicked が正しく判定するか"""
        button_rect = pygame.Rect(100, 100, 50, 50)
        self.assertTrue(self.gui.is_button_clicked((125, 125), button_rect))
        self.assertFalse(self.gui.is_button_clicked((50, 50), button_rect))
        self.assertFalse(self.gui.is_button_clicked((125, 125), None)) # Rect が None の場合

    # === レイアウト計算系のテスト (維持・修正) ===

    def test_get_message_y_position(self):
        """_get_message_y_position が妥当な値を返すか"""
        y_pos = self.gui._get_message_y_position(False, False)
        self.assertIsInstance(y_pos, (int, float))
        self.assertGreater(y_pos, 0)

    def test_get_message_y_position_game_start(self):
        y_pos = self.gui._get_message_y_position(True, False)
        self.assertEqual(y_pos, Screen.GAME_START_MESSAGE_TOP_MARGIN)

    def test_get_message_y_position_game_over(self):
        y_pos = self.gui._get_message_y_position(False, True)
        self.assertIsInstance(y_pos, (int, float))
        self.assertGreater(y_pos, 0)
        # ゲームオーバー時は手番表示と同じY座標になるはず
        expected_y = self.gui._calculate_turn_message_center_y()
        self.assertEqual(y_pos, expected_y)

    def test_calculate_button_rect_start_button(self):
        rect = self.gui._calculate_button_rect(True)
        self.assertIsInstance(rect, pygame.Rect)

    def test_calculate_button_rect_restart_button(self):
        rect = self.gui._calculate_button_rect(False)
        self.assertIsInstance(rect, pygame.Rect)

    def test_calculate_button_rect_reset_button(self):
        rect = self.gui._calculate_button_rect(False, is_reset_button=True)
        self.assertIsInstance(rect, pygame.Rect)

    def test_calculate_button_rect_game_over(self):
        rect = self.gui._calculate_button_rect(False, game_over=True)
        self.assertIsInstance(rect, pygame.Rect)

    def test_load_font(self):
        # setUp でモックしているので、ここではモックが設定されているか確認
        self.assertIsNotNone(self.gui.font)
        self.assertIsInstance(self.gui.font, MagicMock)

    # === 新しいロジックのテスト ===

    @patch('gui.GameGUI.draw_radio_button')
    @patch('gui.GameGUI._draw_text_with_position')
    def test_draw_player_settings_calls_draw_methods(self, mock_draw_text, mock_draw_radio):
        """draw_player_settings がラジオボタンとテキスト描画関数を正しく呼び出すか"""
        # テスト用のゲーム状態設定
        self.game.agents[-1] = None # 黒: 人間
        self.game.agents[1] = FirstAgent() # 白: FirstAgent

        player_settings_top = 100 # 適当な値
        enabled = True

        self.gui.draw_player_settings(self.game, player_settings_top, enabled)

        # 描画関数が呼ばれた回数を確認 (エージェント数 * 2プレイヤー分)
        expected_calls = len(self.test_agent_options) * 2
        self.assertEqual(mock_draw_radio.call_count, expected_calls)
        # ラベル描画(2回) + ラジオボタン横テキスト描画(expected_calls回)
        self.assertEqual(mock_draw_text.call_count, 2 + expected_calls)

        # --- 呼び出し引数の詳細なチェック (例: 黒の人間ラジオボタン) ---
        board_rect = self.gui._calculate_board_rect()
        left_margin = board_rect.left
        radio_y_offset = Screen.RADIO_Y_OFFSET
        radio_y_spacing = Screen.RADIO_Y_SPACING
        radio_text_x_offset = Screen.RADIO_BUTTON_SIZE + Screen.RADIO_BUTTON_MARGIN

        # 黒プレイヤーの最初のラジオボタン (人間, id=0) の期待される引数
        expected_radio_y_human = player_settings_top + radio_y_offset + 0 * radio_y_spacing
        expected_radio_pos_human = (left_margin, expected_radio_y_human)
        expected_text_pos_human = (left_margin + radio_text_x_offset, expected_radio_y_human)

        # 黒が人間なので selected=True
        mock_draw_radio.assert_any_call(expected_radio_pos_human, True, enabled)
        # ラジオボタン横のテキスト描画
        mock_draw_text.assert_any_call('人間', Color.WHITE, expected_text_pos_human)
        # ラベル描画も確認
        mock_draw_text.assert_any_call("黒プレイヤー", Color.WHITE, (left_margin, player_settings_top))


        # --- 呼び出し引数の詳細なチェック (例: 白のFirstAgentラジオボタン) ---
        white_player_label_x = self.gui.screen_width // 2 + Screen.RADIO_BUTTON_MARGIN
        # 白プレイヤーの2番目のラジオボタン (First, id=1) の期待される引数
        expected_radio_y_first = player_settings_top + radio_y_offset + 1 * radio_y_spacing
        expected_radio_pos_first_white = (white_player_label_x, expected_radio_y_first)
        expected_text_pos_first_white = (white_player_label_x + radio_text_x_offset, expected_radio_y_first)

        # 白がFirstAgentなので selected=True
        mock_draw_radio.assert_any_call(expected_radio_pos_first_white, True, enabled)
        # ラジオボタン横のテキスト描画
        mock_draw_text.assert_any_call('First', Color.WHITE, expected_text_pos_first_white)
        # ラベル描画も確認
        mock_draw_text.assert_any_call("白プレイヤー", Color.WHITE, (white_player_label_x, player_settings_top))


        # --- 呼び出し引数の詳細なチェック (例: 黒のRandomラジオボタン - 非選択) ---
        expected_radio_y_random = player_settings_top + radio_y_offset + 2 * radio_y_spacing
        expected_radio_pos_random_black = (left_margin, expected_radio_y_random)
        expected_text_pos_random_black = (left_margin + radio_text_x_offset, expected_radio_y_random)

        # 黒は人間なので selected=False
        mock_draw_radio.assert_any_call(expected_radio_pos_random_black, False, enabled)
        # ラジオボタン横のテキスト描画
        mock_draw_text.assert_any_call('Random', Color.WHITE, expected_text_pos_random_black)


    def test_calculate_player_settings_height(self):
        """_calculate_player_settings_height がエージェント数に基づいて高さを計算するか"""
        font_height = 24 # self.font_mock.get_height.return_value
        num_options = len(self.test_agent_options) # モックされたオプション数 (3)
        # --- 修正: gui.py の _calculate_player_settings_height のロジックに合わせる ---
        # ラベル高さ + オフセット + (ラジオボタン数-1)*間隔 + ラジオボタンサイズ
        # ラジオボタン数は num_options
        expected_height = font_height + Screen.RADIO_Y_OFFSET + Screen.RADIO_Y_SPACING * (num_options - 1) + Screen.RADIO_BUTTON_SIZE

        actual_height = self.gui._calculate_player_settings_height()
        self.assertEqual(actual_height, expected_height)

        # エージェント数が変わった場合もテスト (例: 5個)
        longer_options = [(i, f'Agent{i}') for i in range(5)]
        # gui.get_agent_options のモックの戻り値を変更してテスト
        with patch('gui.get_agent_options', return_value=longer_options):
            # setUp でキャッシュされた値を上書き
            self.gui.agent_options = longer_options
            num_options_longer = len(longer_options)
            # --- 修正: gui.py の _calculate_player_settings_height のロジックに合わせる ---
            expected_height_longer = font_height + Screen.RADIO_Y_OFFSET + Screen.RADIO_Y_SPACING * (num_options_longer - 1) + Screen.RADIO_BUTTON_SIZE
            actual_height_longer = self.gui._calculate_player_settings_height()
            self.assertEqual(actual_height_longer, expected_height_longer)


if __name__ == '__main__':
    unittest.main()

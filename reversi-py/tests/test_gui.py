# tests/test_gui.py
import unittest
import pygame
from unittest.mock import MagicMock, patch, call, ANY # ANY をインポート
import sys
import os
from pathlib import Path # _load_font のテストで使用

# プロジェクトルートへのパスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# テスト対象と依存モジュール
from gui import GameGUI
from config.theme import Color, Screen
from game import Game # Game のモック化のためインポート
from agents.first_agent import FirstAgent # モック用
from agents.random_agent import RandomAgent # モック用
# Button クラスをモック化するためにインポート (元のクラスとして参照)
from ui_elements import Button as OriginalButton

# --- App クラスのテストは test_main.py に移動するため、ここからは削除 ---
# class TestApp(unittest.TestCase):
#    ... (TestApp クラス全体を削除) ...
# --------------------------------------------------------------------

class TestGameGUI(unittest.TestCase): # GameGUI のテストクラスは残す

    @classmethod
    def setUpClass(cls):
        """テストクラス全体で Pygame を初期化"""
        try:
            pygame.init()
            cls.pygame_initialized = True
        except pygame.error as e:
            cls.pygame_initialized = False
            print(f"\nPygame initialization failed in setUpClass: {e}. Skipping GUI tests.", file=sys.stderr)
            # --- 追加: Pygame初期化失敗時にテストをスキップするためのフラグ ---
            cls.skip_tests = True
            cls.skip_reason = f"Pygame initialization failed: {e}"
        else:
            cls.skip_tests = False
            cls.skip_reason = ""
            # --- 追加: フォントの準備 ---
            try:
                cls.OriginalPygameFont = pygame.font.Font # 元のクラスを保持
                # --- 修正: setUpClass ではモックを作らず、クラス参照のみ保持 ---
                # cls.font_mock_for_setup = MagicMock(spec=cls.OriginalPygameFont)
                # dummy_surface = pygame.Surface((10, 10))
                # cls.font_mock_for_setup.render.return_value = dummy_surface
                # cls.font_mock_for_setup.get_height.return_value = 24
                # ----------------------------------------------------------
            except Exception as font_e:
                cls.skip_tests = True
                cls.skip_reason = f"Font setup failed during setUpClass: {font_e}"
            # --------------------------

    @classmethod
    def tearDownClass(cls):
        """テストクラス全体で Pygame を終了"""
        if cls.pygame_initialized:
            pygame.quit()

    def setUp(self):
        """各テストメソッドの前に実行"""
        # --- 修正: setUpClass でスキップ判定 ---
        if self.skip_tests:
            self.skipTest(self.skip_reason)
        # ------------------------------------

        # --- 修正: モック化する前の Font クラスへの参照を保持 ---
        # setUpClass で保持したものを利用
        self.OriginalPygameFont = self.__class__.OriginalPygameFont
        # ----------------------------------------------------

        # --- _load_font のテストのために、GameGUI の初期化前にパッチを適用 ---
        # --- 修正: setUp で毎回新しいモックを作成し、それを返すようにパッチ ---
        self.font_mock = MagicMock(spec=self.OriginalPygameFont)
        self.dummy_surface = MagicMock(spec=pygame.Surface)
        self.dummy_surface.get_rect.return_value = MagicMock(spec=pygame.Rect)
        self.dummy_surface.get_height.return_value = 24
        self.font_mock.render.return_value = self.dummy_surface
        self.font_mock.get_height.return_value = 24

        self.patcher_pygame_font = patch('gui.pygame.font.Font', return_value=self.font_mock)
        self.mock_pygame_font = self.patcher_pygame_font.start()
        self.addCleanup(self.patcher_pygame_font.stop)

        self.patcher_pygame_sysfont = patch('gui.pygame.font.SysFont', return_value=self.font_mock) # SysFont も同じモックを返す
        self.mock_pygame_sysfont = self.patcher_pygame_sysfont.start()
        self.addCleanup(self.patcher_pygame_sysfont.stop)
        # ----------------------------------------------------------------

        self.patcher_path_exists = patch('gui.Path.exists', return_value=True)
        self.mock_path_exists = self.patcher_path_exists.start()
        self.addCleanup(self.patcher_path_exists.stop)

        # ui_elements.Button のモック設定
        self.patcher_button = patch('gui.Button', spec=OriginalButton)
        self.MockButton = self.patcher_button.start()
        self.mock_button_instance = self.MockButton.return_value
        self.mock_button_instance.draw = MagicMock()
        self.mock_button_instance.is_clicked = MagicMock(return_value=False)
        self.addCleanup(self.patcher_button.stop)

        # GameGUI インスタンス生成
        # --- 修正: screen生成をモック化 ---
        # GameGUI の __init__ 内での pygame.display.set_mode をモック
        with patch('gui.pygame.display.set_mode', return_value=MagicMock(spec=pygame.Surface)) as mock_set_mode:
            self.gui = GameGUI()
            # GameGUI 内の screen 属性をモックに差し替え
            self.gui.screen = mock_set_mode.return_value
        # ---------------------------------
        self.gui.screen.get_width.return_value = Screen.WIDTH
        self.gui.screen.get_height.return_value = Screen.HEIGHT
        self.gui.screen_width = Screen.WIDTH
        self.gui.screen_height = Screen.HEIGHT

        # Game インスタンスのモック
        self.game_mock = MagicMock(spec=Game)
        self.game_mock.get_board.return_value = [[0]*8 for _ in range(8)]
        self.game_mock.get_board_size.return_value = 8
        self.game_mock.board = MagicMock()
        self.game_mock.board.count_stones.return_value = (2, 2)
        self.game_mock.get_valid_moves.return_value = []
        self.game_mock.turn = -1
        self.game_mock.game_over = False
        self.game_mock.get_message.return_value = ""
        self.game_mock.agents = {-1: None, 1: None}

        # --- 修正: gui インスタンスの font は _load_font 経由でモックされるはず ---
        # self.gui.font = self.font_mock # この行は不要
        # -----------------------------------------------------------------
        # --- 修正: dummy_surface は setUp で定義したものを使用 ---
        # self.dummy_surface = self.font_mock.render.return_value # 不要
        # ---------------------------------------------

        # config.agents のモック設定
        self.test_agent_options = [(0, '人間'), (1, 'First'), (2, 'Random')]
        self.patcher_get_options = patch('gui.get_agent_options', return_value=self.test_agent_options)
        self.mock_get_options = self.patcher_get_options.start()
        self.addCleanup(self.patcher_get_options.stop)

        def mock_get_class(agent_id):
            if agent_id == 0: return None
            if agent_id == 1: return FirstAgent
            if agent_id == 2: return RandomAgent
            return None
        self.patcher_get_class = patch('gui.get_agent_class', side_effect=mock_get_class)
        self.mock_get_class = self.patcher_get_class.start()
        self.addCleanup(self.patcher_get_class.stop)

        # GUIインスタンスの agent_options を上書き
        self.gui.agent_options = self.test_agent_options

        # pygame.draw のモック設定
        self.patcher_pygame_draw = patch('gui.pygame.draw')
        self.mock_pygame_draw = self.patcher_pygame_draw.start()
        self.addCleanup(self.patcher_pygame_draw.stop)

        # pygame.display, pygame.time のモック
        self.patcher_pygame_display = patch('gui.pygame.display')
        self.mock_pygame_display = self.patcher_pygame_display.start()
        self.addCleanup(self.patcher_pygame_display.stop)

        self.patcher_pygame_time = patch('gui.pygame.time')
        self.mock_pygame_time = self.patcher_pygame_time.start()
        self.addCleanup(self.patcher_pygame_time.stop)


    # === ヘルパーメソッドのテスト ===

    def test_calculate_turn_message_center_y(self):
        """_calculate_turn_message_center_y が数値を返すか"""
        y = self.gui._calculate_turn_message_center_y()
        self.assertIsInstance(y, (int, float))
        self.assertGreater(y, 0)

    def test_calculate_button_height(self):
        """_calculate_button_height が計算を行うか"""
        height = self.gui._calculate_button_height()
        self.font_mock.render.assert_called_with("Button", True, Color.BUTTON_TEXT)
        expected_height = self.dummy_surface.get_height() + Screen.BUTTON_VERTICAL_MARGIN * 2 + Screen.BUTTON_BORDER_WIDTH * 2
        self.assertEqual(height, expected_height)

    def test_calculate_player_settings_height(self):
        """_calculate_player_settings_height がエージェント数に基づいて高さを計算するか"""
        font_height = self.font_mock.get_height()
        num_options = len(self.test_agent_options)
        expected_height = font_height + Screen.RADIO_Y_OFFSET + Screen.RADIO_Y_SPACING * (num_options - 1) + Screen.RADIO_BUTTON_SIZE
        actual_height = self.gui._calculate_player_settings_height()
        self.assertEqual(actual_height, expected_height)

    def test_calculate_player_settings_height_no_options(self):
        """_calculate_player_settings_height が agent_options が空の場合に正しく動作するか"""
        self.gui.agent_options = [] # agent_options を空にする
        font_height = self.font_mock.get_height()
        expected_height = font_height # ラベル分のみ
        actual_height = self.gui._calculate_player_settings_height()
        self.assertEqual(actual_height, expected_height)

    def test_calculate_player_settings_top(self):
        """_calculate_player_settings_top が数値を返すか"""
        self.gui._calculate_button_rect = MagicMock(return_value=pygame.Rect(10, 10, 100, 30))
        top = self.gui._calculate_player_settings_top()
        self.assertIsInstance(top, (int, float))
        self.assertGreater(top, 0)
        self.gui._calculate_button_rect.assert_called_once_with(False, False, False, False)

    def test_get_message_y_position(self):
        """_get_message_y_position が状況に応じて正しいY座標を返すか"""
        y_ingame = self.gui._get_message_y_position(False, False)
        turn_msg_y = self.gui._calculate_turn_message_center_y()
        font_h = self.font_mock.get_height()
        expected_y_ingame = turn_msg_y - font_h - Screen.MESSAGE_ABOVE_TURN_MARGIN
        self.assertEqual(y_ingame, expected_y_ingame)
        y_start = self.gui._get_message_y_position(True, False)
        self.assertEqual(y_start, Screen.GAME_START_MESSAGE_TOP_MARGIN)
        y_over = self.gui._get_message_y_position(False, True)
        expected_y_over = self.gui._calculate_turn_message_center_y()
        self.assertEqual(y_over, expected_y_over)

    @patch('builtins.print')
    def test_load_font_success(self, mock_print):
        """_load_font が正常にフォントをロードするか (モックで確認)"""
        self.mock_path_exists.reset_mock()
        self.mock_pygame_font.reset_mock()
        self.mock_pygame_sysfont.reset_mock()
        mock_print.reset_mock()
        self.mock_path_exists.return_value = True
        self.mock_pygame_font.side_effect = None # エラーを起こさないように
        # --- 修正: _load_font を直接呼び出す ---
        font = self.gui._load_font()
        # ------------------------------------

        self.assertIsInstance(font, MagicMock)
        self.mock_path_exists.assert_called_once()
        # --- 修正: pygame.font.Font が呼ばれるはず ---
        self.mock_pygame_font.assert_called_once()
        # -----------------------------------------
        self.mock_pygame_sysfont.assert_not_called()
        mock_print.assert_not_called()

    @patch('builtins.print')
    def test_load_font_file_not_found(self, mock_print):
        """_load_font でフォントファイルが見つからない場合"""
        self.mock_path_exists.reset_mock()
        self.mock_pygame_font.reset_mock()
        self.mock_pygame_sysfont.reset_mock()
        mock_print.reset_mock()
        self.mock_path_exists.return_value = False
        self.mock_pygame_sysfont.side_effect = None # エラーを起こさないように
        # --- 修正: _load_font を直接呼び出す ---
        font = self.gui._load_font()
        # ------------------------------------

        self.assertIsInstance(font, MagicMock)
        self.mock_path_exists.assert_called_once()
        self.mock_pygame_font.assert_not_called() # Font(path) は呼ばれない
        # --- 修正: SysFont が呼ばれるはず ---
        self.mock_pygame_sysfont.assert_called_once()
        # ----------------------------------
        self.assertGreater(mock_print.call_count, 0)
        all_print_output = "".join(str(call_arg[0]) for call_arg, _ in mock_print.call_args_list)
        self.assertIn("同梱フォントファイルが見つかりません", all_print_output)
        self.assertIn("デフォルトフォント（英語）を使用します。", all_print_output)

    @patch('builtins.print')
    def test_load_font_load_error(self, mock_print):
        """_load_font でフォント読み込み時にエラーが発生する場合"""
        self.mock_path_exists.reset_mock()
        self.mock_pygame_font.reset_mock()
        self.mock_pygame_sysfont.reset_mock()
        mock_print.reset_mock()
        self.mock_path_exists.return_value = True
        # --- 修正: Font(path) でエラー発生 ---
        self.mock_pygame_font.side_effect = [pygame.error("Test font load error"), self.font_mock] # 1回目はエラー、2回目(fallback)は成功
        # -----------------------------------
        self.mock_pygame_sysfont.side_effect = None # SysFont は成功する想定
        # --- 修正: _load_font を直接呼び出す ---
        font = self.gui._load_font()
        # ------------------------------------

        self.assertIsInstance(font, MagicMock)
        self.mock_path_exists.assert_called_once()
        # --- 修正: Font(path) が1回呼ばれる ---
        self.assertEqual(self.mock_pygame_font.call_count, 1)
        # ----------------------------------
        # --- 修正: SysFont が呼ばれるはず ---
        self.mock_pygame_sysfont.assert_called_once()
        # ----------------------------------
        self.assertGreater(mock_print.call_count, 0)
        all_print_output = "".join(str(call_arg[0]) for call_arg, _ in mock_print.call_args_list)
        self.assertIn("同梱フォントの読み込みに失敗しました", all_print_output)
        self.assertIn("Test font load error", all_print_output)
        self.assertIn("デフォルトフォント（英語）を使用します。", all_print_output)

    @patch('builtins.print')
    def test_load_font_sysfont_error(self, mock_print):
        """_load_font で SysFont も失敗する場合"""
        self.mock_path_exists.reset_mock()
        self.mock_pygame_font.reset_mock() # Font モックをリセット
        self.mock_pygame_sysfont.reset_mock()
        mock_print.reset_mock()
        self.mock_path_exists.return_value = False # ファイルなし
        self.mock_pygame_sysfont.side_effect = pygame.error("Test sysfont error") # SysFont 失敗

        # --- 修正: _load_font を直接呼び出す ---
        font = self.gui._load_font()
        # ------------------------------------

        self.assertIsInstance(font, MagicMock)
        self.mock_path_exists.assert_called_once()
        self.mock_pygame_sysfont.assert_called_once() # SysFont は呼ばれる

        # --- 修正: Font(path) は呼ばれず、Font(None, size) が呼ばれる ---
        self.mock_pygame_font.assert_called_once_with(None, ANY)
        # ----------------------------------------------------------

        self.assertGreater(mock_print.call_count, 0)
        all_print_output = "".join(str(call_arg[0]) for call_arg, _ in mock_print.call_args_list)
        self.assertIn("同梱フォントファイルが見つかりません", all_print_output)
        self.assertIn("デフォルトフォント（英語）を使用します。", all_print_output)
        self.assertIn("システムフォントも利用できません。", all_print_output)
        self.assertIn("pygame デフォルトフォントを使用します。", all_print_output)


    def test_calculate_board_rect(self):
        """_calculate_board_rect が正しい盤面 Rect を返すか"""
        rect = self.gui._calculate_board_rect()
        expected_left = (Screen.WIDTH - Screen.BOARD_SIZE) // 2
        expected_top = Screen.BOARD_TOP_MARGIN
        expected_rect = pygame.Rect(expected_left, expected_top, Screen.BOARD_SIZE, Screen.BOARD_SIZE)
        self.assertEqual(rect, expected_rect)

    def test_get_clicked_cell(self):
        """get_clicked_cell が正しいセル座標を返すか"""
        board_rect = self.gui._calculate_board_rect()
        cell_size = Screen.CELL_SIZE
        click_x = board_rect.left + cell_size * 3 + cell_size // 2
        click_y = board_rect.top + cell_size * 4 + cell_size // 2
        row, col = self.gui.get_clicked_cell((click_x, click_y))
        self.assertEqual(row, 4)
        self.assertEqual(col, 3)
        row_out_tl, col_out_tl = self.gui.get_clicked_cell((board_rect.left - 1, board_rect.top - 1))
        self.assertEqual(row_out_tl, -1)
        self.assertEqual(col_out_tl, -1)
        row_out_br, col_out_br = self.gui.get_clicked_cell((board_rect.right, board_rect.bottom))
        self.assertEqual(row_out_br, -1)
        self.assertEqual(col_out_br, -1)
        row_out_bl, col_out_bl = self.gui.get_clicked_cell((board_rect.left - 1, board_rect.bottom))
        self.assertEqual(row_out_bl, -1)
        self.assertEqual(col_out_bl, -1)
        row_out_tr, col_out_tr = self.gui.get_clicked_cell((board_rect.right, board_rect.top - 1))
        self.assertEqual(row_out_tr, -1)
        self.assertEqual(col_out_tr, -1)


    # === 描画メソッドのテスト ===
    @patch('gui.GameGUI._draw_board_background')
    @patch('gui.GameGUI._draw_board_grid')
    @patch('gui.GameGUI._draw_stones')
    @patch('gui.GameGUI._draw_stone_count')
    def test_draw_board(self, mock_draw_count, mock_draw_stones, mock_draw_grid, mock_draw_bg):
        board_rect = self.gui._calculate_board_rect()
        self.gui.draw_board(self.game_mock)
        mock_draw_bg.assert_called_once_with(board_rect)
        mock_draw_grid.assert_called_once_with(board_rect)
        mock_draw_stones.assert_called_once_with(self.game_mock.get_board(), board_rect)
        mock_draw_count.assert_called_once_with(self.game_mock, board_rect)

    def test_draw_board_background(self):
        board_rect = pygame.Rect(10, 10, 100, 100)
        self.gui._draw_board_background(board_rect)
        self.gui.screen.fill.assert_called_once_with(Color.BACKGROUND)
        self.mock_pygame_draw.rect.assert_called_once_with(self.gui.screen, Color.BOARD, board_rect)

    def test_draw_board_grid(self):
        board_rect = pygame.Rect(10, 10, Screen.BOARD_SIZE, Screen.BOARD_SIZE)
        self.gui._draw_board_grid(board_rect)
        self.assertEqual(self.mock_pygame_draw.rect.call_count, 64)
        last_cell_rect = pygame.Rect(
            board_rect.left + 7 * Screen.CELL_SIZE,
            board_rect.top + 7 * Screen.CELL_SIZE,
            Screen.CELL_SIZE,
            Screen.CELL_SIZE
        )
        self.mock_pygame_draw.rect.assert_called_with(self.gui.screen, Color.BLACK, last_cell_rect, 1)

    @patch('gui.GameGUI._draw_stone')
    def test_draw_stones(self, mock_draw_stone):
        board_rect = pygame.Rect(10, 10, Screen.BOARD_SIZE, Screen.BOARD_SIZE)
        dummy_board = [[0]*8 for _ in range(8)]
        dummy_board[3][3] = -1
        dummy_board[4][4] = 1
        self.game_mock.get_board.return_value = dummy_board
        self.gui._draw_stones(dummy_board, board_rect)
        self.assertEqual(mock_draw_stone.call_count, 2)
        mock_draw_stone.assert_any_call(board_rect, 3, 3, Color.BLACK)
        mock_draw_stone.assert_any_call(board_rect, 4, 4, Color.WHITE)

    def test_draw_stone(self):
        board_rect = pygame.Rect(10, 10, Screen.BOARD_SIZE, Screen.BOARD_SIZE)
        row, col = 3, 4
        color = Color.BLACK
        self.gui._draw_stone(board_rect, row, col, color)
        expected_center = (
            board_rect.left + col * Screen.CELL_SIZE + Screen.CELL_SIZE // 2,
            board_rect.top + row * Screen.CELL_SIZE + Screen.CELL_SIZE // 2
        )
        expected_radius = Screen.CELL_SIZE // 2 - 5
        self.mock_pygame_draw.circle.assert_called_once_with(self.gui.screen, color, expected_center, expected_radius)

    @patch('gui.GameGUI._draw_text_with_position')
    def test_draw_stone_count(self, mock_draw_text):
        board_rect = self.gui._calculate_board_rect()
        self.game_mock.board.count_stones.return_value = (10, 5)
        self.gui._draw_stone_count(self.game_mock, board_rect)
        expected_y = board_rect.bottom + Screen.TURN_MESSAGE_TOP_MARGIN
        left_margin = board_rect.left
        right_x = self.gui.screen_width - left_margin
        self.assertEqual(mock_draw_text.call_count, 2)
        mock_draw_text.assert_any_call(f"黒: 10", Color.BLACK, (left_margin, expected_y))
        mock_draw_text.assert_any_call(f"白: 5", Color.WHITE, (right_x, expected_y), is_right_aligned=True)

    def test_draw_text_with_position(self):
        text = "Test"
        color = Color.WHITE
        pos = (50, 60)
        self.gui._draw_text_with_position(text, color, pos)
        self.font_mock.render.assert_called_with(text, True, color)
        expected_rect = self.dummy_surface.get_rect(topleft=pos)
        self.gui.screen.blit.assert_called_once_with(self.dummy_surface, expected_rect)

    def test_draw_text_with_position_right_aligned(self):
        text = "Right"
        color = Color.BLACK
        pos = (200, 80)
        self.gui._draw_text_with_position(text, color, pos, is_right_aligned=True)
        self.font_mock.render.assert_called_with(text, True, color)
        expected_rect = self.dummy_surface.get_rect(topleft=pos)
        expected_rect.right = pos[0]
        self.gui.screen.blit.assert_called_once_with(self.dummy_surface, expected_rect)

    def test_draw_valid_moves(self):
        board_rect = self.gui._calculate_board_rect()
        valid_moves = [(2, 3), (5, 5)]
        self.game_mock.get_valid_moves.return_value = valid_moves
        self.gui.draw_valid_moves(self.game_mock)
        self.assertEqual(self.mock_pygame_draw.circle.call_count, len(valid_moves))
        expected_center_1 = (
            board_rect.left + 3 * Screen.CELL_SIZE + Screen.CELL_SIZE // 2,
            board_rect.top + 2 * Screen.CELL_SIZE + Screen.CELL_SIZE // 2
        )
        expected_radius = Screen.CELL_SIZE // 8
        self.mock_pygame_draw.circle.assert_any_call(self.gui.screen, Color.GRAY, expected_center_1, expected_radius)

    def test_draw_message(self):
        message = "Hello World"
        with patch.object(self.gui, '_get_message_y_position', return_value=150) as mock_get_y:
            self.gui.draw_message(message)
            mock_get_y.assert_called_once_with(False, False)
            self.font_mock.render.assert_called_with(message, True, Color.WHITE)
            expected_center = (self.gui.screen_width // 2, 150)
            expected_rect = self.dummy_surface.get_rect(center=expected_center)
            self.gui.screen.blit.assert_called_once_with(self.dummy_surface, expected_rect)

    def test_draw_message_empty(self):
        # --- 修正: setUp でモックをリセットするので、render が呼ばれないはず ---
        self.gui.draw_message(None)
        self.gui.screen.blit.assert_not_called()
        self.gui.draw_message("")
        self.gui.screen.blit.assert_not_called()
        # -----------------------------------------------------------------

    def test_draw_turn_message(self):
        self.game_mock.turn = 1
        self.game_mock.game_over = False
        with patch.object(self.gui, '_calculate_turn_message_center_y', return_value=200) as mock_calc_y:
            self.gui.draw_turn_message(self.game_mock)
            mock_calc_y.assert_called_once()
            expected_message = "白の番です"
            self.font_mock.render.assert_called_with(expected_message, True, Color.WHITE)
            expected_center = (self.gui.screen_width // 2, 200)
            expected_rect = self.dummy_surface.get_rect(center=expected_center)
            self.gui.screen.blit.assert_called_once_with(self.dummy_surface, expected_rect)

    def test_draw_turn_message_game_over(self):
        # --- 修正: setUp でモックをリセットするので、render が呼ばれないはず ---
        self.game_mock.game_over = True
        self.gui.draw_turn_message(self.game_mock)
        self.gui.screen.blit.assert_not_called()
        # -----------------------------------------------------------------

    # === ボタン描画メソッドのテスト ===
    def test_draw_start_button(self):
        self.gui.draw_start_button()
        # __init__ で生成されたインスタンスの draw が呼ばれる
        self.mock_button_instance.draw.assert_called_once_with(self.gui.screen)

    def test_draw_restart_button(self):
        expected_rect = pygame.Rect(10, 10, 100, 30)
        self.gui._calculate_button_rect = MagicMock(return_value=expected_rect)
        mock_button_in_method = MagicMock(spec=OriginalButton)
        # --- 修正: MockButton は setUp で開始済みなので、return_value を設定 ---
        self.MockButton.return_value = mock_button_in_method
        # -----------------------------------------------------------------

        self.gui.draw_restart_button(game_over=False)

        self.gui._calculate_button_rect.assert_called_once_with(False, False, False, False)
        # Button が正しい引数でインスタンス化されたか確認
        self.MockButton.assert_called_with(expected_rect, "リスタート", self.gui.font)
        # 生成されたインスタンスの draw が呼ばれたか
        mock_button_in_method.draw.assert_called_with(self.gui.screen)

        # --- 修正: モックの return_value を元に戻す ---
        self.MockButton.return_value = self.mock_button_instance
        # -----------------------------------------
        self.gui._calculate_button_rect.reset_mock()
        self.gui._calculate_button_rect.return_value = None


    def test_draw_reset_button(self):
        expected_rect = pygame.Rect(120, 10, 100, 30)
        self.gui._calculate_button_rect = MagicMock(return_value=expected_rect)
        mock_button_in_method = MagicMock(spec=OriginalButton)
        # --- 修正: MockButton は setUp で開始済みなので、return_value を設定 ---
        self.MockButton.return_value = mock_button_in_method
        # -----------------------------------------------------------------

        self.gui.draw_reset_button(game_over=True)

        self.gui._calculate_button_rect.assert_called_once_with(False, True, True, False)
        self.MockButton.assert_called_with(expected_rect, "リセット", self.gui.font)
        mock_button_in_method.draw.assert_called_with(self.gui.screen)

        # --- 修正: モックの return_value を元に戻す ---
        self.MockButton.return_value = self.mock_button_instance
        # -----------------------------------------
        self.gui._calculate_button_rect.reset_mock()
        self.gui._calculate_button_rect.return_value = None

    def test_draw_quit_button(self):
        expected_rect = pygame.Rect(230, 10, 100, 30)
        self.gui._calculate_button_rect = MagicMock(return_value=expected_rect)
        mock_button_in_method = MagicMock(spec=OriginalButton)
        # --- 修正: MockButton は setUp で開始済みなので、return_value を設定 ---
        self.MockButton.return_value = mock_button_in_method
        # -----------------------------------------------------------------

        self.gui.draw_quit_button(game_over=False)

        self.gui._calculate_button_rect.assert_called_once_with(False, False, False, True)
        self.MockButton.assert_called_with(expected_rect, "終了", self.gui.font)
        mock_button_in_method.draw.assert_called_with(self.gui.screen)

        # --- 修正: モックの return_value を元に戻す ---
        self.MockButton.return_value = self.mock_button_instance
        # -----------------------------------------
        self.gui._calculate_button_rect.reset_mock()
        self.gui._calculate_button_rect.return_value = None

    # === ラジオボタン関連のテスト ===
    def test_draw_radio_button(self):
        pos = (100, 120)
        selected = True
        enabled = True
        self.gui.draw_radio_button(pos, selected, enabled)
        center = (pos[0] + Screen.RADIO_BUTTON_SIZE // 2, pos[1] + Screen.RADIO_BUTTON_SIZE // 2)
        outer_radius = Screen.RADIO_BUTTON_SIZE // 2
        inner_radius = int(Screen.RADIO_BUTTON_SIZE * Screen.RADIO_BUTTON_INNER_CIRCLE_RATIO // 2)
        self.assertEqual(self.mock_pygame_draw.circle.call_count, 2)
        self.mock_pygame_draw.circle.assert_any_call(self.gui.screen, Color.DARK_BLUE, center, outer_radius, 1)
        self.mock_pygame_draw.circle.assert_any_call(self.gui.screen, Color.DARK_BLUE, center, inner_radius)

    def test_draw_radio_button_not_selected(self):
        pos = (100, 120)
        selected = False
        enabled = True
        self.gui.draw_radio_button(pos, selected, enabled)
        center = (pos[0] + Screen.RADIO_BUTTON_SIZE // 2, pos[1] + Screen.RADIO_BUTTON_SIZE // 2)
        outer_radius = Screen.RADIO_BUTTON_SIZE // 2
        self.assertEqual(self.mock_pygame_draw.circle.call_count, 1)
        self.mock_pygame_draw.circle.assert_called_once_with(self.gui.screen, Color.DARK_BLUE, center, outer_radius, 1)

    def test_draw_radio_button_disabled(self):
        pos = (100, 120)
        selected = True
        enabled = False
        self.gui.draw_radio_button(pos, selected, enabled)
        center = (pos[0] + Screen.RADIO_BUTTON_SIZE // 2, pos[1] + Screen.RADIO_BUTTON_SIZE // 2)
        outer_radius = Screen.RADIO_BUTTON_SIZE // 2
        inner_radius = int(Screen.RADIO_BUTTON_SIZE * Screen.RADIO_BUTTON_INNER_CIRCLE_RATIO // 2)
        self.assertEqual(self.mock_pygame_draw.circle.call_count, 2)
        self.mock_pygame_draw.circle.assert_any_call(self.gui.screen, Color.LIGHT_BLUE, center, outer_radius, 1)
        self.mock_pygame_draw.circle.assert_any_call(self.gui.screen, Color.LIGHT_BLUE, center, inner_radius)

    def test_draw_text(self):
        text = "Label"
        pos = (150, 160)
        enabled = True
        self.gui.draw_text(text, pos, enabled)
        self.font_mock.render.assert_called_with(text, True, Color.WHITE)
        expected_rect = self.dummy_surface.get_rect(topleft=pos)
        self.gui.screen.blit.assert_called_once_with(self.dummy_surface, expected_rect)

    def test_draw_text_disabled(self):
        text = "Disabled Label"
        pos = (150, 160)
        enabled = False
        self.gui.draw_text(text, pos, enabled)
        self.font_mock.render.assert_called_with(text, True, Color.DISABLED_TEXT)
        expected_rect = self.dummy_surface.get_rect(topleft=pos)
        self.gui.screen.blit.assert_called_once_with(self.dummy_surface, expected_rect)

    @patch('gui.GameGUI.draw_radio_button')
    @patch('gui.GameGUI._draw_text_with_position')
    def test_draw_player_settings_calls_draw_methods(self, mock_draw_text, mock_draw_radio):
        mock_first_agent = MagicMock(spec=FirstAgent)
        self.game_mock.agents = {-1: None, 1: mock_first_agent}
        player_settings_top = 100
        enabled = True
        self.gui._calculate_board_rect = MagicMock(return_value=pygame.Rect(0,0,400,400))
        self.gui.draw_player_settings(self.game_mock, player_settings_top, enabled)
        expected_calls = len(self.test_agent_options) * 2
        self.assertEqual(mock_draw_radio.call_count, expected_calls)
        self.assertEqual(mock_draw_text.call_count, 2 + expected_calls)

    def test_get_clicked_radio_button(self):
        """get_clicked_radio_button が正しいボタンを返すか"""
        player_settings_top = 300
        board_rect = self.gui._calculate_board_rect()
        left_margin = board_rect.left
        white_player_label_x = self.gui.screen_width // 2 + Screen.RADIO_BUTTON_MARGIN
        radio_y_offset = Screen.RADIO_Y_OFFSET
        radio_y_spacing = Screen.RADIO_Y_SPACING
        radio_size = Screen.RADIO_BUTTON_SIZE
        radio_y_first = player_settings_top + radio_y_offset + 1 * radio_y_spacing
        click_pos_black_first = (left_margin + radio_size // 2, radio_y_first + radio_size // 2)
        player, agent_id = self.gui.get_clicked_radio_button(click_pos_black_first, player_settings_top)
        self.assertEqual(player, -1)
        self.assertEqual(agent_id, 1)
        radio_y_random = player_settings_top + radio_y_offset + 2 * radio_y_spacing
        click_pos_white_random = (white_player_label_x + radio_size // 2, radio_y_random + radio_size // 2)
        player, agent_id = self.gui.get_clicked_radio_button(click_pos_white_random, player_settings_top)
        self.assertEqual(player, 1)
        self.assertEqual(agent_id, 2)
        click_pos_none = (0, 0)
        player, agent_id = self.gui.get_clicked_radio_button(click_pos_none, player_settings_top)
        self.assertIsNone(player)
        self.assertIsNone(agent_id)

    @patch('builtins.print')
    def test_get_clicked_radio_button_no_options(self, mock_print):
        """get_clicked_radio_button で agent_options がない場合に警告が出るか"""
        player_settings_top = 300
        click_pos = (100, 350)
        original_options = self.gui.agent_options
        warning_message = "Warning: agent_options not found in GUI. Radio button clicks won't work."

        try:
            self.gui.agent_options = None
            player, agent_id = self.gui.get_clicked_radio_button(click_pos, player_settings_top)
            self.assertIsNone(player)
            self.assertIsNone(agent_id)
            mock_print.assert_called_with(warning_message)
            mock_print.reset_mock()

            self.gui.agent_options = []
            player, agent_id = self.gui.get_clicked_radio_button(click_pos, player_settings_top)
            self.assertIsNone(player)
            self.assertIsNone(agent_id)
            mock_print.assert_called_with(warning_message)
            mock_print.reset_mock()

            delattr(self.gui, 'agent_options')
            player, agent_id = self.gui.get_clicked_radio_button(click_pos, player_settings_top)
            self.assertIsNone(player)
            self.assertIsNone(agent_id)
            mock_print.assert_called_with(warning_message)

        finally:
            if not hasattr(self.gui, 'agent_options'):
                 self.gui.agent_options = original_options
            elif self.gui.agent_options is None or self.gui.agent_options == []:
                 self.gui.agent_options = original_options

    # === アニメーションメソッドのテスト ===
    @patch('gui.GameGUI.draw_board')
    @patch('gui.GameGUI.draw_turn_message')
    @patch('gui.GameGUI.draw_message')
    @patch('gui.GameGUI.draw_restart_button')
    @patch('gui.GameGUI.draw_reset_button')
    @patch('gui.GameGUI.draw_quit_button')
    @patch('gui.GameGUI.draw_player_settings')
    def test_draw_stone_animation(self, mock_draw_settings, mock_draw_quit, mock_draw_reset, mock_draw_restart, mock_draw_msg, mock_draw_turn, mock_draw_board):
        """draw_stone_animation がループ内で描画メソッドを正しく呼び出すか"""
        row, col = 3, 3
        color = Color.BLACK
        self.gui._calculate_player_settings_top = MagicMock(return_value=500)
        max_radius = self.gui.cell_size // 2 - 5
        expected_loop_count = (max_radius + 4) // 5 if max_radius > 0 else 0
        if max_radius > 0:
            self.assertGreater(expected_loop_count, 0, "Animation loop should run at least once")
        else:
            self.assertEqual(expected_loop_count, 0, "Animation loop should not run if max_radius <= 0")

        self.gui.draw_stone_animation(self.game_mock, row, col, color)

        self.assertEqual(mock_draw_board.call_count, expected_loop_count)
        self.assertEqual(mock_draw_turn.call_count, expected_loop_count)
        self.assertEqual(mock_draw_msg.call_count, expected_loop_count)
        self.assertEqual(mock_draw_restart.call_count, expected_loop_count)
        self.assertEqual(mock_draw_reset.call_count, expected_loop_count)
        self.assertEqual(mock_draw_quit.call_count, expected_loop_count)
        self.assertEqual(self.gui._calculate_player_settings_top.call_count, expected_loop_count)
        self.assertEqual(mock_draw_settings.call_count, expected_loop_count)
        self.assertEqual(self.mock_pygame_draw.circle.call_count, expected_loop_count)
        self.assertEqual(self.mock_pygame_display.flip.call_count, expected_loop_count)
        self.assertEqual(self.mock_pygame_time.delay.call_count, expected_loop_count)

    @patch('gui.GameGUI._draw_board_background')
    @patch('gui.GameGUI._draw_board_grid')
    @patch('gui.GameGUI._draw_stone')
    @patch('gui.GameGUI.draw_turn_message')
    @patch('gui.GameGUI.draw_message')
    @patch('gui.GameGUI.draw_restart_button')
    @patch('gui.GameGUI.draw_reset_button')
    @patch('gui.GameGUI.draw_quit_button')
    @patch('gui.GameGUI.draw_player_settings')
    def test_draw_flip_animation(self, mock_draw_settings, mock_draw_quit, mock_draw_reset, mock_draw_restart, mock_draw_msg, mock_draw_turn, mock_draw_stone, mock_draw_grid, mock_draw_bg):
        """draw_flip_animation がループ内で描画メソッドを正しく呼び出すか"""
        flipped_stones = [(3, 4), (4, 3)]
        color = Color.WHITE
        board_size = 8
        dummy_board = [[0]*board_size for _ in range(board_size)]
        dummy_board[3][4] = -1
        dummy_board[4][3] = -1
        dummy_board[3][3] = 1
        dummy_board[4][4] = -1
        self.game_mock.get_board.return_value = dummy_board
        self.game_mock.get_board_size.return_value = board_size
        self.gui._calculate_player_settings_top = MagicMock(return_value=500)

        steps = 10
        expected_loop_count = steps
        non_flipped_stone_count = sum(1 for r in range(board_size) for c in range(board_size) if dummy_board[r][c] != 0 and (r, c) not in flipped_stones)

        self.gui.draw_flip_animation(self.game_mock, flipped_stones, color)

        self.assertEqual(mock_draw_bg.call_count, expected_loop_count)
        self.assertEqual(mock_draw_grid.call_count, expected_loop_count)
        self.assertEqual(mock_draw_stone.call_count, expected_loop_count * non_flipped_stone_count)
        self.assertEqual(mock_draw_turn.call_count, expected_loop_count)
        self.assertEqual(mock_draw_msg.call_count, expected_loop_count)
        self.assertEqual(mock_draw_restart.call_count, expected_loop_count)
        self.assertEqual(mock_draw_reset.call_count, expected_loop_count)
        self.assertEqual(mock_draw_quit.call_count, expected_loop_count)
        self.assertEqual(self.gui._calculate_player_settings_top.call_count, expected_loop_count)
        self.assertEqual(mock_draw_settings.call_count, expected_loop_count)
        self.assertEqual(self.mock_pygame_draw.circle.call_count, expected_loop_count * len(flipped_stones))
        self.assertEqual(self.mock_pygame_display.flip.call_count, expected_loop_count)
        self.assertEqual(self.mock_pygame_time.delay.call_count, expected_loop_count)

    @patch('gui.GameGUI._draw_board_background')
    @patch('gui.GameGUI._draw_board_grid')
    @patch('gui.GameGUI._draw_stone')
    @patch('gui.GameGUI.draw_turn_message')
    @patch('gui.GameGUI.draw_message')
    @patch('gui.GameGUI.draw_restart_button')
    @patch('gui.GameGUI.draw_reset_button')
    @patch('gui.GameGUI.draw_quit_button')
    @patch('gui.GameGUI.draw_player_settings')
    def test_draw_flip_animation_no_flips(self, mock_draw_settings, mock_draw_quit, mock_draw_reset, mock_draw_restart, mock_draw_msg, mock_draw_turn, mock_draw_stone, mock_draw_grid, mock_draw_bg):
        """draw_flip_animation で flipped_stones が空の場合のテスト"""
        flipped_stones = []
        color = Color.WHITE
        board_size = 8
        dummy_board = [[0]*board_size for _ in range(board_size)]
        dummy_board[3][3] = 1
        dummy_board[4][4] = -1
        self.game_mock.get_board.return_value = dummy_board
        self.game_mock.get_board_size.return_value = board_size
        self.gui._calculate_player_settings_top = MagicMock(return_value=500)

        steps = 10
        expected_loop_count = steps
        non_flipped_stone_count = sum(1 for r in range(board_size) for c in range(board_size) if dummy_board[r][c] != 0)

        self.gui.draw_flip_animation(self.game_mock, flipped_stones, color)

        self.assertEqual(mock_draw_stone.call_count, expected_loop_count * non_flipped_stone_count)
        self.assertEqual(self.mock_pygame_draw.circle.call_count, 0)
        self.assertEqual(mock_draw_bg.call_count, expected_loop_count)
        self.assertEqual(mock_draw_grid.call_count, expected_loop_count)
        self.assertEqual(mock_draw_turn.call_count, expected_loop_count)
        self.assertEqual(mock_draw_msg.call_count, expected_loop_count)
        self.assertEqual(mock_draw_restart.call_count, expected_loop_count)
        self.assertEqual(mock_draw_reset.call_count, expected_loop_count)
        self.assertEqual(mock_draw_quit.call_count, expected_loop_count)
        self.assertEqual(self.gui._calculate_player_settings_top.call_count, expected_loop_count)
        self.assertEqual(mock_draw_settings.call_count, expected_loop_count)
        self.assertEqual(self.mock_pygame_display.flip.call_count, expected_loop_count)
        self.assertEqual(self.mock_pygame_time.delay.call_count, expected_loop_count)

    # === ボタンクリック判定メソッドのテスト ===

    def test_is_start_button_clicked(self):
        """is_start_button_clicked が正しく判定するか"""
        expected_rect = pygame.Rect(100, 100, 150, 50)
        original_calc_rect = self.gui._calculate_button_rect
        self.gui._calculate_button_rect = MagicMock(wraps=original_calc_rect)
        self.gui._calculate_button_rect.return_value = expected_rect

        mock_temp_button_instance = MagicMock(spec=OriginalButton)
        mock_temp_button_instance.is_clicked.return_value = True
        # --- 修正: MockButton は setUp で開始済み ---
        self.MockButton.return_value = mock_temp_button_instance
        # -----------------------------------------
        click_pos_inside = expected_rect.center
        self.assertTrue(self.gui.is_start_button_clicked(click_pos_inside))
        self.gui._calculate_button_rect.assert_called_once_with(is_start_button=True)
        self.MockButton.assert_called_with(expected_rect, "", self.gui.font)
        mock_temp_button_instance.is_clicked.assert_called_with(click_pos_inside)

        mock_temp_button_instance.is_clicked.return_value = False
        click_pos_outside = (0, 0)
        self.assertFalse(self.gui.is_start_button_clicked(click_pos_outside))
        self.assertEqual(mock_temp_button_instance.is_clicked.call_count, 2)
        mock_temp_button_instance.is_clicked.assert_called_with(click_pos_outside)

        # --- 修正: モックの return_value を元に戻す ---
        self.MockButton.return_value = self.mock_button_instance
        # -----------------------------------------
        self.gui._calculate_button_rect = original_calc_rect

    def test_is_restart_button_clicked(self):
        """is_restart_button_clicked が正しく判定するか"""
        expected_rect_game_over = pygame.Rect(50, 200, 100, 40)
        expected_rect_in_game = pygame.Rect(60, 210, 110, 45)
        original_calc_rect = self.gui._calculate_button_rect
        self.gui._calculate_button_rect = MagicMock(wraps=original_calc_rect)

        mock_temp_button_instance = MagicMock(spec=OriginalButton)
        # --- 修正: MockButton は setUp で開始済み ---
        self.MockButton.return_value = mock_temp_button_instance
        # -----------------------------------------
        # --- game_over = True ---
        self.gui._calculate_button_rect.return_value = expected_rect_game_over
        mock_temp_button_instance.is_clicked.return_value = True
        click_pos_inside_go = expected_rect_game_over.center
        self.assertTrue(self.gui.is_restart_button_clicked(click_pos_inside_go, game_over=True))
        self.gui._calculate_button_rect.assert_called_with(False, True, False, False)
        self.MockButton.assert_called_with(expected_rect_game_over, "", self.gui.font)
        mock_temp_button_instance.is_clicked.assert_called_with(click_pos_inside_go)

        mock_temp_button_instance.is_clicked.return_value = False
        click_pos_outside_go = (0, 0)
        self.assertFalse(self.gui.is_restart_button_clicked(click_pos_outside_go, game_over=True))

        # --- game_over = False ---
        self.gui._calculate_button_rect.return_value = expected_rect_in_game
        mock_temp_button_instance.is_clicked.return_value = True
        click_pos_inside_ig = expected_rect_in_game.center
        self.assertTrue(self.gui.is_restart_button_clicked(click_pos_inside_ig, game_over=False))
        self.gui._calculate_button_rect.assert_called_with(False, False, False, False)
        self.MockButton.assert_called_with(expected_rect_in_game, "", self.gui.font)
        mock_temp_button_instance.is_clicked.assert_called_with(click_pos_inside_ig)

        mock_temp_button_instance.is_clicked.return_value = False
        click_pos_outside_ig = (1, 1)
        self.assertFalse(self.gui.is_restart_button_clicked(click_pos_outside_ig, game_over=False))

        # --- 修正: モックの return_value を元に戻す ---
        self.MockButton.return_value = self.mock_button_instance
        # -----------------------------------------
        self.gui._calculate_button_rect = original_calc_rect

    def test_is_reset_button_clicked(self):
        """is_reset_button_clicked が正しく判定するか"""
        expected_rect_game_over = pygame.Rect(160, 200, 100, 40)
        expected_rect_in_game = pygame.Rect(180, 210, 110, 45)
        original_calc_rect = self.gui._calculate_button_rect
        self.gui._calculate_button_rect = MagicMock(wraps=original_calc_rect)

        mock_temp_button_instance = MagicMock(spec=OriginalButton)
        # --- 修正: MockButton は setUp で開始済み ---
        self.MockButton.return_value = mock_temp_button_instance
        # -----------------------------------------
        # --- game_over = True ---
        self.gui._calculate_button_rect.return_value = expected_rect_game_over
        mock_temp_button_instance.is_clicked.return_value = True
        click_pos_inside_go = expected_rect_game_over.center
        self.assertTrue(self.gui.is_reset_button_clicked(click_pos_inside_go, game_over=True))
        self.gui._calculate_button_rect.assert_called_with(False, True, True, False)
        self.MockButton.assert_called_with(expected_rect_game_over, "", self.gui.font)
        mock_temp_button_instance.is_clicked.assert_called_with(click_pos_inside_go)

        mock_temp_button_instance.is_clicked.return_value = False
        click_pos_outside_go = (0, 0)
        self.assertFalse(self.gui.is_reset_button_clicked(click_pos_outside_go, game_over=True))

        # --- game_over = False ---
        self.gui._calculate_button_rect.return_value = expected_rect_in_game
        mock_temp_button_instance.is_clicked.return_value = True
        click_pos_inside_ig = expected_rect_in_game.center
        self.assertTrue(self.gui.is_reset_button_clicked(click_pos_inside_ig, game_over=False))
        self.gui._calculate_button_rect.assert_called_with(False, False, True, False)
        self.MockButton.assert_called_with(expected_rect_in_game, "", self.gui.font)
        mock_temp_button_instance.is_clicked.assert_called_with(click_pos_inside_ig)

        mock_temp_button_instance.is_clicked.return_value = False
        click_pos_outside_ig = (1, 1)
        self.assertFalse(self.gui.is_reset_button_clicked(click_pos_outside_ig, game_over=False))

        # --- 修正: モックの return_value を元に戻す ---
        self.MockButton.return_value = self.mock_button_instance
        # -----------------------------------------
        self.gui._calculate_button_rect = original_calc_rect

    def test_is_quit_button_clicked(self):
        """is_quit_button_clicked が正しく判定するか"""
        expected_rect_game_over = pygame.Rect(270, 200, 100, 40)
        expected_rect_in_game = pygame.Rect(300, 210, 110, 45)
        original_calc_rect = self.gui._calculate_button_rect
        self.gui._calculate_button_rect = MagicMock(wraps=original_calc_rect)

        mock_temp_button_instance = MagicMock(spec=OriginalButton)
        # --- 修正: MockButton は setUp で開始済み ---
        self.MockButton.return_value = mock_temp_button_instance
        # -----------------------------------------
        # --- game_over = True ---
        self.gui._calculate_button_rect.return_value = expected_rect_game_over
        mock_temp_button_instance.is_clicked.return_value = True
        click_pos_inside_go = expected_rect_game_over.center
        self.assertTrue(self.gui.is_quit_button_clicked(click_pos_inside_go, game_over=True))
        self.gui._calculate_button_rect.assert_called_with(False, True, False, True)
        self.MockButton.assert_called_with(expected_rect_game_over, "", self.gui.font)
        mock_temp_button_instance.is_clicked.assert_called_with(click_pos_inside_go)

        mock_temp_button_instance.is_clicked.return_value = False
        click_pos_outside_go = (0, 0)
        self.assertFalse(self.gui.is_quit_button_clicked(click_pos_outside_go, game_over=True))

        # --- game_over = False ---
        self.gui._calculate_button_rect.return_value = expected_rect_in_game
        mock_temp_button_instance.is_clicked.return_value = True
        click_pos_inside_ig = expected_rect_in_game.center
        self.assertTrue(self.gui.is_quit_button_clicked(click_pos_inside_ig, game_over=False))
        self.gui._calculate_button_rect.assert_called_with(False, False, False, True)
        self.MockButton.assert_called_with(expected_rect_in_game, "", self.gui.font)
        mock_temp_button_instance.is_clicked.assert_called_with(click_pos_inside_ig)

        mock_temp_button_instance.is_clicked.return_value = False
        click_pos_outside_ig = (1, 1)
        self.assertFalse(self.gui.is_quit_button_clicked(click_pos_outside_ig, game_over=False))

        # --- 修正: モックの return_value を元に戻す ---
        self.MockButton.return_value = self.mock_button_instance
        # -----------------------------------------
        self.gui._calculate_button_rect = original_calc_rect


if __name__ == '__main__':
    unittest.main(verbosity=2)

# tests/test_ui_elements.py
import unittest
import pygame
from unittest.mock import MagicMock, call, patch
import sys
import os

# --- プロジェクトルートへのパスを追加 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
# ------------------------------------

# --- テスト対象と依存モジュールをインポート ---
from ui_elements import Button
from config.theme import Color, Screen
# -----------------------------------------

class TestButton(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """テストクラス全体で Pygame を初期化する"""
        try:
            pygame.init()
            # フォントの準備 (クラスレベルで一度だけ試行)
            cls.font = None
            font_size = 24
            cls.font = pygame.font.Font(None, font_size)
            # 簡単なレンダリングテスト
            assert isinstance(cls.font.render("Test", True, Color.WHITE), pygame.Surface)
            cls.pygame_initialized = True
            cls.skip_tests = False
        except pygame.error as e:
            cls.pygame_initialized = False
            cls.skip_tests = True
            cls.skip_reason = f"Pygame initialization or font loading failed: {e}"
        except Exception as e: # 予期せぬエラー
             cls.pygame_initialized = False
             cls.skip_tests = True
             cls.skip_reason = f"Unexpected error during setup: {e}"


    @classmethod
    def tearDownClass(cls):
        """テストクラス全体で Pygame を終了する"""
        if cls.pygame_initialized:
            pygame.quit()

    def setUp(self):
        """各テストメソッドの前に実行される"""
        # Pygame 初期化失敗時はテストをスキップ
        if self.skip_tests:
            self.skipTest(self.skip_reason)

        # 各テストの前にボタンインスタンスを作成
        rect_default = pygame.Rect(10, 20, 100, 50)
        text_default = "Click Me"
        self.default_button = Button(rect_default, text_default, self.font)

        rect_custom = pygame.Rect(50, 60, 120, 40)
        text_custom = "Custom"
        custom_bg = Color.BLACK
        custom_text = Color.GREEN
        custom_border = Color.RED # config/theme.py に RED が追加されている前提
        custom_width = 3
        self.custom_button = Button(rect_custom, text_custom, self.font,
                                    bg_color=custom_bg, text_color=custom_text,
                                    border_color=custom_border, border_width=custom_width)

    def test_initialization_default(self):
        """デフォルト引数での初期化をテスト"""
        self.assertEqual(self.default_button.rect, pygame.Rect(10, 20, 100, 50))
        self.assertEqual(self.default_button.text, "Click Me")
        self.assertEqual(self.default_button.font, self.font)
        self.assertEqual(self.default_button.bg_color, Color.BUTTON)
        self.assertEqual(self.default_button.text_color, Color.BUTTON_TEXT)
        self.assertEqual(self.default_button.border_color, Color.WHITE)
        self.assertEqual(self.default_button.border_width, Screen.BUTTON_BORDER_WIDTH)
        self.assertIsInstance(self.default_button.text_surface, pygame.Surface)
        self.assertIsInstance(self.default_button.text_rect, pygame.Rect)
        self.assertEqual(self.default_button.text_rect.center, self.default_button.rect.center)

    def test_initialization_custom(self):
        """カスタム引数での初期化をテスト"""
        self.assertEqual(self.custom_button.rect, pygame.Rect(50, 60, 120, 40))
        self.assertEqual(self.custom_button.text, "Custom")
        self.assertEqual(self.custom_button.font, self.font)
        self.assertEqual(self.custom_button.bg_color, Color.BLACK)
        self.assertEqual(self.custom_button.text_color, Color.GREEN)
        self.assertEqual(self.custom_button.border_color, Color.RED)
        self.assertEqual(self.custom_button.border_width, 3)
        self.assertIsInstance(self.custom_button.text_surface, pygame.Surface)
        self.assertIsInstance(self.custom_button.text_rect, pygame.Rect)
        self.assertEqual(self.custom_button.text_rect.center, self.custom_button.rect.center)

    # --- 修正箇所 ---
    # @patch('pygame.Surface.blit') # <- このデコレータを削除
    @patch('pygame.draw.rect')    # pygame.draw.rect のモック化は維持
    def test_draw_calls(self, mock_draw_rect): # <- 引数から mock_blit を削除
        """draw メソッドが pygame の描画関数を正しく呼び出すかテスト"""
        # mock_screen は MagicMock で作成 (spec=pygame.Surface を指定)
        mock_screen = MagicMock(spec=pygame.Surface)

        # draw メソッドを実行
        self.default_button.draw(mock_screen)

        # pygame.draw.rect の呼び出しを確認
        expected_calls_rect = [
            call(mock_screen, self.default_button.bg_color, self.default_button.rect),
            call(mock_screen, self.default_button.border_color, self.default_button.rect, self.default_button.border_width)
        ]
        mock_draw_rect.assert_has_calls(expected_calls_rect, any_order=False)

        # screen.blit の呼び出しを確認 (mock_screen の blit メソッドが呼ばれたか確認)
        mock_screen.blit.assert_called_once_with(self.default_button.text_surface, self.default_button.text_rect)
    # ---------------

    def test_is_clicked_inside(self):
        """ボタン内部をクリックした場合のテスト"""
        inside_pos = self.default_button.rect.center
        self.assertTrue(self.default_button.is_clicked(inside_pos))

    def test_is_clicked_outside(self):
        """ボタン外部をクリックした場合のテスト"""
        outside_pos = (self.default_button.rect.left - 1, self.default_button.rect.top - 1)
        self.assertFalse(self.default_button.is_clicked(outside_pos))
        outside_pos_br = (self.default_button.rect.right + 1, self.default_button.rect.bottom + 1)
        self.assertFalse(self.default_button.is_clicked(outside_pos_br))

    def test_is_clicked_on_border(self):
        """ボタン境界上をクリックした場合のテスト (collidepoint は境界を含む)"""
        border_pos_tl = self.default_button.rect.topleft
        self.assertTrue(self.default_button.is_clicked(border_pos_tl))
        border_pos_br_exclusive = (self.default_button.rect.right, self.default_button.rect.bottom)
        self.assertFalse(self.default_button.is_clicked(border_pos_br_exclusive))
        border_pos_br_inclusive = (self.default_button.rect.right - 1, self.default_button.rect.bottom - 1)
        self.assertTrue(self.default_button.is_clicked(border_pos_br_inclusive))

if __name__ == '__main__':
    unittest.main(verbosity=2)

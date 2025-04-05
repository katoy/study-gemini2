import unittest
import pygame
import os
from gui import GameGUI, Screen, Color
from game import Game


class TestGameGUI(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.game = Game()
        self.gui = GameGUI()
        self.gui.screen = pygame.Surface((Screen.WIDTH, Screen.HEIGHT))

        # フォントの読み込みをテスト用に修正
        font_paths = [
            "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",  # macOS
            "/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc",  # macOS
            "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",  # Ubuntu
            "/usr/share/fonts/truetype/fonts-japanese-mincho.ttf",  # Ubuntu
        ]
        font_loaded = False
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    self.gui.font = pygame.font.Font(font_path, 24)
                    font_loaded = True
                except Exception as e:
                    print(f"フォントの読み込みに失敗しました: {e}")

    def test_calculate_board_rect(self):
        board_rect = self.gui._calculate_board_rect()
        self.assertEqual(board_rect.width, Screen.BOARD_SIZE)
        self.assertEqual(board_rect.height, Screen.BOARD_SIZE)
        self.assertEqual(
            board_rect.left, (Screen.WIDTH - Screen.BOARD_SIZE) // 2)
        self.assertEqual(board_rect.top, Screen.BOARD_TOP_MARGIN)

    def test_draw_board_background(self):
        board_rect = self.gui._calculate_board_rect()
        self.gui._draw_board_background(board_rect)
        # Check if the screen is filled with the background color
        self.assertEqual(self.gui.screen.get_at((0, 0)), Color.BACKGROUND)
        # Check if the board is drawn with the board color
        self.assertEqual(self.gui.screen.get_at(
            (board_rect.left + 1, board_rect.top + 1)), Color.BOARD)

    def test_calculate_button_rect(self):
        start_button_rect = self.gui._calculate_button_rect(True)
        self.assertEqual(start_button_rect.width, 141)
        self.assertEqual(start_button_rect.height, 35)
        self.assertEqual(start_button_rect.centerx, Screen.WIDTH // 2 - 1)
        self.assertEqual(start_button_rect.centery, Screen.HEIGHT // 2 - 1)

    def test_draw_board(self):
        self.gui.draw_board(self.game)
        # Check if the screen is filled with the background color
        self.assertEqual(self.gui.screen.get_at((0, 0)), Color.BACKGROUND)

    def test_draw_stone_count(self):
        board_rect = self.gui._calculate_board_rect()
        self.gui._draw_stone_count(self.game, board_rect)
        # Check if the stone count is drawn
        self.assertNotEqual(self.gui.screen.get_at(
            (board_rect.left + 1, board_rect.bottom + 1)), Color.BACKGROUND)

    def test_draw_valid_moves(self):
        self.gui.draw_board(self.game)
        self.gui.draw_valid_moves(self.game)
        # Check if the valid moves are drawn
        self.assertNotEqual(self.gui.screen.get_at(
            (Screen.WIDTH // 2, Screen.HEIGHT // 2)), Color.BOARD)

    def test_draw_message(self):
        self.gui.draw_message("Test Message")
        # Check if the message is drawn
        self.assertNotEqual(self.gui.screen.get_at(
            (Screen.WIDTH // 2, Screen.HEIGHT // 2)), Color.BACKGROUND)

    def test_get_clicked_cell(self):
        board_rect = self.gui._calculate_board_rect()
        row, col = self.gui.get_clicked_cell(
            (board_rect.left + 1, board_rect.top + 1))
        self.assertEqual(row, 0)
        self.assertEqual(col, 0)
        row, col = self.gui.get_clicked_cell(
            (board_rect.right - 1, board_rect.bottom - 1))
        self.assertEqual(row, 7)
        self.assertEqual(col, 7)
        row, col = self.gui.get_clicked_cell((0, 0))
        self.assertEqual(row, -1)
        self.assertEqual(col, -1)

    def test_draw_stone_animation(self):
        self.gui.draw_stone_animation(self.game, 0, 0, Color.BLACK)
        # Check if the stone is drawn
        self.assertEqual(self.gui.screen.get_at(
            (Screen.WIDTH // 2, Screen.HEIGHT // 2)), Color.BLACK)

    def test_draw_flip_animation(self):
        self.gui.draw_flip_animation(self.game, [(0, 0)], Color.BLACK)
        # Check if the stone is drawn
        self.assertEqual(self.gui.screen.get_at(
            (Screen.WIDTH // 2, Screen.HEIGHT // 2)), Color.BLACK)

    def test_draw_start_button(self):
        start_button_rect = self.gui.draw_start_button()
        # Check if the start button is drawn
        self.assertNotEqual(self.gui.screen.get_at(
            (start_button_rect.centerx, start_button_rect.centery)), Color.BACKGROUND)

    def test_draw_restart_button(self):
        restart_button_rect = self.gui.draw_restart_button()
        # Check if the restart button is drawn
        self.assertNotEqual(self.gui.screen.get_at(
            (restart_button_rect.centerx, restart_button_rect.centery)), Color.BACKGROUND)

    def test_draw_reset_button(self):
        reset_button_rect = self.gui.draw_reset_button()
        # Check if the reset button is drawn
        self.assertNotEqual(self.gui.screen.get_at(
            (reset_button_rect.centerx, reset_button_rect.centery)), Color.BACKGROUND)

    def test_is_button_clicked(self):
        start_button_rect = self.gui.draw_start_button()
        self.assertTrue(self.gui.is_button_clicked(
            start_button_rect.center, start_button_rect))
        self.assertFalse(self.gui.is_button_clicked((0, 0), start_button_rect))

    def test_draw_radio_button(self):
        self.gui.draw_radio_button((0, 0), True)
        # Check if the radio button is drawn
        self.assertNotEqual(self.gui.screen.get_at((10, 10)), Color.BACKGROUND)

    def test_draw_text(self):
        self.gui.draw_text("Test Text", (0, 0))
        # Check if the text is drawn
        self.assertNotEqual(self.gui.screen.get_at((10, 10)), Color.BACKGROUND)

    def test_draw_player_settings(self):
        self.gui.draw_player_settings(self.game)
        # Check if the player settings are drawn
        self.assertNotEqual(self.gui.screen.get_at((10, 10)), Color.BACKGROUND)

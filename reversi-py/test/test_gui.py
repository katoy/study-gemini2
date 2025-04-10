# test/test_gui.py
import unittest
import pygame
from unittest.mock import MagicMock, patch
from gui import GameGUI
from config.theme import Color, Screen
from game import Game

class TestGameGUI(unittest.TestCase):
    def setUp(self):
        pygame.init()
        # Create a real screen for testing
        self.gui = GameGUI()
        self.game = Game()
        self.game.set_players(0,0)
        self.screen = pygame.display.set_mode((Screen.WIDTH, Screen.HEIGHT))
        self.gui.screen = self.screen

        # --- font_mock の render が実際の Surface を返すように修正 ---
        self.font_mock = MagicMock(spec=pygame.font.Font)
        # 小さな実際の Surface を作成
        real_surface = pygame.Surface((10, 10))
        # render がこの実際の Surface を返すように設定
        self.font_mock.render.return_value = real_surface
        # get_height はレイアウト計算に必要なのでモックのまま
        self.font_mock.get_height.return_value = 24
        # -------------------------------------------------------
        self.gui.font = self.font_mock

    def tearDown(self):
        pygame.quit()

    def test_draw_board(self):
        self.gui.draw_board(self.game)
        pygame.display.flip()

    def test_draw_valid_moves(self):
        self.game.board.board = [[0 for _ in range(8)] for _ in range(8)]
        self.game.board.board[3][3] = 1
        self.game.board.board[3][4] = -1
        self.game.board.board[4][3] = -1
        self.game.board.board[4][4] = 1
        self.gui.draw_valid_moves(self.game)
        pygame.display.flip()

    def test_draw_message(self):
        self.gui.draw_message("Test Message")
        self.font_mock.render.assert_called_once_with("Test Message", True, Color.WHITE)
        pygame.display.flip()

    def test_draw_message_game_start(self):
        self.gui.draw_message("Test Message", is_game_start=True)
        self.font_mock.render.assert_called_once_with("Test Message", True, Color.WHITE)
        pygame.display.flip()

    def test_draw_message_game_over(self):
        self.gui.draw_message("Test Message", is_game_over=True)
        self.font_mock.render.assert_called_once_with("Test Message", True, Color.WHITE)
        pygame.display.flip()

    def test_get_clicked_cell(self):
        cell_size = Screen.BOARD_SIZE // 8
        board_left = (Screen.WIDTH - Screen.BOARD_SIZE) // 2
        board_top = Screen.BOARD_TOP_MARGIN
        click_x = board_left + cell_size * 3 + cell_size // 2
        click_y = board_top + cell_size * 4 + cell_size // 2
        row, col = self.gui.get_clicked_cell((click_x, click_y))
        self.assertEqual(row, 4)
        self.assertEqual(col, 3)
        row, col = self.gui.get_clicked_cell((0, 0))
        self.assertEqual(row, -1)
        self.assertEqual(col, -1)

    def test_draw_stone_animation(self):
        self.gui.draw_stone_animation(self.game, 3, 3, Color.BLACK)
        pygame.display.flip()

    def test_draw_flip_animation(self):
        self.gui.draw_flip_animation(self.game, [(3, 3), (3, 4)], Color.BLACK)
        pygame.display.flip()

    def test_draw_start_button(self):
        self.gui.draw_start_button()
        pygame.display.flip()

    def test_draw_restart_button(self):
        self.gui.draw_restart_button()
        pygame.display.flip()

    def test_draw_reset_button(self):
        self.gui.draw_reset_button()
        pygame.display.flip()

    def test_is_button_clicked(self):
        button_rect = pygame.Rect(100, 100, 50, 50)
        self.assertTrue(self.gui.is_button_clicked((125, 125), button_rect))
        self.assertFalse(self.gui.is_button_clicked((50, 50), button_rect))
        self.assertFalse(self.gui.is_button_clicked((125, 125), None))

    def test_draw_radio_button(self):
        self.gui.draw_radio_button((100, 100), True)
        pygame.display.flip()

    def test_draw_text(self):
        self.gui.draw_text("Test Text", (100, 100))
        pygame.display.flip()

    def test_draw_player_settings(self):
        player_settings_top = self.gui._calculate_player_settings_top()
        self.gui.draw_player_settings(self.game, player_settings_top)
        pygame.display.flip()

    def test_draw_turn_message(self):
        self.gui.draw_turn_message(self.game)
        pygame.display.flip()

    def test_draw_stone_count(self):
        board_rect = self.gui._calculate_board_rect()
        self.gui._draw_stone_count(self.game, board_rect)
        pygame.display.flip()

    def test_draw_text_with_position(self):
        self.gui._draw_text_with_position("Test Text", Color.BLACK, (100, 100))
        pygame.display.flip()

    def test_draw_text_with_position_right_aligned(self):
        self.gui._draw_text_with_position("Test Text", Color.BLACK, (200, 100), is_right_aligned=True)
        pygame.display.flip()

    def test_draw_board_background(self):
        board_rect = self.gui._calculate_board_rect()
        self.gui._draw_board_background(board_rect)
        pygame.display.flip()

    def test_draw_board_grid(self):
        board_rect = self.gui._calculate_board_rect()
        self.gui._draw_board_grid(board_rect)
        pygame.display.flip()

    def test_draw_stones(self):
        board_rect = self.gui._calculate_board_rect()
        self.gui._draw_stones(self.game.get_board(), board_rect)
        pygame.display.flip()

    def test_draw_stone(self):
        board_rect = self.gui._calculate_board_rect()
        self.gui._draw_stone(board_rect, 3, 3, Color.BLACK)
        pygame.display.flip()

    def test_get_message_y_position(self):
        y_pos = self.gui._get_message_y_position(False, False)
        self.assertGreater(y_pos, 0)

    def test_get_message_y_position_game_start(self):
        y_pos = self.gui._get_message_y_position(True, False)
        self.assertEqual(y_pos, Screen.GAME_START_MESSAGE_TOP_MARGIN)

    def test_get_message_y_position_game_over(self):
        y_pos = self.gui._get_message_y_position(False, True)
        self.assertGreater(y_pos, 0)

    def test_calculate_button_rect_start_button(self):
        rect = self.gui._calculate_button_rect(True)
        self.assertIsNotNone(rect)

    def test_calculate_button_rect_restart_button(self):
        rect = self.gui._calculate_button_rect(False)
        self.assertIsNotNone(rect)

    def test_calculate_button_rect_reset_button(self):
        rect = self.gui._calculate_button_rect(False, is_reset_button=True)
        self.assertIsNotNone(rect)

    def test_calculate_button_rect_game_over(self):
        rect = self.gui._calculate_button_rect(False, game_over=True)
        self.assertIsNotNone(rect)

    def test_draw_button(self):
        button_rect = pygame.Rect(100, 100, 100, 50)
        self.gui._draw_button(button_rect, "Test")
        pygame.display.flip()

    def test_draw_button_border(self):
        button_rect = pygame.Rect(100, 100, 100, 50)
        self.gui._draw_button_border(button_rect)
        pygame.display.flip()

    def test_load_font(self):
        self.assertIsNotNone(self.gui.font)

if __name__ == '__main__':
    unittest.main()

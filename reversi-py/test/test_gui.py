import unittest
import pygame
from gui import GameGUI, Screen  # Screen をインポート
from game import Game

class TestGameGUI(unittest.TestCase):
    def setUp(self):
        self.gui = GameGUI()
        self.game = Game()

    def test_draw_stone_count(self):
        # 必要な引数を追加
        board_width = Screen.BOARD_SIZE  # Screen.BOARD_SIZE を使用
        board_height = Screen.BOARD_SIZE  # Screen.BOARD_SIZE を使用
        board_left = (self.gui.screen_width - board_width) // 2
        board_top = Screen.BOARD_TOP_MARGIN # Screen.BOARD_TOP_MARGIN を使用
        self.gui.draw_stone_count(2, 2, board_left, board_top, board_width, board_height)

    def test_draw_board(self):
        self.gui.draw_board(self.game)

    def test_draw_valid_moves(self):
        self.gui.draw_valid_moves(self.game)

    def test_draw_message(self):
        self.gui.draw_message("Test Message")

    def test_get_clicked_cell(self):
        # ボード内のクリック
        row, col = self.gui.get_clicked_cell((200, 200))
        self.assertTrue(0 <= row < 8)
        self.assertTrue(0 <= col < 8)

        # ボード外のクリック
        row, col = self.gui.get_clicked_cell((0, 0))
        self.assertEqual(row, -1)
        self.assertEqual(col, -1)

    def test_draw_stone_animation(self):
        self.gui.draw_stone_animation(self.game, 3, 3, (0, 0, 0))

    def test_draw_flip_animation(self):
        flipped_stones = [(3, 3), (3, 4)]
        self.gui.draw_flip_animation(self.game, flipped_stones, (0, 0, 0))

    def test_draw_start_button(self):
        self.gui.draw_start_button()

    def test_draw_restart_button(self):
        self.gui.draw_restart_button()
        self.gui.draw_restart_button(True)

    def test_is_button_clicked(self):
        button_rect = pygame.Rect(100, 100, 50, 50)  # pygame.Rect を使用
        self.assertTrue(self.gui.is_button_clicked((125, 125), button_rect))
        self.assertFalse(self.gui.is_button_clicked((0, 0), button_rect))

    def test_draw_radio_button(self):
        self.gui.draw_radio_button((10, 10), True)  # 余分な引数を削除
        self.gui.draw_radio_button((10, 40), False)  # 余分な引数を削除

    def test_draw_text(self):
        self.gui.draw_text("Test Text", (10, 10))
        self.gui.draw_text("Test Text", (10, 40), False)

    def test_draw_player_settings(self):
        self.gui.draw_player_settings(self.game)
        self.gui.draw_player_settings(self.game, True)

if __name__ == '__main__':
    unittest.main()

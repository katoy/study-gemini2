import unittest
import pygame
import sys
import os

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from gui import GameGUI, BLACK, WHITE, GREEN, GRAY, BOARD_COLOR, BACKGROUND_COLOR, BUTTON_COLOR, BUTTON_TEXT_COLOR
from game import Game

class TestGameGUI(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.gui = GameGUI(400, 500)
        self.game = Game()

    def tearDown(self):
        pygame.quit()

    def test_draw_board(self):
        # ボードが正しく描画されるかテスト
        self.gui.draw_board(self.game)
        # ここでは、描画された内容を直接検証することは難しいので、
        # エラーが発生しないことを確認する程度にとどめます。
        # 実際の描画結果を目視で確認する必要があります。
        self.assertTrue(True)

    def test_draw_stone_count(self):
        # 石の数が正しく描画されるかテスト
        self.gui.draw_stone_count(2, 2)
        self.assertTrue(True)

    def test_draw_valid_moves(self):
        # 合法手が正しく描画されるかテスト
        self.gui.draw_valid_moves(self.game)
        self.assertTrue(True)

    def test_draw_message(self):
        # メッセージが正しく描画されるかテスト
        self.gui.draw_message("テストメッセージ")
        self.assertTrue(True)


    def test_draw_stone_animation(self):
        # 石を置くアニメーションが正しく実行されるかテスト
        self.gui.draw_stone_animation(self.game, 2, 3, BLACK)
        self.assertTrue(True)

    def test_draw_flip_animation(self):
        # 石をひっくり返すアニメーションが正しく実行されるかテスト
        flipped_stones = [(3, 3), (3, 4)]
        self.gui.draw_flip_animation(self.game, flipped_stones, WHITE)
        self.assertTrue(True)

    def test_draw_start_button(self):
        # スタートボタンが正しく描画されるかテスト
        button_rect = self.gui.draw_start_button()
        self.assertTrue(isinstance(button_rect, tuple))
        self.assertEqual(len(button_rect), 4)

    def test_draw_restart_button(self):
        # リスタートボタンが正しく描画されるかテスト
        button_rect = self.gui.draw_restart_button()
        self.assertTrue(isinstance(button_rect, tuple))
        self.assertEqual(len(button_rect), 4)

    def test_is_button_clicked(self):
        # ボタンがクリックされたか正しく判定できるかテスト
        button_rect = self.gui.draw_start_button()
        self.assertTrue(self.gui.is_button_clicked((200, 250), button_rect))
        self.assertFalse(self.gui.is_button_clicked((0, 0), button_rect))

if __name__ == '__main__':
    unittest.main()

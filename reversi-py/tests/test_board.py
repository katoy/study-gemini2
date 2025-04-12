# test/test_board.py
import unittest
import sys
import os

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from board import Board


class TestBoard(unittest.TestCase):

    def setUp(self):
        self.board = Board()

    def test_initial_board(self):
        # 初期盤面の確認
        expected_board = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, -1, 0, 0, 0],
            [0, 0, 0, -1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]
        self.assertEqual(self.board.get_board(), expected_board)

    def test_is_valid_move(self):
        # 合法手の確認
        self.assertTrue(self.board.is_valid_move(2, 3, -1))
        self.assertTrue(self.board.is_valid_move(3, 2, -1))
        self.assertTrue(self.board.is_valid_move(4, 5, -1))
        self.assertTrue(self.board.is_valid_move(5, 4, -1))
        self.assertTrue(self.board.is_valid_move(2, 4, 1))
        self.assertTrue(self.board.is_valid_move(3, 5, 1))
        self.assertTrue(self.board.is_valid_move(4, 2, 1))
        self.assertTrue(self.board.is_valid_move(5, 3, 1))

        # 不正な手の確認
        self.assertFalse(self.board.is_valid_move(0, 0, -1))
        self.assertFalse(self.board.is_valid_move(3, 3, -1))
        self.assertFalse(self.board.is_valid_move(4, 4, -1))
        self.assertFalse(self.board.is_valid_move(3, 3, 1))
        self.assertFalse(self.board.is_valid_move(4, 4, 1))
        self.assertFalse(self.board.is_valid_move(-1, 0, -1))
        self.assertFalse(self.board.is_valid_move(0, -1, -1))
        self.assertFalse(self.board.is_valid_move(8, 0, -1))
        self.assertFalse(self.board.is_valid_move(0, 8, -1))

    def test_get_valid_moves(self):
        # 合法手のリストの確認
        valid_moves_black = self.board.get_valid_moves(-1)
        self.assertEqual(len(valid_moves_black), 4)
        self.assertIn((2, 3), valid_moves_black)
        self.assertIn((3, 2), valid_moves_black)
        self.assertIn((4, 5), valid_moves_black)
        self.assertIn((5, 4), valid_moves_black)

        valid_moves_white = self.board.get_valid_moves(1)
        self.assertEqual(len(valid_moves_white), 4)
        self.assertIn((2, 4), valid_moves_white)
        self.assertIn((3, 5), valid_moves_white)
        self.assertIn((4, 2), valid_moves_white)
        self.assertIn((5, 3), valid_moves_white)

    def test_place_stone(self):
        # 石を置くテスト
        self.assertTrue(self.board.place_stone(2, 3, -1))
        expected_board_after_move = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, -1, 0, 0, 0, 0],
            [0, 0, 0, -1, -1, 0, 0, 0],
            [0, 0, 0, -1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]
        self.assertEqual(self.board.get_board(), expected_board_after_move)

        # 不正な場所に石を置くテスト
        self.assertFalse(self.board.place_stone(0, 0, -1))
        self.assertFalse(self.board.place_stone(3, 3, -1))

    def test_count_stones(self):
        # 石の数の確認
        black_count, white_count = self.board.count_stones()
        self.assertEqual(black_count, 2)
        self.assertEqual(white_count, 2)

        self.board.place_stone(2, 3, -1)
        black_count, white_count = self.board.count_stones()
        self.assertEqual(black_count, 4)
        self.assertEqual(white_count, 1)

if __name__ == '__main__':
    unittest.main()

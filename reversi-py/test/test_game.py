import unittest
from game import Game
from board import Board

class TestGame(unittest.TestCase):
    def setUp(self):
        self.game = Game()

    def test_initial_board(self):
        board = self.game.get_board()
        self.assertEqual(board[3][3], 1)
        self.assertEqual(board[4][4], 1)
        self.assertEqual(board[3][4], -1)
        self.assertEqual(board[4][3], -1)

    def test_switch_turn(self):
        self.assertEqual(self.game.turn, -1)
        self.game.switch_turn()
        self.assertEqual(self.game.turn, 1)
        self.game.switch_turn()
        self.assertEqual(self.game.turn, -1)

    def test_place_stone(self):
        # 初期状態では(2, 3)に置けるはず
        self.assertTrue(self.game.place_stone(2, 3))
        self.assertEqual(self.game.get_board()[2][3], -1)
        self.assertEqual(self.game.get_board()[3][3], -1)

        # すでに石がある場所には置けない
        self.assertFalse(self.game.place_stone(2, 3))

        # ターンを切り替えて、(2, 4)に置けるはず
        self.game.switch_turn()
        self.assertTrue(self.game.place_stone(2, 4))
        self.assertEqual(self.game.get_board()[2][4], 1)
        self.assertEqual(self.game.get_board()[3][4], 1)

    def test_get_valid_moves(self):
        # 初期状態での黒の合法手
        valid_moves_black = self.game.get_valid_moves()
        self.assertEqual(len(valid_moves_black), 4)
        self.assertIn((2, 3), valid_moves_black)
        self.assertIn((3, 2), valid_moves_black)
        self.assertIn((4, 5), valid_moves_black)
        self.assertIn((5, 4), valid_moves_black)

        # 黒が(2,3)に置いた後の白の合法手
        self.game.place_stone(2, 3)
        self.game.switch_turn()
        valid_moves_white = self.game.get_valid_moves()
        self.assertEqual(len(valid_moves_white), 3) #修正
        self.assertIn((2, 4), valid_moves_white)
        self.assertIn((2, 2), valid_moves_white)
        self.assertIn((4, 2), valid_moves_white)
        #self.assertIn((5, 3), valid_moves_white) #削除

    def test_check_game_over(self):
        # 初期状態ではゲームオーバーではない
        self.game.check_game_over()
        self.assertFalse(self.game.game_over)

        # すべてのマスを埋めたらゲームオーバーになる
        for row in range(8):
            for col in range(8):
                if self.game.get_board()[row][col] == 0:
                    self.game.place_stone(row, col)
                    if self.game.get_valid_moves():
                        self.game.switch_turn()
        self.game.check_game_over()
        self.assertTrue(self.game.game_over)

    def test_get_winner(self):
        # 初期状態では勝者は決まっていない
        self.assertEqual(self.game.get_winner(), 0)

        # 黒が勝つように盤面を操作
        self.game.board.board = [[-1 for _ in range(8)] for _ in range(8)]
        self.game.board.board[0][0] = 1
        self.assertEqual(self.game.get_winner(), -1)

        # 白が勝つように盤面を操作
        self.game.board.board = [[1 for _ in range(8)] for _ in range(8)]
        self.game.board.board[0][0] = -1
        self.assertEqual(self.game.get_winner(), 1)

        # 引き分けになるように盤面を操作
        self.game.board.board = [[0 for _ in range(8)] for _ in range(8)]
        for i in range(4):
            for j in range(8):
                self.game.board.board[i][j] = -1
        for i in range(4,8):
            for j in range(8):
                self.game.board.board[i][j] = 1
        self.assertEqual(self.game.get_winner(), 0)

    def test_reset(self):
        # 石を置いてからリセット
        self.game.place_stone(2, 3)
        self.game.reset()
        self.assertEqual(self.game.turn, -1)
        self.assertFalse(self.game.game_over)
        self.assertEqual(self.game.get_board()[3][3], 1)
        self.assertEqual(self.game.get_board()[4][4], 1)
        self.assertEqual(self.game.get_board()[3][4], -1)
        self.assertEqual(self.game.get_board()[4][3], -1)

    def test_set_players(self):
        self.game.set_players(1, 2)
        self.assertIsNotNone(self.game.agents[-1])
        self.assertIsNotNone(self.game.agents[1])

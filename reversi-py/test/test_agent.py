# test/test_agent.py
import unittest
from unittest.mock import MagicMock
import sys
import os

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from agent import FirstAgent, RandomAgent, GainAgent
from game import Game
from board import Board

class TestAgents(unittest.TestCase):

    def setUp(self):
        self.game = Game()
        self.game.board = Board()
        self.game.board.board = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, -1, 1, 0, 0, 0],
            [0, 0, 0, 1, -1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]
        self.game.turn = -1

    def test_first_agent(self):
        agent = FirstAgent()
        move = agent.play(self.game)
        self.assertIn(move, self.game.get_valid_moves())

        # 合法手がない場合
        self.game.board.board = [
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
        ]
        move = agent.play(self.game)
        self.assertIsNone(move)

    def test_random_agent(self):
        agent = RandomAgent()
        move = agent.play(self.game)
        self.assertIn(move, self.game.get_valid_moves())

        # 合法手がない場合
        self.game.board.board = [
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
        ]
        move = agent.play(self.game)
        self.assertIsNone(move)

    def test_gain_agent(self):
        agent = GainAgent()
        move = agent.play(self.game)
        self.assertIn(move, self.game.get_valid_moves())

        # 合法手がない場合
        self.game.board.board = [
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1],
        ]
        move = agent.play(self.game)
        self.assertIsNone(move)

        # ゲインが最大になる手を選択しているか
        self.game.board.board = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, -1, 1, 0, 0, 0],
            [0, 0, 0, 1, -1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]
        self.game.turn = -1
        agent = GainAgent()
        move = agent.play(self.game)
        self.assertEqual(move, (2, 4)) # (2,4)に置くと、ひっくり返る数が最大になる

if __name__ == '__main__':
    unittest.main()

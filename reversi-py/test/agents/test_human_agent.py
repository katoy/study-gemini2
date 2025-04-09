# tests/agents/test_human_agent.py
import unittest
from agents.human_agent import HumanAgent
from game import Game

class TestHumanAgent(unittest.TestCase):
    def test_play_does_nothing(self):
        agent = HumanAgent()
        game = Game()
        # HumanAgent.play() は何もしないため、特にアサーションは不要
        agent.play(game)

if __name__ == '__main__':
    unittest.main()

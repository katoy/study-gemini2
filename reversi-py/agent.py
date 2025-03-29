# agent.py
import random

class Agent:
    def play(self, game):
        raise NotImplementedError

class RandomAgent(Agent):
    def play(self, game):
        valid_moves = game.get_valid_moves()
        if valid_moves:
            return random.choice(valid_moves)
        return None

class HumanAgent(Agent):
    def play(self, game):
        # マウス入力から石を置く場所を決定
        # ここでは、main.pyで処理するため、pass
        pass

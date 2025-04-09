# agents/random_agent.py
import random
from .base_agent import Agent

class RandomAgent(Agent):
    def play(self, game):
        valid_moves = game.get_valid_moves()
        if valid_moves:
            return random.choice(valid_moves)
        return None

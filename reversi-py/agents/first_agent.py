# agents/first_agent.py
from .base_agent import Agent

class FirstAgent(Agent):
    def play(self, game):
        valid_moves = game.get_valid_moves()
        if valid_moves:
            return valid_moves[0]
        return None

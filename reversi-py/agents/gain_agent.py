# agents/gain_agent.py
from .base_agent import Agent
from board import Board  # board.py から Board クラスをインポート

class TempGame:
    def __init__(self, board, turn):
        self.board = Board()
        self.board.board = [row[:] for row in board]
        self.turn = turn

    def place_stone(self, row, col):
        self.board.place_stone(row, col, self.turn)

    def get_board(self):
        return self.board.get_board()

    def get_valid_moves(self):
        return self.board.get_valid_moves(self.turn)

class GainAgent(Agent):
    def play(self, game):
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            return None

        best_move = None
        max_gain = -float('inf')

        for move in valid_moves:
            temp_game = TempGame(game.get_board(), game.turn)
            temp_game.place_stone(move[0], move[1])
            black_count, white_count = temp_game.board.count_stones()

            original_black_count, original_white_count = game.board.count_stones()
            if game.turn == -1:
                gain = black_count - original_black_count
            else:
                gain = white_count - original_white_count

            if gain > max_gain:
                max_gain = gain
                best_move = move

        return best_move

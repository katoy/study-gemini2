# agent.py
import random
# from game import Game  # Game クラスのインポートを削除

class Agent:
    def play(self, game):
        raise NotImplementedError

class FirstAgent(Agent):
    def play(self, game):
        valid_moves = game.get_valid_moves()
        if valid_moves:
            return valid_moves[0]
        return None

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

class GainAgent(Agent):
    def play(self, game):
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            return None

        best_move = None
        max_gain = -1

        for move in valid_moves:
            # Game クラスのインスタンスを作成
            class Game:
                def __init__(self):
                    from board import Board
                    self.board = Board()
                    self.turn = game.turn
                def place_stone(self, row, col):
                    self.board.place_stone(row, col, self.turn)
                def get_board(self):
                    return self.board.get_board()
            temp_game = Game()
            temp_game.board.board = [row[:] for row in game.get_board()]
            temp_game.turn = game.turn
            temp_game.place_stone(move[0], move[1])
            black_count, white_count = temp_game.board.count_stones()
            gain = black_count if game.turn == -1 else white_count

            if gain > max_gain:
                max_gain = gain
                best_move = move

        return best_move

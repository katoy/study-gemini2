# game.py
from board import Board

class Game:
    def __init__(self, board_size=8):
        self.board = Board(board_size)
        self.turn = -1  # 黒から開始
        self.game_over = False
        self.board_size = board_size

    def switch_turn(self):
        self.turn *= -1

    def check_game_over(self):
        if not self.board.get_valid_moves(-1) and not self.board.get_valid_moves(1):
            self.game_over = True

    def get_winner(self):
        black_count, white_count = self.board.count_stones()
        if black_count > white_count:
            return -1  # 黒の勝ち
        elif white_count > black_count:
            return 1  # 白の勝ち
        else:
            return 0  # 引き分け

    def place_stone(self, row, col):
        return self.board.place_stone(row, col, self.turn)

    def get_valid_moves(self):
        return self.board.get_valid_moves(self.turn) # 修正箇所

    def get_board(self):
        return self.board.get_board()

    def get_board_size(self):
        return self.board_size

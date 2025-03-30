# board.py
class Board:
    def __init__(self, board_size=8):
        self.board_size = board_size
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.board[self.board_size // 2 - 1][self.board_size // 2 - 1] = self.board[self.board_size // 2][self.board_size // 2] = 1  # 白
        self.board[self.board_size // 2 - 1][self.board_size // 2] = self.board[self.board_size // 2][self.board_size // 2 - 1] = -1 # 黒

    def is_valid_move(self, row, col, turn):
        if not (0 <= row < self.board_size and 0 <= col < self.board_size) or self.board[row][col] != 0:
            return False

        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                flipped = False
                while 0 <= r < self.board_size and 0 <= c < self.board_size:
                    if self.board[r][c] == 0:
                        break
                    if self.board[r][c] == turn:
                        if flipped:
                            return True
                        break
                    flipped = True
                    r += dr
                    c += dc
        return False

    def get_valid_moves(self, turn):
        valid_moves = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.is_valid_move(row, col, turn):
                    valid_moves.append((row, col))
        return valid_moves

    def place_stone(self, row, col, turn):
        if not self.is_valid_move(row, col, turn):
            return False

        self.board[row][col] = turn
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                to_flip = []
                while 0 <= r < self.board_size and 0 <= c < self.board_size:
                    if self.board[r][c] == 0:
                        break
                    if self.board[r][c] == turn:
                        for fr, fc in to_flip:
                            self.board[fr][fc] = turn
                        break
                    to_flip.append((r, c))
                    r += dr
                    c += dc
        return True

    def count_stones(self):
        black_count = sum(row.count(-1) for row in self.board)
        white_count = sum(row.count(1) for row in self.board)
        return black_count, white_count

    def get_board(self):
        return self.board

    def get_flipped_stones(self, row, col, turn):
        flipped_stones = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                to_flip = []
                while 0 <= r < self.board_size and 0 <= c < self.board_size:
                    if self.board[r][c] == 0:
                        break
                    if self.board[r][c] == turn:
                        flipped_stones.extend(to_flip)
                        break
                    to_flip.append((r, c))
                    r += dr
                    c += dc
        return flipped_stones
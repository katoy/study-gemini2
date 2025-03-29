# reversi.py
class Reversi:
    def __init__(self, board_size=8):
        self.board_size = board_size
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.board[self.board_size // 2 - 1][self.board_size // 2 - 1] = self.board[self.board_size // 2][self.board_size // 2] = 1  # 白
        self.board[self.board_size // 2 - 1][self.board_size // 2] = self.board[self.board_size // 2][self.board_size // 2 - 1] = -1 # 黒
        self.turn = -1  # 黒から開始
        self.game_over = False

    def is_valid_move(self, row, col, turn):
        # 盤面の範囲外、すでに石がある場所は無効
        if not (0 <= row < self.board_size and 0 <= col < self.board_size) or self.board[row][col] != 0:
            return False

        # 8方向をチェック
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
        # 8方向をチェックして石をひっくり返す
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

    def switch_turn(self):
        self.turn *= -1

    def check_game_over(self):
        if not self.get_valid_moves(-1) and not self.get_valid_moves(1):
            self.game_over = True

    def get_winner(self):
        black_count = sum(row.count(-1) for row in self.board)
        white_count = sum(row.count(1) for row in self.board)
        if black_count > white_count:
            return -1  # 黒の勝ち
        elif white_count > black_count:
            return 1  # 白の勝ち
        else:
            return 0  # 引き分け

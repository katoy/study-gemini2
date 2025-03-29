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
            # temp_game = Game()  # Game クラスのインスタンスを作成
            # temp_game.board.board = [row[:] for row in game.get_board()]
            # temp_game.turn = game.turn
            # temp_game.place_stone(move[0], move[1])
            # black_count, white_count = temp_game.board.count_stones()
            # gain = black_count if game.turn == -1 else white_count
            temp_board = [row[:] for row in game.get_board()]
            temp_turn = game.turn
            temp_black_count, temp_white_count = self.simulate_place_stone(temp_board, move[0], move[1], temp_turn, game.get_board_size())
            gain = temp_black_count if game.turn == -1 else temp_white_count

            if gain > max_gain:
                max_gain = gain
                best_move = move

        return best_move

    def simulate_place_stone(self, board, row, col, turn, board_size):
        if not self.is_valid_move(board, row, col, turn, board_size):
            return 0, 0

        board[row][col] = turn
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                to_flip = []
                while 0 <= r < board_size and 0 <= c < board_size:
                    if board[r][c] == 0:
                        break
                    if board[r][c] == turn:
                        for fr, fc in to_flip:
                            board[fr][fc] = turn
                        break
                    to_flip.append((r, c))
                    r += dr
                    c += dc
        black_count = sum(row.count(-1) for row in board)
        white_count = sum(row.count(1) for row in board)
        return black_count, white_count

    def is_valid_move(self, board, row, col, turn, board_size):
        if not (0 <= row < board_size and 0 <= col < board_size) or board[row][col] != 0:
            return False

        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                flipped = False
                while 0 <= r < board_size and 0 <= c < board_size:
                    if board[r][c] == 0:
                        break
                    if board[r][c] == turn:
                        if flipped:
                            return True
                        break
                    flipped = True
                    r += dr
                    c += dc
        return False

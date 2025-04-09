# agents/gain_agent.py
import random  # random モジュールをインポート
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

        move_gains = [] # 各手の獲得数を保存するリスト [(move, gain), ...]
        max_gain = -1   # 獲得数は0以上なので、-1で初期化しても良い

        # 1. 全ての有効な手を評価し、獲得数を計算
        for move in valid_moves:
            temp_game = TempGame(game.get_board(), game.turn)
            # place_stone は反転後の盤面を返すわけではないので、獲得数を計算する必要がある
            # get_flipped_stones を使う方が効率的かもしれないが、既存ロジックを踏襲
            flipped_stones = temp_game.board.get_flipped_stones(move[0], move[1], game.turn)
            gain = len(flipped_stones) # 獲得数は反転した石の数

            move_gains.append((move, gain)) # 手と獲得数をタプルで保存

            # 2. 最大の獲得数を更新
            if gain > max_gain:
                max_gain = gain

        # 3. 最大の獲得数を持つ手のリストを作成
        best_moves = [move for move, gain in move_gains if gain == max_gain]

        # 4 & 5. best_moves のリストから手を選択
        if not best_moves: # 念のため (通常は起こらないはず)
             # もし万が一 best_moves が空なら、有効な手の中からランダムに選ぶ (フォールバック)
             return random.choice(valid_moves) if valid_moves else None
        elif len(best_moves) == 1:
             return best_moves[0] # 候補が1つならそれを返す
        else:
             # 候補が複数ならランダムに選ぶ
             return random.choice(best_moves)

# agents/gain_agent.py
import random
from .base_agent import Agent
# Board クラスは get_flipped_stones を使うために必要
from board import Board

# --- TempGame クラス定義を削除 ---

class GainAgent(Agent):
    def play(self, game):
        """
        有効な手の中から、最も多くの石を獲得できる手を選択します。
        複数の手が同じ数の石を獲得できる場合、その中からランダムに1つの手を選択します。

        Args:
            game: Gameオブジェクトのようなインターフェースを持つオブジェクト
                  (get_valid_moves, board.get_flipped_stones を持つ)
        Returns:
            tuple[int, int] | None: 選択された手の座標 (row, col)。有効な手がない場合は None。
        """
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            return None

        move_gains = [] # 各手の獲得数を保存するリスト [(move, gain), ...]
        max_gain = -1   # 獲得数は0以上なので、-1で初期化しても良い

        # 全ての有効な手を評価し、獲得数を計算
        for move in valid_moves:
            flipped_stones = game.board.get_flipped_stones(move[0], move[1], game.turn)
            gain = len(flipped_stones) # 獲得数は反転した石の数

            move_gains.append((move, gain)) # 手と獲得数をタプルで保存

            # 最大の獲得数を更新
            if gain > max_gain:
                max_gain = gain

        # 最大の獲得数を持つ手のリストを作成
        best_moves = [move for move, gain in move_gains if gain == max_gain]

        # best_moves のリストから手を選択
        if len(best_moves) == 1:
            return best_moves[0] # 候補が1つならそれを返す
        else:
            # 候補が複数ならランダムに選ぶ
            return random.choice(best_moves)

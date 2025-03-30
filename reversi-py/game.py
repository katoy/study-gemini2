# game.py
from board import Board
from agent import RandomAgent, GainAgent, FirstAgent  # Agentクラスをインポート

class Game:
    def __init__(self, board_size=8):
        self.board = Board(board_size)
        self.turn = -1  # 黒から開始
        self.game_over = False
        self.board_size = board_size
        self.history = []  # プレイの履歴を保存するリスト
        self.history_index = -1 #履歴のインデックス
        self.players = [-1, 1] #プレイヤーのタイプ
        self.agents = {
            -1: None,  # 黒のプレイヤー（デフォルトは人間）
            1: None   # 白のプレイヤー（デフォルトは人間）
        }
        self.message = "ゲーム開始" #初期メッセージ

    def reset(self):
        self.board = Board(self.board_size)
        self.turn = -1
        self.game_over = False
        self.history = []
        self.history_index = -1
        self.message = "ゲーム開始"

    def switch_turn(self):
        self.turn *= -1
        self.set_message(f"{'黒' if self.turn == -1 else '白'}の番です") #ターン切り替え時のメッセージ

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
        if self.board.place_stone(row, col, self.turn):
            self.history.append(((row, col), self.turn, self.board.get_board()))  # 履歴に記録
            self.history_index += 1
            return True
        return False

    def get_flipped_stones(self, row, col, turn):
        return self.board.get_flipped_stones(row, col, turn)

    def get_valid_moves(self):
        return self.board.get_valid_moves(self.turn)

    def get_board(self):
        return self.board.get_board()

    def get_board_size(self):
        return self.board_size

    def set_players(self, player1_type, player2_type):
        self.players = [-1, 1]
        self.agents[-1] = self.create_agent(player1_type)
        self.agents[1] = self.create_agent(player2_type)

    def create_agent(self, agent_type):
        if agent_type == 0:
            return None
        elif agent_type == 1:
            return FirstAgent()
        elif agent_type == 2:
            return RandomAgent()
        elif agent_type == 3:
            return GainAgent()
        else:
            return None

    def set_message(self, message):
        self.message = message

    def get_message(self):
        return self.message

    def replay(self, index):
        if 0 <= index < len(self.history):
            self.board.board = [row[:] for row in self.history[index][2]]
            self.turn = self.history[index][1]
            self.history_index = index
            return True
        return False

    def history_top(self):
        if len(self.history) > 0:
            self.replay(0)

    def history_last(self):
        if len(self.history) > 0:
            self.replay(len(self.history) - 1)

    def get_current_history(self):
        if self.history_index >= 0:
            return self.history[self.history_index]
        return None

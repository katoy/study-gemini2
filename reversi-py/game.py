# game.py
from board import Board
# config.agents からヘルパー関数をインポート
from config.agents import get_agent_class, get_agent_params


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
        self.message = "" #初期メッセージをクリア

    def reset(self):
        self.board = Board(self.board_size)
        self.turn = -1
        self.game_over = False
        self.history = []
        self.history_index = -1
        self.message = "" #リセット時にメッセージをクリア
        # プレイヤー設定を初期化
        self.agents = {
            -1: None,  # 黒のプレイヤー（デフォルトは人間）
            1: None   # 白のプレイヤー（デフォルトは人間）
        }

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
        if self.board.place_stone(row, col, self.turn):
            # 履歴には盤面のコピーを保存する
            board_copy = [r[:] for r in self.board.get_board()] # ディープコピーを作成
            self.history.append(((row, col), self.turn, board_copy)) # コピーを履歴に追加
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

    def set_players(self, black_player_id, white_player_id):
        """
        プレイヤーの種類をIDで設定する。
        Args:
            black_player_id (int): 黒プレイヤーのエージェントID (config.agents.py で定義)
            white_player_id (int): 白プレイヤーのエージェントID (config.agents.py で定義)
        """
        self.agents[-1] = self.create_agent(black_player_id)
        self.agents[1] = self.create_agent(white_player_id)

    def create_agent(self, agent_id):
        """
        指定されたIDに基づいてエージェントのインスタンスを生成する。
        Args:
            agent_id (int): エージェントID (config.agents.py で定義)
        Returns:
            Agent | None: 生成されたエージェントインスタンス、または人間プレイヤーや不明なIDの場合は None。
        """
        agent_class = get_agent_class(agent_id)
        if agent_class is None:
            # 人間プレイヤー (id=0) または 不明なID
            return None
        else:
            params = get_agent_params(agent_id)
            try:
                # パラメータがある場合は展開して渡す
                return agent_class(**params)
            except TypeError as e:
                print(f"エラー: エージェント {agent_class.__name__} (ID: {agent_id}) の初期化に失敗しました。")
                print(f"  期待されるパラメータと渡されたパラメータを確認してください: {params}")
                print(f"  エラー詳細: {e}")
                return None # エラー時は None を返す
            except Exception as e:
                print(f"エラー: エージェント {agent_class.__name__} (ID: {agent_id}) の初期化中に予期せぬエラーが発生しました。")
                print(f"  パラメータ: {params}")
                print(f"  エラー詳細: {e}")
                return None # エラー時は None を返す

    def set_message(self, message):
        self.message = message

    def get_message(self):
        return self.message

    def replay(self, index):
        """指定されたインデックスの履歴状態に盤面と手番を復元する"""
        if 0 <= index < len(self.history):
            # 履歴から盤面状態を復元 (コピーを渡す)
            self.board.board = [row[:] for row in self.history[index][2]]
            # 履歴から手番を復元
            self.turn = self.history[index][1]
            self.history_index = index
            # ゲームオーバー状態もリセットしておく（履歴再生時は通常ゲームオーバーではない）
            self.game_over = False
            return True
        return False

    def history_top(self):
        """履歴の最初の状態に戻る"""
        if len(self.history) > 0:
            # replay の戻り値を返すように修正
            return self.replay(0)
        return False # 履歴がない場合は False を返す

    def history_last(self):
        """履歴の最後の状態（最新の状態）に戻る"""
        if len(self.history) > 0:
            # replay の戻り値を返すように修正
            return self.replay(len(self.history) - 1)
        return False # 履歴がない場合は False を返す

    def get_current_history(self):
        """現在の履歴インデックスに対応する履歴データを取得する"""
        if 0 <= self.history_index < len(self.history): # <<< 修正
            return self.history[self.history_index]
        return None

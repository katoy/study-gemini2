# game.py
from board import Board
# config.agents からヘルパー関数をインポート
from config.agents_config import get_agent_class
from config.agent_config_utils import get_agent_params


class Game:
    """リバーシゲームの制御。ゲームロジックと盤面管理を担当。

    責務：
    - 盤面管理：Board インスタンスを保有、石の配置
    - ターン管理：手番（黒=-1, 白=1）の切り替え
    - プレイヤー管理：各プレイヤーのエージェント（AI または人間）
    - ゲーム状態：勝敗判定、パス判定、ゲームオーバー
    - 履歴管理：巻き戻し機能用の手数履歴

    設計上の注記：
    - Board と Game を分離することで責務が明確（ボード操作 vs ゲーム流れ）
    - agents 辞書でプレイヤーの AI インスタンスを保有
    - agent_ids で現在選択中のエージェント ID を管理

    属性：
        board (Board): 盤面
        turn: 現在の手番（-1=黒, 1=白）
        agents: エージェントインスタンス {-1: agent_black, 1: agent_white}
        agent_ids: エージェント ID {-1: id_black, 1: id_white}
        history: 手数履歴（盤面状態の列）
        history_index: 履歴内の現在位置
    """
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
        self.agent_ids = {
            -1: 0,  # 黒のエージェント ID（デフォルトは 0 = 人間）
            1: 0    # 白のエージェント ID（デフォルトは 0 = 人間）
        }
        self.message = "" #初期メッセージをクリア
        # 有効手のキャッシング（毎ターン1回だけ計算）
        self._valid_moves_cache = None
        self._valid_moves_turn = None

    def _invalidate_valid_moves_cache(self):
        """合法手キャッシュを無効化する。"""
        self._valid_moves_cache = None
        self._valid_moves_turn = None

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
        self.agent_ids = {
            -1: 0,  # 黒のエージェント ID（デフォルトは 0 = 人間）
            1: 0    # 白のエージェント ID（デフォルトは 0 = 人間）
        }
        # 有効手キャッシュをリセット
        self._invalidate_valid_moves_cache()

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
            self._invalidate_valid_moves_cache()
            # 履歴には盤面のコピーを保存する
            board_copy = [r[:] for r in self.board.get_board()] # ディープコピーを作成
            self.history.append(((row, col), self.turn, board_copy)) # コピーを履歴に追加
            self.history_index += 1
            return True
        return False

    def get_flipped_stones(self, row, col, turn):
        return self.board.get_flipped_stones(row, col, turn)

    def get_valid_moves(self):
        # ターンが変わらなければキャッシュを使用
        if self._valid_moves_turn != self.turn:
            self._valid_moves_cache = self.board.get_valid_moves(self.turn)
            self._valid_moves_turn = self.turn
        return self._valid_moves_cache

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
        self.agent_ids[-1] = black_player_id
        self.agent_ids[1] = white_player_id
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
        if index == -1:
            # 初期状態に戻す
            agents_backup = self.agents.copy() # プレイヤー設定は維持
            self.reset()
            self.agents = agents_backup
            return True

        if 0 <= index < len(self.history):
            # 履歴から盤面状態を復元 (コピーを渡す)
            self.board.board = [row[:] for row in self.history[index][2]]
            # 履歴から手番を復元
            self.turn = self.history[index][1]
            self.history_index = index
            # ゲームオーバー状態もリセットしておく（履歴再生時は通常ゲームオーバーではない）
            self.game_over = False
            self._invalidate_valid_moves_cache()
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

# test/test_game.py
import unittest
import sys
import os
from unittest.mock import MagicMock

# プロジェクトルートへのパスを追加 (test ディレクトリから見て親ディレクトリ)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from game import Game
from board import Board
# config.agents から ID 定義やクラスを参照するためにインポート
# from config import agents as agents_config # ID を直接使うので不要かも
# agents モジュールからクラスをインポート (isinstance チェック用)
from agents import FirstAgent, RandomAgent, GainAgent, MonteCarloTreeSearchAgent

class TestGame(unittest.TestCase):
    def setUp(self):
        # self.gui = GameGUI()
        self.game = Game()
        # self.gui.screen

    def test_initial_board(self):
        board = self.game.get_board()
        self.assertEqual(board[3][3], 1)
        self.assertEqual(board[4][4], 1)
        self.assertEqual(board[3][4], -1)
        self.assertEqual(board[4][3], -1)
        self.assertEqual(self.game.turn, -1)
        self.assertFalse(self.game.game_over)
        self.assertEqual(self.game.history, [])
        self.assertEqual(self.game.history_index, -1)
        self.assertIsNone(self.game.agents[-1]) # 初期プレイヤーは人間 (None)
        self.assertIsNone(self.game.agents[1]) # 初期プレイヤーは人間 (None)

    def test_switch_turn(self):
        self.assertEqual(self.game.turn, -1)
        self.game.switch_turn()
        self.assertEqual(self.game.turn, 1)
        self.game.switch_turn()
        self.assertEqual(self.game.turn, -1)

    def test_place_stone_updates_history(self):
        """place_stone が正しく石を置き、履歴を更新するかテスト"""
        initial_board_copy = [row[:] for row in self.game.get_board()]
        self.assertEqual(len(self.game.history), 0)
        self.assertEqual(self.game.history_index, -1)

        # 1手目 (黒)
        self.assertTrue(self.game.place_stone(2, 3))
        self.assertEqual(self.game.get_board()[2][3], -1, "石が置かれているべき")
        self.assertEqual(self.game.get_board()[3][3], -1, "石がひっくり返るべき")
        self.assertEqual(len(self.game.history), 1, "履歴が1つ増えるべき")
        self.assertEqual(self.game.history_index, 0, "履歴インデックスが更新されるべき")

        # 履歴の内容を確認
        move1, turn1, board1 = self.game.history[0]
        self.assertEqual(move1, (2, 3))
        self.assertEqual(turn1, -1)
        self.assertIsInstance(board1, list)
        self.assertNotEqual(id(board1), id(self.game.board.board), "履歴の盤面はコピーであるべき")

        # 1手目の盤面状態を確認
        expected_board1 = [row[:] for row in initial_board_copy]
        expected_board1[2][3] = -1
        expected_board1[3][3] = -1 # ひっくり返る
        self.assertEqual(board1, expected_board1, "履歴に保存された盤面が正しくない")

        # 不正な手
        self.assertFalse(self.game.place_stone(0, 0)) # 合法手ではない
        self.assertEqual(len(self.game.history), 1, "不正な手では履歴は増えない")
        self.assertEqual(self.game.history_index, 0, "不正な手では履歴インデックスは変わらない")
        self.assertFalse(self.game.place_stone(2, 3)) # すでに石がある
        self.assertEqual(len(self.game.history), 1)
        self.assertEqual(self.game.history_index, 0)

    def test_get_valid_moves(self):
        # 初期状態での黒の合法手
        valid_moves_black = self.game.get_valid_moves()
        self.assertEqual(len(valid_moves_black), 4)
        self.assertIn((2, 3), valid_moves_black)
        self.assertIn((3, 2), valid_moves_black)
        self.assertIn((4, 5), valid_moves_black)
        self.assertIn((5, 4), valid_moves_black)

        # 黒が(2,3)に置いた後の白の合法手
        self.game.place_stone(2, 3)
        self.game.switch_turn()
        valid_moves_white = self.game.get_valid_moves()
        self.assertEqual(len(valid_moves_white), 3)
        self.assertIn((2, 4), valid_moves_white)
        self.assertIn((2, 2), valid_moves_white)
        self.assertIn((4, 2), valid_moves_white)

    def test_check_game_over(self):
        # 初期状態ではゲームオーバーではない
        self.game.check_game_over()
        self.assertFalse(self.game.game_over)

        # 両者パスの状態を作る (例: 盤面を埋める)
        # 簡単のため、Board オブジェクトを直接操作してパス状態にする
        self.game.board = MagicMock(spec=Board)
        self.game.board.get_valid_moves.return_value = [] # 常に空リストを返すようにモック
        self.game.check_game_over()
        self.assertTrue(self.game.game_over)

    def test_get_winner(self):
        # 初期状態では引き分け (石の数が同じ)
        self.assertEqual(self.game.get_winner(), 0)

        # 黒が勝つように盤面を操作
        self.game.board.board = [[-1 for _ in range(8)] for _ in range(8)]
        self.game.board.board[0][0] = 1 # 1つだけ白
        self.assertEqual(self.game.get_winner(), -1)

        # 白が勝つように盤面を操作
        self.game.board.board = [[1 for _ in range(8)] for _ in range(8)]
        self.game.board.board[0][0] = -1 # 1つだけ黒
        self.assertEqual(self.game.get_winner(), 1)

        # 引き分けになるように盤面を操作 (例: 半分ずつ)
        self.game.board.board = [[0 for _ in range(8)] for _ in range(8)]
        for i in range(4):
            for j in range(8):
                self.game.board.board[i][j] = -1
        for i in range(4, 8):
            for j in range(8):
                self.game.board.board[i][j] = 1
        self.assertEqual(self.game.get_winner(), 0)

    def test_reset(self):
        # 何かゲームを進めてからリセット
        self.game.set_players(1, 4) # First vs MCTS
        self.game.place_stone(2, 3)
        self.game.switch_turn()
        self.game.place_stone(2, 4)
        self.game.game_over = True
        self.game.message = "Test Message"

        self.game.reset()

        # 初期状態に戻っているか確認
        self.assertEqual(self.game.turn, -1)
        self.assertFalse(self.game.game_over)
        self.assertEqual(self.game.history, [])
        self.assertEqual(self.game.history_index, -1)
        self.assertEqual(self.game.message, "")
        # agents もリセットされているか確認
        self.assertIsNone(self.game.agents[-1], "リセット後、黒プレイヤーは None であるべき")
        self.assertIsNone(self.game.agents[1], "リセット後、白プレイヤーは None であるべき")
        # 盤面が初期状態か確認
        initial_board = Board().get_board()
        self.assertEqual(self.game.get_board(), initial_board, "リセット後の盤面が初期状態でない")

    def test_set_players(self):
        """set_players が正しくエージェントを設定するかテスト"""
        human_id = 0
        first_agent_id = 1
        random_agent_id = 2
        mcts_agent_id = 4

        # 人間 vs MCTS
        self.game.set_players(human_id, mcts_agent_id)
        self.assertIsNone(self.game.agents[-1], "黒プレイヤー (人間) は None であるべき")
        self.assertIsInstance(self.game.agents[1], MonteCarloTreeSearchAgent, "白プレイヤーは MCTS のインスタンスであるべき")

        # First vs Random
        self.game.set_players(first_agent_id, random_agent_id)
        self.assertIsInstance(self.game.agents[-1], FirstAgent, "黒プレイヤーは FirstAgent のインスタンスであるべき")
        self.assertIsInstance(self.game.agents[1], RandomAgent, "白プレイヤーは RandomAgent のインスタンスであるべき")

        # 不明なID を含む場合 (create_agent が None を返す)
        self.game.set_players(999, first_agent_id)
        self.assertIsNone(self.game.agents[-1], "不明なIDの場合、エージェントは None であるべき")
        self.assertIsInstance(self.game.agents[1], FirstAgent)

    def test_create_agent(self):
        """create_agent が ID に基づいて正しくエージェントを生成するかテスト"""
        # 人間 (ID: 0)
        self.assertIsNone(self.game.create_agent(0), "ID 0 は None を返すべき")
        # FirstAgent (ID: 1)
        agent1 = self.game.create_agent(1)
        self.assertIsInstance(agent1, FirstAgent, "ID 1 は FirstAgent インスタンスを返すべき")
        # RandomAgent (ID: 2)
        agent2 = self.game.create_agent(2)
        self.assertIsInstance(agent2, RandomAgent, "ID 2 は RandomAgent インスタンスを返すべき")
        # GainAgent (ID: 3)
        agent3 = self.game.create_agent(3)
        self.assertIsInstance(agent3, GainAgent, "ID 3 は GainAgent インスタンスを返すべき")
        # MCTS Agent (ID: 4, パラメータ付き)
        agent4 = self.game.create_agent(4)
        self.assertIsInstance(agent4, MonteCarloTreeSearchAgent, "ID 4 は MCTS インスタンスを返すべき")
        # MCTS のパラメータが設定されているか（簡易チェック）
        # config/agents.py で定義された値と比較
        self.assertEqual(agent4.iterations, 50000)
        self.assertEqual(agent4.time_limit_ms, 4000)
        self.assertEqual(agent4.exploration_weight, 1.41)
        # 存在しないID
        self.assertIsNone(self.game.create_agent(999), "存在しないIDは None を返すべき")

    def test_replay(self):
        """replay が正しく盤面、手番、インデックスを復元するかテスト"""
        # 3手進める
        self.assertTrue(self.game.place_stone(2, 3), "1手目(黒 2,3)が失敗") # 黒 (index 0)
        board_state_0 = [row[:] for row in self.game.get_board()]
        turn_0 = self.game.turn
        self.game.switch_turn()
        self.assertTrue(self.game.place_stone(2, 4), "2手目(白 2,4)が失敗") # 白 (index 1)
        board_state_1 = [row[:] for row in self.game.get_board()]
        turn_1 = self.game.turn
        self.game.switch_turn()
        self.assertTrue(self.game.place_stone(3, 5), "3手目(黒 3,5)が失敗") # 黒 (index 2)
        board_state_2 = [row[:] for row in self.game.get_board()]
        turn_2 = self.game.turn
        self.game.switch_turn() # 次は白の番

        # 3手進めた後の履歴数を確認
        self.assertEqual(len(self.game.history), 3, "3手進めた後の履歴数が3ではありません")

        # 1手目の状態に戻す (index=0)
        self.assertTrue(self.game.replay(0), "replay(0) が False を返しました")
        self.assertEqual(self.game.history_index, 0, "replay(0)後のインデックスが違う")
        self.assertEqual(self.game.turn, self.game.history[0][1], "replay(0)後の手番が履歴と一致しない")
        self.assertEqual(self.game.get_board(), self.game.history[0][2], "replay(0)後の盤面が履歴と一致しない")
        self.assertFalse(self.game.game_over, "replay後はgame_overフラグがFalseであるべき")

        # 最新の状態に戻す (index=2)
        self.assertTrue(self.game.replay(2), f"replay(2) が False を返しました (history len: {len(self.game.history)})")
        self.assertEqual(self.game.history_index, 2, "replay(2)後のインデックスが違う")
        self.assertEqual(self.game.turn, self.game.history[2][1], "replay(2)後の手番が履歴と一致しない")
        self.assertEqual(self.game.get_board(), self.game.history[2][2], "replay(2)後の盤面が履歴と一致しない")
        self.assertFalse(self.game.game_over, "replay後はgame_overフラグがFalseであるべき")

        # 範囲外のインデックス
        current_index = self.game.history_index
        current_turn = self.game.turn
        current_board = [row[:] for row in self.game.get_board()]
        self.assertFalse(self.game.replay(-1))
        self.assertFalse(self.game.replay(len(self.game.history)))
        # 状態が変わっていないことを確認
        self.assertEqual(self.game.history_index, current_index)
        self.assertEqual(self.game.turn, current_turn)
        self.assertEqual(self.game.get_board(), current_board)

    def test_history_top_last(self):
        """history_top と history_last が正しく動作するかテスト"""
        # 履歴がない場合
        self.assertFalse(self.game.history_top())
        self.assertFalse(self.game.history_last())

        # 2手進める
        self.game.place_stone(2, 3) # 黒 (index 0)
        self.game.switch_turn()
        self.game.place_stone(2, 4) # 白 (index 1)
        self.game.switch_turn() # 次は黒の番

        # history_top (index=0 の状態になるはず)
        self.assertTrue(self.game.history_top())
        self.assertEqual(self.game.history_index, 0)
        move1, turn1, board1 = self.game.history[0]
        self.assertEqual(self.game.turn, turn1)
        self.assertEqual(self.game.get_board(), board1)

        # history_last (index=1 の状態になるはず)
        self.assertTrue(self.game.history_last())
        self.assertEqual(self.game.history_index, len(self.game.history) - 1)
        move_last, turn_last, board_last = self.game.history[-1]
        self.assertEqual(self.game.turn, turn_last)
        self.assertEqual(self.game.get_board(), board_last)

    def test_get_current_history(self):
        """get_current_history が正しい履歴データを返すかテスト"""
        # 履歴がない場合
        self.assertIsNone(self.game.get_current_history())

        # 1手進める
        self.game.place_stone(2, 3) # 黒 (index 0)
        expected_history_data_0 = self.game.history[0]
        self.assertEqual(self.game.get_current_history(), expected_history_data_0)

        # 2手目
        self.game.switch_turn()
        self.game.place_stone(2, 4) # 白 (index 1)
        expected_history_data_1 = self.game.history[1]
        self.assertEqual(self.game.get_current_history(), expected_history_data_1)

        # replay で戻る
        self.game.replay(0)
        self.assertEqual(self.game.get_current_history(), expected_history_data_0)

    def test_set_get_message(self):
        """set_message と get_message が正しく動作するかテスト"""
        self.assertEqual(self.game.get_message(), "")
        self.game.set_message("テストメッセージ")
        self.assertEqual(self.game.get_message(), "テストメッセージ")
        self.game.set_message("")
        self.assertEqual(self.game.get_message(), "")


if __name__ == '__main__':
    unittest.main(verbosity=2)

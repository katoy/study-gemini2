# test/test_game.py
import unittest
import sys
import os
from unittest.mock import MagicMock, patch, call

# プロジェクトルートへのパスを追加 (test ディレクトリから見て親ディレクトリ)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from game import Game
from board import Board
from agents.first_agent import FirstAgent
from agents.random_agent import RandomAgent
from agents.gain_agent import GainAgent
from agents.mcts_agent import MonteCarloTreeSearchAgent
# --- config.agents から必要なものをインポート (create_agent のテストで使用) ---
# AGENT_DEFINITIONS をインポートして FirstAgent の ID を取得
from config.agents import AGENT_DEFINITIONS, get_agent_class as original_get_agent_class
from config.agent_config_utils import get_agent_params

class TestGame(unittest.TestCase):
    def setUp(self):
        self.game = Game()

    # === 基本的なテストメソッド (カバレッジ向上のため追加) ===
    def test_initial_state(self):
        self.assertEqual(self.game.turn, -1)
        self.assertFalse(self.game.game_over)
        self.assertEqual(len(self.game.history), 0)
        self.assertEqual(self.game.history_index, -1)
        self.assertEqual(self.game.message, "")
        self.assertIsNone(self.game.agents[-1])
        self.assertIsNone(self.game.agents[1])
        # 初期盤面の確認も追加
        initial_board = Board().get_board()
        self.assertEqual(self.game.get_board(), initial_board)
        self.assertEqual(self.game.get_board_size(), 8) # デフォルトサイズ確認

    def test_reset(self):
        # 何か状態を変更してからリセット
        self.game.place_stone(2, 3) # 黒が (2,3) に置く
        self.game.switch_turn()
        self.game.set_message("Test")
        # config から ID を取得
        first_agent_id = next((d['id'] for d in AGENT_DEFINITIONS if d['class'] == FirstAgent), None)
        random_agent_id = next((d['id'] for d in AGENT_DEFINITIONS if d['class'] == RandomAgent), None)
        self.assertIsNotNone(first_agent_id)
        self.assertIsNotNone(random_agent_id)
        self.game.set_players(first_agent_id, random_agent_id) # FirstAgent, RandomAgent
        self.game.game_over = True

        self.game.reset()

        # 初期状態に戻っているか確認
        self.assertEqual(self.game.turn, -1)
        self.assertFalse(self.game.game_over)
        self.assertEqual(len(self.game.history), 0)
        self.assertEqual(self.game.history_index, -1)
        self.assertEqual(self.game.message, "")
        self.assertIsNone(self.game.agents[-1]) # reset でプレイヤー設定も初期化される
        self.assertIsNone(self.game.agents[1])
        # 盤面も初期状態か確認
        initial_board = Board().get_board()
        self.assertEqual(self.game.get_board(), initial_board)

    def test_switch_turn(self):
        self.assertEqual(self.game.turn, -1)
        self.game.switch_turn()
        self.assertEqual(self.game.turn, 1)
        self.game.switch_turn()
        self.assertEqual(self.game.turn, -1)

    def test_place_stone_valid(self):
        self.assertEqual(self.game.turn, -1)
        valid_move = (2, 3)
        # place_stone の前に get_flipped_stones を呼ぶテストも追加 (行 79-80 カバー)
        flipped_before = self.game.get_flipped_stones(valid_move[0], valid_move[1], self.game.turn)
        self.assertIsInstance(flipped_before, list) # 返り値はリストのはず
        self.assertTrue(len(flipped_before) > 0, "Valid move should flip stones") # 有効手なら反転する石があるはず

        self.assertTrue(self.game.place_stone(valid_move[0], valid_move[1]))
        # 石が置かれたか確認
        self.assertEqual(self.game.board.board[valid_move[0]][valid_move[1]], -1)
        # 裏返った石があるか確認 (例: (3,3) が -1 になっているはず)
        self.assertEqual(self.game.board.board[3][3], -1)
        # 履歴が追加されたか確認
        self.assertEqual(len(self.game.history), 1)
        self.assertEqual(self.game.history_index, 0)
        # 履歴の内容を確認
        history_entry = self.game.history[0]
        self.assertEqual(history_entry[0], valid_move) # 置いた手
        self.assertEqual(history_entry[1], -1) # 手番
        # 盤面のコピーが保存されているか (一部だけ確認)
        self.assertEqual(history_entry[2][valid_move[0]][valid_move[1]], -1)
        self.assertEqual(history_entry[2][3][3], -1)

    def test_place_stone_invalid(self):
        self.assertEqual(self.game.turn, -1)
        invalid_move = (0, 0)
        self.assertFalse(self.game.place_stone(invalid_move[0], invalid_move[1]))
        # 石が置かれていないか確認
        self.assertEqual(self.game.board.board[invalid_move[0]][invalid_move[1]], 0)
        # 履歴が増えていないか確認
        self.assertEqual(len(self.game.history), 0)
        self.assertEqual(self.game.history_index, -1)

    def test_get_winner(self):
        # 初期状態 (引き分けではないが、仮)
        self.assertEqual(self.game.get_winner(), 0) # 初期は同数

        # 黒勝ちの盤面 (行 67 カバー)
        self.game.board.board = [[-1]*8 for _ in range(8)]
        self.game.board.board[0][0] = 1 # 白1つ
        self.assertEqual(self.game.get_winner(), -1)

        # 白勝ちの盤面 (行 70 カバー)
        self.game.board.board = [[1]*8 for _ in range(8)]
        self.game.board.board[0][0] = -1 # 黒1つ
        self.assertEqual(self.game.get_winner(), 1)

        # 引き分けの盤面 (行 72 カバー)
        self.game.board.board = [[-1 if (r+c)%2 == 0 else 1 for c in range(8)] for r in range(8)]
        # この盤面は 32 vs 32 で引き分けになる
        black_count, white_count = self.game.board.count_stones()
        self.assertEqual(black_count, white_count, "Test setup error: Draw board should have equal stones")
        self.assertEqual(self.game.get_winner(), 0)

    def test_set_players(self):
        # config/agents.py の定義に基づいてIDを指定
        human_id = 0
        first_agent_id = next((d['id'] for d in AGENT_DEFINITIONS if d['class'] == FirstAgent), None)
        random_agent_id = next((d['id'] for d in AGENT_DEFINITIONS if d['class'] == RandomAgent), None)

        self.assertIsNotNone(first_agent_id, "FirstAgent ID not found in config")
        self.assertIsNotNone(random_agent_id, "RandomAgent ID not found in config")

        # 黒: 人間, 白: FirstAgent
        self.game.set_players(human_id, first_agent_id)
        self.assertIsNone(self.game.agents[-1])
        self.assertIsInstance(self.game.agents[1], FirstAgent)

        # 黒: RandomAgent, 白: 人間
        self.game.set_players(random_agent_id, human_id)
        self.assertIsInstance(self.game.agents[-1], RandomAgent)
        self.assertIsNone(self.game.agents[1])

        # 黒: FirstAgent, 白: RandomAgent
        self.game.set_players(first_agent_id, random_agent_id)
        self.assertIsInstance(self.game.agents[-1], FirstAgent)
        self.assertIsInstance(self.game.agents[1], RandomAgent)

    def test_set_message_get_message(self):
        self.assertEqual(self.game.get_message(), "")
        test_msg = "Hello, Reversi!"
        self.game.set_message(test_msg)
        self.assertEqual(self.game.get_message(), test_msg)
        self.game.set_message("")
        self.assertEqual(self.game.get_message(), "")

    # === 履歴関連のテスト (カバレッジ向上のため追加) ===
    def test_history_empty(self):
        self.assertFalse(self.game.history_top()) # 行 131 カバー
        self.assertFalse(self.game.history_last()) # 行 138 カバー
        self.assertIsNone(self.game.get_current_history()) # 行 146 カバー
        self.assertFalse(self.game.replay(0)) # 行 127 カバー (範囲外)

    def test_history_navigation(self):
        # 1手目: 黒 (2,3)
        self.game.place_stone(2, 3)
        board1 = [r[:] for r in self.game.get_board()]
        turn1 = -1 # place_stone 後の手番は変わらないが、履歴には打った手番が記録される
        history1 = self.game.history[0]

        # 2手目: 白 (2,4) - place_stoneの前に手番を変える必要がある
        self.game.switch_turn()
        self.game.place_stone(2, 4)
        board2 = [r[:] for r in self.game.get_board()]
        turn2 = 1
        history2 = self.game.history[1]

        # 3手目: 黒 (3,5)
        self.game.switch_turn()
        self.game.place_stone(3, 5)
        board3 = [r[:] for r in self.game.get_board()]
        turn3 = -1
        history3 = self.game.history[2]

        self.assertEqual(len(self.game.history), 3)
        self.assertEqual(self.game.history_index, 2) # 最新のインデックス

        # --- replay テスト (行 118-126 カバー) ---
        # 1手目の状態に戻る
        self.assertTrue(self.game.replay(0))
        self.assertEqual(self.game.history_index, 0)
        self.assertEqual(self.game.get_board(), history1[2]) # 1手目終了時の盤面
        self.assertEqual(self.game.turn, history1[1]) # 1手目を打ったプレイヤーの手番 (-1)
        self.assertFalse(self.game.game_over) # replay で game_over=False になること確認

        # 3手目 (最新) の状態に戻る
        self.assertTrue(self.game.replay(2))
        self.assertEqual(self.game.history_index, 2)
        self.assertEqual(self.game.get_board(), history3[2]) # 3手目終了時の盤面
        self.assertEqual(self.game.turn, history3[1]) # 3手目を打ったプレイヤーの手番 (-1)

        # --- history_top / history_last テスト (行 131-141 カバー) ---
        # 履歴の最初に移動
        self.assertTrue(self.game.history_top())
        self.assertEqual(self.game.history_index, 0)
        self.assertEqual(self.game.get_board(), history1[2])
        self.assertEqual(self.game.turn, history1[1])

        # 履歴の最後に移動
        self.assertTrue(self.game.history_last())
        self.assertEqual(self.game.history_index, 2)
        self.assertEqual(self.game.get_board(), history3[2])
        self.assertEqual(self.game.turn, history3[1])

        # --- get_current_history テスト (行 145-147 カバー) ---
        self.game.replay(1) # 2手目の状態へ
        current_hist = self.game.get_current_history()
        self.assertIsNotNone(current_hist)
        self.assertEqual(current_hist[0], (2, 4)) # 2手目の手
        self.assertEqual(current_hist[1], 1)      # 2手目の手番 (白)
        self.assertEqual(current_hist[2], history2[2]) # 2手目終了時の盤面

        # 範囲外の replay (行 127 カバー)
        self.assertFalse(self.game.replay(-1))
        self.assertFalse(self.game.replay(3))

    # === カバレッジのためのテスト ===

    # --- 行 61 (check_game_over) のテスト ---
    def test_check_game_over_double_pass_real_board(self):
        """両者パスでゲームオーバーになる実際の盤面でテスト"""
        # 盤面を全て埋める (これで確実に両者パスになる)
        self.game.board.board = [[-1 if (r+c)%2 == 0 else 1 for c in range(8)] for r in range(8)]
        # 全てのマスが埋まっていることを念のため確認
        self.assertFalse(any(0 in row for row in self.game.board.board), "Test setup error: Board should be full")

        # この状態だと get_valid_moves が [] を返すことを確認
        self.assertEqual(self.game.board.get_valid_moves(-1), [], "黒の有効手がない盤面のはず")
        self.assertEqual(self.game.board.get_valid_moves(1), [], "白の有効手がない盤面のはず")

        self.assertFalse(self.game.game_over, "初期状態ではゲームオーバーではない")
        self.game.check_game_over() # game.py の行 61 を実行
        self.assertTrue(self.game.game_over, "両者有効手なしの場合、game_overフラグがTrueになるべき")

    # --- 行 70 (get_winner) の確認 ---
    # 上記の test_get_winner 内で白勝ちケースをテスト済み。

    # --- 行 99-108 (create_agent) のテスト ---
    @patch('game.get_agent_params')
    @patch('builtins.print')
    def test_create_agent_type_error(self, mock_print, mock_get_params):
        """エージェント初期化時に TypeError が発生するケースをテスト (行 100-104)"""
        # FirstAgent の ID を取得 (config に依存)
        first_agent_id = next((d['id'] for d in AGENT_DEFINITIONS if d['class'] == FirstAgent), None)
        self.assertIsNotNone(first_agent_id, "FirstAgent ID not found in config")

        mock_get_params.return_value = {'invalid_param': 123}

        agent = self.game.create_agent(first_agent_id)

        self.assertIsNone(agent, "TypeError発生時はNoneが返るべき")
        mock_get_params.assert_called_once_with(first_agent_id)

        # print が呼び出されたことを確認 (最低1回は呼ばれるはず)
        self.assertGreater(mock_print.call_count, 0, "print should have been called on TypeError")
        # 呼び出された print の全テキストを結合
        all_print_output = "".join(str(call_arg[0]) for call_arg, _ in mock_print.call_args_list)
        # 期待されるメッセージの一部が含まれているか確認
        self.assertIn(f"エージェント FirstAgent (ID: {first_agent_id}) の初期化に失敗しました。", all_print_output)
        # "TypeError" という文字列ではなく、TypeError に関連するメッセージが含まれているか確認
        # (例: "takes no arguments", "unexpected keyword argument")
        self.assertTrue("takes no arguments" in all_print_output or "unexpected keyword argument" in all_print_output,
                        f"Expected TypeError related message in print output: {all_print_output}")
        self.assertIn("エラー詳細:", all_print_output) # "エラー詳細:" という文字列が含まれるか

    @patch('game.get_agent_class')
    @patch('game.get_agent_params')
    @patch('builtins.print')
    def test_create_agent_generic_exception(self, mock_print, mock_get_params, mock_get_class):
        """エージェント初期化時に一般的な Exception が発生するケースをテスト (行 105-108)"""
        agent_id_to_test = 99 # ダミーID

        class DummyAgentError(Exception): pass
        class AgentWithInitError:
            def __init__(self, **kwargs):
                raise DummyAgentError("Test Exception during init")

        mock_get_class.return_value = AgentWithInitError
        mock_get_params.return_value = {}

        agent = self.game.create_agent(agent_id_to_test)

        self.assertIsNone(agent, "Exception発生時はNoneが返るべき")
        mock_get_class.assert_called_once_with(agent_id_to_test)
        mock_get_params.assert_called_once_with(agent_id_to_test)

        # --- 修正: print アサーション ---
        self.assertGreater(mock_print.call_count, 0, "print should have been called on Exception")
        all_print_output = "".join(str(call_arg[0]) for call_arg, _ in mock_print.call_args_list)
        self.assertIn(f"エージェント AgentWithInitError (ID: {agent_id_to_test}) の初期化中に予期せぬエラーが発生しました。", all_print_output)
        # self.assertIn("DummyAgentError", all_print_output) # <- 修正前: 例外クラス名を確認していた
        self.assertIn("Test Exception during init", all_print_output) # <- 修正後: 例外メッセージを確認する
        self.assertIn("エラー詳細:", all_print_output)
        # ---------------------------------

    # --- 追加: create_agent で人間プレイヤー (ID=0) または不明なIDの場合 (行 93, 96 カバー) ---
    @patch('game.get_agent_class', return_value=None) # get_agent_class が None を返すようにモック
    def test_create_agent_human_or_unknown(self, mock_get_class):
        """create_agent が人間プレイヤー(ID=0)や不明なIDに対して None を返すかテスト"""
        # 人間プレイヤーID
        human_id = 0
        agent_human = self.game.create_agent(human_id)
        self.assertIsNone(agent_human, "Agent for human ID (0) should be None")
        mock_get_class.assert_called_with(human_id) # get_agent_class が呼ばれる

        # 不明なID
        unknown_id = 999
        agent_unknown = self.game.create_agent(unknown_id)
        self.assertIsNone(agent_unknown, "Agent for unknown ID should be None")
        mock_get_class.assert_called_with(unknown_id) # get_agent_class が呼ばれる

# ... (クラスの末尾) ...

if __name__ == '__main__':
    unittest.main(verbosity=2)

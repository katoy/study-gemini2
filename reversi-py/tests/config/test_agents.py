# tests/config/test_agents.py
import unittest
import sys
from pathlib import Path
from unittest.mock import patch # print文の出力を抑制するために使用 (任意)

# プロジェクトルートをsys.pathに追加
# このテストファイル (test_agents.py) の親 (config) のさらに親 (tests) のさらに親 (プロジェクトルート)
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# テスト対象のモジュールをインポート
# config.agents モジュールから必要な関数と定数をインポート
try:
    from config.agents import (
        AGENT_DEFINITIONS,
        get_agent_options,
        get_agent_class,
        get_agent_params,
        get_agent_definition,
    )
except ImportError as e:
    print(f"テストのインポートエラー: {e}")
    print("config/agents.py が見つからないか、インポートできません。")
    print("プロジェクト構造と sys.path を確認してください。")
    print(f"現在の sys.path: {sys.path}")
    sys.exit(1)

# 比較のためにエージェントクラスもインポート
# (get_agent_class のテストで使用)
try:
    from agents.base_agent import Agent # Base class (optional)
    from agents.first_agent import FirstAgent
    from agents.random_agent import RandomAgent
    from agents.gain_agent import GainAgent
    from agents.mcts_agent import MonteCarloTreeSearchAgent
    from agents.api_agent import ApiAgent
except ImportError as e:
    print(f"エージェントクラスのインポートエラー: {e}")
    print("agents ディレクトリ内のファイルが見つからないか、インポートできません。")
    sys.exit(1)


class TestConfigAgents(unittest.TestCase):

    def test_get_agent_options(self):
        """get_agent_optionsが正しい形式のリストを返すかテスト"""
        options = get_agent_options()
        self.assertIsInstance(options, list, "Options should be a list")
        self.assertTrue(options, "Options list should not be empty") # 定義があれば空でないはず
        # 各要素が (int, str) のタプルかチェック
        for item in options:
            self.assertIsInstance(item, tuple, f"Each option should be a tuple: {item}")
            self.assertEqual(len(item), 2, f"Each option tuple should have 2 elements: {item}")
            self.assertIsInstance(item[0], int, f"First element (ID) should be an integer: {item}")
            self.assertIsInstance(item[1], str, f"Second element (display name) should be a string: {item}")

        # AGENT_DEFINITIONS と一致するか確認
        expected_options = [(d['id'], d['display_name']) for d in AGENT_DEFINITIONS]
        self.assertEqual(options, expected_options, "Options list does not match AGENT_DEFINITIONS")

    def test_get_agent_class_valid_ids(self):
        """get_agent_classが有効なIDに対して正しいクラスまたはNoneを返すかテスト"""
        # AGENT_DEFINITIONS に基づいて動的にテスト
        for definition in AGENT_DEFINITIONS:
            agent_id = definition['id']
            expected_class = definition['class']
            actual_class = get_agent_class(agent_id)
            self.assertEqual(actual_class, expected_class,
                             f"Class mismatch for ID {agent_id}. Expected {expected_class}, got {actual_class}")

    @patch('builtins.print') # printの出力をキャッチ/抑制
    def test_get_agent_class_invalid_id(self, mock_print):
        """get_agent_classが無効なIDに対してNoneを返し、警告を出力するかテスト (カバレッジ用)"""
        # AGENT_DEFINITIONS に存在しないIDを決定的に選択
        existing_ids = {d['id'] for d in AGENT_DEFINITIONS}
        invalid_id = max(existing_ids) + 1 if existing_ids else 999

        # 無効なIDで関数を呼び出し
        result = get_agent_class(invalid_id)

        # 戻り値がNoneであることを確認
        self.assertIsNone(result, f"get_agent_class should return None for invalid ID {invalid_id}")
        # printが期待通り呼び出されたか確認 (行 118-119)
        mock_print.assert_called_once()
        # 呼び出し引数に期待される警告メッセージが含まれているか確認 (より厳密なテスト)
        # self.assertIn(f"警告: 指定されたエージェントID {invalid_id} が見つかりません。", mock_print.call_args[0][0])

    def test_get_agent_params_valid_ids(self):
        """get_agent_paramsが有効なIDに対して正しいパラメータ辞書を返すかテスト"""
        # AGENT_DEFINITIONS に基づいて動的にテスト
        for definition in AGENT_DEFINITIONS:
            agent_id = definition['id']
            # 'params' キーが存在しない場合に備えて .get() を使う
            expected_params = definition.get('params', {})
            actual_params = get_agent_params(agent_id)
            self.assertEqual(actual_params, expected_params,
                             f"Params mismatch for ID {agent_id}. Expected {expected_params}, got {actual_params}")

    @patch('builtins.print') # printの出力をキャッチ/抑制
    def test_get_agent_params_invalid_id(self, mock_print):
        """get_agent_paramsが無効なIDに対して空の辞書を返し、警告を出力するかテスト (カバレッジ用)"""
        # AGENT_DEFINITIONS に存在しないIDを決定的に選択
        existing_ids = {d['id'] for d in AGENT_DEFINITIONS}
        invalid_id = max(existing_ids) + 1 if existing_ids else 999

        # 無効なIDで関数を呼び出し
        result = get_agent_params(invalid_id)

        # 戻り値が空の辞書であることを確認
        self.assertEqual(result, {}, f"get_agent_params should return an empty dict for invalid ID {invalid_id}")
        # printが期待通り呼び出されたか確認 (行 129-133)
        mock_print.assert_called_once()
        # 呼び出し引数に期待される警告メッセージが含まれているか確認 (より厳密なテスト)
        # self.assertIn(f"警告: 指定されたエージェントID {invalid_id} のパラメータが見つかりません。", mock_print.call_args[0][0])

    def test_get_agent_definition_valid_ids(self):
        """get_agent_definitionが有効なIDに対して正しい定義辞書を返すかテスト"""
        # AGENT_DEFINITIONS に基づいて動的にテスト
        for expected_def in AGENT_DEFINITIONS:
            agent_id = expected_def['id']
            actual_def = get_agent_definition(agent_id)
            # 辞書の内容が完全に一致するか確認
            self.assertEqual(actual_def, expected_def,
                             f"Definition mismatch for ID {agent_id}")

    @patch('builtins.print') # printの出力をキャッチ/抑制
    def test_get_agent_definition_invalid_id(self, mock_print):
        """get_agent_definitionが無効なIDに対してNoneを返し、警告を出力するかテスト"""
        # AGENT_DEFINITIONS に存在しないIDを決定的に選択
        existing_ids = {d['id'] for d in AGENT_DEFINITIONS}
        invalid_id = max(existing_ids) + 1 if existing_ids else 999

        # 無効なIDで関数を呼び出し
        result = get_agent_definition(invalid_id)

        # 戻り値がNoneであることを確認
        self.assertIsNone(result, f"get_agent_definition should return None for invalid ID {invalid_id}")
        # printが期待通り呼び出されたか確認
        mock_print.assert_called_once()
        # 呼び出し引数に期待される警告メッセージが含まれているか確認 (より厳密なテスト)
        # self.assertIn(f"警告: 指定されたエージェントID {invalid_id} の定義が見つかりません。", mock_print.call_args[0][0])


if __name__ == '__main__':
    unittest.main(verbosity=2)

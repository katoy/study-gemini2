# tests/config/test_agents.py
import os
import unittest
import sys
from pathlib import Path
from unittest.mock import patch

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

try:
    from agents.api_agent import ApiAgent
    from config.agents_config import (
        AGENT_DEFINITIONS,
        get_agent_options,
        get_agent_class,
        get_agent_definition,
    )
    from config.agent_config_utils import get_agent_params
    from server.api_server import _select_agent
except ImportError as e:
    print(f"テストのインポートエラー: {e}")
    print("config/agents_config.py が見つからないか、インポートできません。")
    print("プロジェクト構造と sys.path を確認してください。")
    print(f"現在の sys.path: {sys.path}")
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

    def test_get_agent_class_invalid_id(self):
        """get_agent_classが無効なIDに対してNoneを返すかテスト"""
        # AGENT_DEFINITIONS に存在しないIDを決定的に選択
        existing_ids = {d['id'] for d in AGENT_DEFINITIONS}
        invalid_id = max(existing_ids) + 1 if existing_ids else 999

        # 無効なIDで関数を呼び出し
        result = get_agent_class(invalid_id)

        # 戻り値がNoneであることを確認
        self.assertIsNone(result, f"get_agent_class should return None for invalid ID {invalid_id}")

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

    def test_get_agent_definition_invalid_id(self):
        """get_agent_definitionが無効なIDに対してNoneを返すかテスト"""
        # AGENT_DEFINITIONS に存在しないIDを決定的に選択
        existing_ids = {d['id'] for d in AGENT_DEFINITIONS}
        invalid_id = max(existing_ids) + 1 if existing_ids else 999

        # 無効なIDで関数を呼び出し
        result = get_agent_definition(invalid_id)

        # 戻り値がNoneであることを確認
        self.assertIsNone(result, f"get_agent_definition should return None for invalid ID {invalid_id}")

    def test_api_agent_has_agent_type_param(self):
        """すべての API エージェント定義 (人間以外) の params に agent_type が含まれる"""
        api_agents = [d for d in AGENT_DEFINITIONS if d['id'] != 0]  # 人間 (id=0) を除外
        valid_agent_types = [
            "first",
            "random",
            "gain",
            "mcts",
            "negamax_3k",
            "negamax_6k",
            "transposition",
            "pattern",
            "minimax",
            "alphazero_minimax",
        ]
        for defn in api_agents:
            with self.subTest(agent_id=defn['id']):
                self.assertIn("params", defn, "Definition should have 'params' key")
                self.assertIn("agent_type", defn["params"], "params should contain 'agent_type'")
                self.assertIn(
                    defn["params"].get("agent_type"),
                    valid_agent_types,
                    f"agent_type {defn['params'].get('agent_type')} not in valid list",
                )

    def test_negamax_selection_is_split_into_3k_and_6k(self):
        """プレイヤー設定の Negamax は 3K / 6K の 2 種類になっている"""
        negamax_options = [
            d for d in AGENT_DEFINITIONS if d["display_name"].startswith("API (Negamax")
        ]
        self.assertEqual(len(negamax_options), 2)
        self.assertEqual(
            [d["display_name"] for d in negamax_options],
            ["API (Negamax-3K)", "API (Negamax-6K)"],
        )
        self.assertEqual(
            [d["params"]["agent_type"] for d in negamax_options],
            ["negamax_3k", "negamax_6k"],
        )
        self.assertTrue(all(d["params"].get("timeout") == 10 for d in negamax_options))

    def test_api_agent_timeouts_exceed_server_time_limits(self):
        """各 API エージェントの HTTP タイムアウトがサーバー側の思考時間上限より十分長い"""
        time_limit_env_keys = {
            "NEGAMAX_TIME_LIMIT_MS",
            "MINIMAX_TIME_LIMIT_MS",
            "TRANSPOSITION_TIME_LIMIT_MS",
            "PATTERN_TIME_LIMIT_MS",
            "ALPHAZERO_MINIMAX_ENDGAME_TIME_LIMIT_MS",
        }
        clean_env = {k: v for k, v in os.environ.items() if k not in time_limit_env_keys}

        with patch.dict(os.environ, clean_env, clear=True):
            for defn in AGENT_DEFINITIONS:
                if defn["id"] == 0:
                    continue
                with self.subTest(agent_id=defn["id"], display_name=defn["display_name"]):
                    api_agent = ApiAgent(**defn["params"])
                    server_agent = _select_agent(defn["params"]["agent_type"])
                    self.assertIsNotNone(server_agent)

                    limits_ms = [
                        getattr(server_agent, "time_limit_ms", 0),
                        getattr(server_agent, "_time_limit_ms", 0),
                    ]
                    solver = getattr(server_agent, "_solver", None)
                    if solver is not None:
                        limits_ms.append(getattr(solver, "time_limit_ms", 0))

                    max_time_limit_ms = max(limits_ms)
                    required_timeout_sec = max_time_limit_ms / 1000.0 + 4.0
                    self.assertGreaterEqual(
                        api_agent.timeout,
                        required_timeout_sec,
                        f"{defn['display_name']} timeout={api_agent.timeout}s is too short "
                        f"for server limit {max_time_limit_ms}ms",
                    )


if __name__ == '__main__':
    unittest.main(verbosity=2)

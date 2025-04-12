# test/config/test_agents.py
import unittest
import sys
import os
import inspect # class の型チェック用

# プロジェクトルートへのパスを追加 (test/config ディレクトリから見て親の親ディレクトリ)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
sys.path.append(project_root)

# テスト対象のモジュールと、依存するエージェントクラスをインポート
# config.agents を agents_config という名前でインポート
from config import agents as agents_config
# agents モジュールから必要なクラスをインポート
from agents import FirstAgent, RandomAgent, GainAgent, MonteCarloTreeSearchAgent

class TestAgentsConfig(unittest.TestCase):
    """config.agents モジュールのテストクラス"""

    def test_agent_definitions_structure_and_content(self):
        """AGENT_DEFINITIONS の構造と基本的な内容を検証する"""
        definitions = agents_config.AGENT_DEFINITIONS
        self.assertIsInstance(definitions, list, "AGENT_DEFINITIONS はリストであるべきです")
        self.assertGreater(len(definitions), 0, "エージェント定義が空であってはなりません")

        seen_ids = set()
        for agent_def in definitions:
            self.assertIsInstance(agent_def, dict, "各エージェント定義は辞書であるべきです")
            # 必須キーの存在確認
            self.assertIn('id', agent_def, "キー 'id' が必要です")
            self.assertIn('class', agent_def, "キー 'class' が必要です")
            self.assertIn('display_name', agent_def, "キー 'display_name' が必要です")
            self.assertIn('params', agent_def, "キー 'params' が必要です")

            # 型チェック
            agent_id = agent_def['id']
            agent_class = agent_def['class']
            display_name = agent_def['display_name']
            params = agent_def['params']

            self.assertIsInstance(agent_id, int, f"ID {agent_id}: 'id' は整数であるべきです")
            # class はクラスオブジェクトか None
            self.assertTrue(agent_class is None or inspect.isclass(agent_class),
                            f"ID {agent_id}: 'class' はクラスオブジェクトまたはNoneであるべきです")
            self.assertIsInstance(display_name, str, f"ID {agent_id}: 'display_name' は文字列であるべきです")
            self.assertIsInstance(params, dict, f"ID {agent_id}: 'params' は辞書であるべきです")

            # ID のユニーク性チェック
            self.assertNotIn(agent_id, seen_ids, f"エージェントID {agent_id} が重複しています")
            seen_ids.add(agent_id)

        # 特定のエージェントの存在と内容を確認 (例: 人間)
        human_def = agents_config.get_agent_definition(0)
        self.assertIsNotNone(human_def, "ID 0 (人間) の定義が見つかりません")
        self.assertEqual(human_def['display_name'], '人間', "ID 0 の表示名が '人間' ではありません")
        self.assertIsNone(human_def['class'], "ID 0 のクラスが None ではありません")
        self.assertEqual(human_def['params'], {}, "ID 0 のパラメータが空辞書ではありません")

        # 特定のエージェントの存在と内容を確認 (例: MCTS)
        mcts_def = agents_config.get_agent_definition(4)
        self.assertIsNotNone(mcts_def, "ID 4 (MCTS) の定義が見つかりません")
        self.assertEqual(mcts_def['display_name'], 'MCTS', "ID 4 の表示名が 'MCTS' ではありません")
        self.assertEqual(mcts_def['class'], MonteCarloTreeSearchAgent, "ID 4 のクラスが MonteCarloTreeSearchAgent ではありません")
        self.assertIn('iterations', mcts_def['params'], "ID 4 のパラメータに 'iterations' がありません")
        self.assertIn('time_limit_ms', mcts_def['params'], "ID 4 のパラメータに 'time_limit_ms' がありません")
        self.assertIn('exploration_weight', mcts_def['params'], "ID 4 のパラメータに 'exploration_weight' がありません")


    def test_get_agent_options(self):
        """get_agent_options() の動作を検証する"""
        options = agents_config.get_agent_options()
        self.assertIsInstance(options, list, "get_agent_options はリストを返すべきです")
        self.assertEqual(len(options), len(agents_config.AGENT_DEFINITIONS),
                         "オプションの数と定義の数が一致しません")

        for option in options:
            self.assertIsInstance(option, tuple, "各オプションはタプルであるべきです")
            self.assertEqual(len(option), 2, "各オプションタプルは2要素であるべきです")
            self.assertIsInstance(option[0], int, "オプションの第一要素 (id) は整数であるべきです")
            self.assertIsInstance(option[1], str, "オプションの第二要素 (display_name) は文字列であるべきです")

        # 内容の一致確認 (定義リストから期待されるオプションリストを作成して比較)
        expected_options = [(d['id'], d['display_name']) for d in agents_config.AGENT_DEFINITIONS]
        self.assertListEqual(options, expected_options, "返されたオプションリストの内容が期待値と一致しません")

    def test_get_agent_class(self):
        """get_agent_class() の動作を検証する"""
        # 存在するIDに対応するクラスが返されるか
        self.assertIsNone(agents_config.get_agent_class(0), "ID 0 は None を返すべきです")
        self.assertEqual(agents_config.get_agent_class(1), FirstAgent, "ID 1 は FirstAgent を返すべきです")
        self.assertEqual(agents_config.get_agent_class(2), RandomAgent, "ID 2 は RandomAgent を返すべきです")
        self.assertEqual(agents_config.get_agent_class(3), GainAgent, "ID 3 は GainAgent を返すべきです")
        self.assertEqual(agents_config.get_agent_class(4), MonteCarloTreeSearchAgent, "ID 4 は MonteCarloTreeSearchAgent を返すべきです")

        # 存在しないIDの場合に None が返されるか
        non_existent_id = 999
        self.assertIsNone(agents_config.get_agent_class(non_existent_id), "存在しないIDは None を返すべきです")

    def test_get_agent_params(self):
        """get_agent_params() の動作を検証する"""
        # パラメータがないエージェントの場合、空の辞書が返されるか
        self.assertEqual(agents_config.get_agent_params(0), {}, "ID 0 のパラメータは空辞書であるべきです")
        self.assertEqual(agents_config.get_agent_params(1), {}, "ID 1 のパラメータは空辞書であるべきです")
        self.assertEqual(agents_config.get_agent_params(2), {}, "ID 2 のパラメータは空辞書であるべきです")
        self.assertEqual(agents_config.get_agent_params(3), {}, "ID 3 のパラメータは空辞書であるべきです")

        # パラメータがあるエージェントの場合、正しい辞書が返されるか
        mcts_params = agents_config.get_agent_params(4)
        self.assertIsInstance(mcts_params, dict, "ID 4 のパラメータは辞書であるべきです")
        expected_mcts_params = {
            'iterations': 50000,
            'time_limit_ms': 4000,
            'exploration_weight': 1.41
        }
        self.assertDictEqual(mcts_params, expected_mcts_params, "ID 4 のパラメータの内容が期待値と一致しません")

        # 存在しないIDの場合に空の辞書が返されるか
        non_existent_id = 999
        self.assertEqual(agents_config.get_agent_params(non_existent_id), {}, "存在しないIDのパラメータは空辞書であるべきです")

    def test_get_agent_definition(self):
        """get_agent_definition() の動作を検証する"""
        # 存在するIDの場合、対応する完全な辞書が返されるか
        definition_0 = agents_config.get_agent_definition(0)
        self.assertIsNotNone(definition_0, "ID 0 の定義が見つかりません")
        # AGENT_DEFINITIONS の最初の要素と比較
        self.assertDictEqual(definition_0, agents_config.AGENT_DEFINITIONS[0], "ID 0 の定義内容が期待値と一致しません")

        definition_4 = agents_config.get_agent_definition(4)
        self.assertIsNotNone(definition_4, "ID 4 の定義が見つかりません")
        # AGENT_DEFINITIONS の対応する要素を探して比較
        expected_def_4 = next((d for d in agents_config.AGENT_DEFINITIONS if d['id'] == 4), None)
        self.assertDictEqual(definition_4, expected_def_4, "ID 4 の定義内容が期待値と一致しません")

        # 存在しないIDの場合に None が返されるか
        non_existent_id = 999
        self.assertIsNone(agents_config.get_agent_definition(non_existent_id), "存在しないIDの定義は None を返すべきです")

if __name__ == '__main__':
    # テストを実行
    unittest.main(verbosity=2) # verbosity=2 で詳細な結果を表示

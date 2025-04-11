# tests/test_config_agents.py

import unittest
import sys
import os
import inspect  # クラスかどうかを判定するために使用

# テスト対象のモジュールをインポートするためにパスを追加
# このテストファイルがプロジェクトルートの 'tests' ディレクトリにあると仮定
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# config.agents をインポート
try:
    from config.agents import AGENT_REGISTRY
    # AGENT_REGISTRY がインポートできない場合はテストをスキップするなどの処理も可能
    config_agents_imported = True
except ImportError as e:
    print(f"テストスキップ: config.agents のインポートに失敗しました: {e}")
    config_agents_imported = False
    AGENT_REGISTRY = [] # ダミーを設定してテストがエラーにならないようにする

# agents モジュールもインポートしてクラスの存在を確認 (存在すれば)
try:
    from agents import FirstAgent, RandomAgent, GainAgent, MonteCarloTreeSearchAgent
    agents_imported = True
except ImportError:
    agents_imported = False
    # agents モジュールがない場合、クラスの型チェックは限定的になる

@unittest.skipUnless(config_agents_imported, "config.agents モジュールが見つからないため、テストをスキップします。")
class TestConfigAgents(unittest.TestCase):

    def test_agent_registry_is_list(self):
        """AGENT_REGISTRY がリストであることをテスト"""
        self.assertIsInstance(AGENT_REGISTRY, list, "AGENT_REGISTRY はリストである必要があります。")
        self.assertGreater(len(AGENT_REGISTRY), 0, "AGENT_REGISTRY は空であってはいけません。")

    def test_registry_elements_are_dicts(self):
        """AGENT_REGISTRY の各要素が辞書であることをテスト"""
        for item in AGENT_REGISTRY:
            self.assertIsInstance(item, dict, f"AGENT_REGISTRY の要素は辞書である必要があります: {item}")

    def test_dict_keys_exist(self):
        """各辞書が必要なキー ('key', 'name', 'class') を持っていることをテスト"""
        required_keys = {'key', 'name', 'class'}
        for item in AGENT_REGISTRY:
            self.assertTrue(required_keys.issubset(item.keys()),
                            f"辞書に必要なキー {required_keys} が含まれていません: {item}")

    def test_key_is_string_and_unique(self):
        """'key' が文字列であり、かつリスト内で一意であることをテスト"""
        keys = set()
        for item in AGENT_REGISTRY:
            key = item.get('key')
            self.assertIsInstance(key, str, f"'key' は文字列である必要があります: {item}")
            self.assertTrue(key, f"'key' は空文字列であってはいけません: {item}") # 空文字列でないことも確認
            self.assertNotIn(key, keys, f"'key' は一意である必要があります: 重複 '{key}'")
            keys.add(key)

    def test_name_is_string(self):
        """'name' が文字列であることをテスト"""
        for item in AGENT_REGISTRY:
            name = item.get('name')
            self.assertIsInstance(name, str, f"'name' は文字列である必要があります: {item}")
            self.assertTrue(name, f"'name' は空文字列であってはいけません: {item}") # 空文字列でないことも確認

    def test_class_is_type_or_none(self):
        """'class' がクラスオブジェクト (type) または None であることをテスト"""
        for item in AGENT_REGISTRY:
            agent_class = item.get('class')
            # inspect.isclass() はクラスオブジェクトかどうかを判定する
            is_class = inspect.isclass(agent_class)
            is_none = agent_class is None
            self.assertTrue(is_class or is_none,
                            f"'class' はクラスオブジェクトまたは None である必要があります: {item}, type={type(agent_class)}")

    def test_human_agent_class_is_none(self):
        """'key' が 'human' の場合、'class' が None であることをテスト"""
        human_agent_found = False
        for item in AGENT_REGISTRY:
            if item.get('key') == 'human':
                self.assertIsNone(item.get('class'), f"'human' エージェントの 'class' は None である必要があります: {item}")
                human_agent_found = True
        self.assertTrue(human_agent_found, "'human' エージェントが AGENT_REGISTRY に見つかりません。")

    def test_non_human_agent_class_is_not_none_and_is_class(self):
        """'key' が 'human' 以外の場合、'class' が None でなく、かつクラスオブジェクトであることをテスト"""
        for item in AGENT_REGISTRY:
            if item.get('key') != 'human':
                agent_class = item.get('class')
                self.assertIsNotNone(agent_class, f"'{item.get('key')}' エージェントの 'class' は None であってはいけません: {item}")
                self.assertTrue(inspect.isclass(agent_class),
                                f"'{item.get('key')}' エージェントの 'class' はクラスオブジェクトである必要があります: {item}")

    @unittest.skipUnless(agents_imported, "agents モジュールが見つからないため、クラスの存在確認テストをスキップします。")
    def test_registered_classes_match_imports(self):
        """AGENT_REGISTRY に登録されているクラスがインポートされたクラスと一致するかテスト"""
        # config/agents.py でインポートしているクラスを期待値として設定
        expected_classes = {
            'first': FirstAgent,
            'random': RandomAgent,
            'gain': GainAgent,
            'mcts': MonteCarloTreeSearchAgent,
            # 新しいエージェントを追加したらここにも追加
        }
        registered_agent_keys = set()
        for item in AGENT_REGISTRY:
            key = item.get('key')
            agent_class = item.get('class')
            if key != 'human':
                registered_agent_keys.add(key)
                self.assertIn(key, expected_classes, f"AGENT_REGISTRY に登録されているキー '{key}' が予期されるキーのリストにありません。")
                # is 比較で同じクラスオブジェクトかを厳密にチェック
                self.assertIs(agent_class, expected_classes[key],
                    f"キー '{key}' に登録されているクラス ({agent_class.__name__ if agent_class else 'None'}) が期待されるクラス ({expected_classes[key].__name__}) と一致しません。")

        # 期待されるすべてのキーが登録されているかも確認
        self.assertEqual(registered_agent_keys, set(expected_classes.keys()),
            "AGENT_REGISTRY に登録されているエージェントのキーが、期待されるキーのセットと一致しません。")


if __name__ == '__main__':
    # テストを実行
    # コマンドラインから実行する場合: python -m unittest tests/test_config_agents.py
    unittest.main(argv=['first-arg-is-ignored'], exit=False) # Jupyter等で実行する場合

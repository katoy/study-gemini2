# tests/test_config.py
import unittest
import os
import sys

# テスト対象のモジュールをインポートするためにパスを追加
# このテストファイルが tests/ ディレクトリにあることを想定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# テスト対象のモジュールをインポート
from config import (
    LayoutConfig,
    DEFAULT_SETTINGS_FILENAME,
    DEFAULT_USER_NAME,
    DEFAULT_OPTION_KEY
)

class TestConfig(unittest.TestCase):
    """
    config.py の定数と LayoutConfig クラスをテストするクラス。
    """

    def setUp(self):
        """
        各テストメソッドの前に実行されるセットアップメソッド。
        LayoutConfig のインスタンスを作成します。
        """
        self.config = LayoutConfig()

    def test_layout_config_instance_creation(self):
        """
        LayoutConfig クラスのインスタンスが正しく作成されることをテストします。
        """
        self.assertIsInstance(self.config, LayoutConfig)

    def test_layout_config_attributes_types_and_values(self):
        """
        LayoutConfig クラスの各属性が期待される型と値を持っていることをテストします。
        """
        # --- ウィンドウとダイアログのサイズ ---
        self.assertIsInstance(self.config.WINDOW_WIDTH, int)
        self.assertEqual(self.config.WINDOW_WIDTH, 600)

        self.assertIsInstance(self.config.WINDOW_HEIGHT, int)
        self.assertEqual(self.config.WINDOW_HEIGHT, 400)

        self.assertIsInstance(self.config.DIALOG_WIDTH, int)
        self.assertEqual(self.config.DIALOG_WIDTH, 400)

        self.assertIsInstance(self.config.DIALOG_HEIGHT, int)
        self.assertEqual(self.config.DIALOG_HEIGHT, 300)

        # --- UI要素のサイズとマージン ---
        self.assertIsInstance(self.config.BUTTON_WIDTH, int)
        self.assertEqual(self.config.BUTTON_WIDTH, 150)

        self.assertIsInstance(self.config.BUTTON_HEIGHT, int)
        self.assertEqual(self.config.BUTTON_HEIGHT, 50)

        self.assertIsInstance(self.config.MARGIN, int)
        self.assertEqual(self.config.MARGIN, 10)

        # --- settings_dialog.py 用のレイアウト定数 ---
        self.assertIsInstance(self.config.DIALOG_LABEL_HEIGHT, int)
        self.assertEqual(self.config.DIALOG_LABEL_HEIGHT, 30)

        self.assertIsInstance(self.config.DIALOG_ENTRY_HEIGHT, int)
        self.assertEqual(self.config.DIALOG_ENTRY_HEIGHT, 30)

        self.assertIsInstance(self.config.DIALOG_RADIO_PANEL_HEIGHT, int)
        self.assertEqual(self.config.DIALOG_RADIO_PANEL_HEIGHT, 50)

        self.assertIsInstance(self.config.DIALOG_RADIO_BUTTON_WIDTH, int)
        self.assertEqual(self.config.DIALOG_RADIO_BUTTON_WIDTH, 110)

        self.assertIsInstance(self.config.DIALOG_RADIO_BUTTON_HEIGHT, int)
        self.assertEqual(self.config.DIALOG_RADIO_BUTTON_HEIGHT, 30)

        self.assertIsInstance(self.config.DIALOG_ACTION_BUTTON_WIDTH, int)
        self.assertEqual(self.config.DIALOG_ACTION_BUTTON_WIDTH, 100)

        self.assertIsInstance(self.config.DIALOG_ACTION_BUTTON_HEIGHT, int)
        self.assertEqual(self.config.DIALOG_ACTION_BUTTON_HEIGHT, 40)

        # --- フォント設定 ---
        self.assertIsInstance(self.config.FONT_NAME, str)
        self.assertEqual(self.config.FONT_NAME, "NotoSansJP-Regular.ttf")

        self.assertIsInstance(self.config.FONT_SIZE, int)
        self.assertEqual(self.config.FONT_SIZE, 16)

        # --- main.py 用の計算済みレイアウト値 ---
        self.assertIsInstance(self.config.BUTTON_Y, int)
        expected_button_y = self.config.WINDOW_HEIGHT - self.config.BUTTON_HEIGHT - self.config.MARGIN * 2
        self.assertEqual(self.config.BUTTON_Y, expected_button_y)
        # 具体的な値も確認 (400 - 50 - 10 * 2 = 330)
        self.assertEqual(self.config.BUTTON_Y, 330)

    def test_default_settings_constants(self):
        """
        ファイルレベルのデフォルト設定定数が期待される型と値を持っていることをテストします。
        """
        self.assertIsInstance(DEFAULT_SETTINGS_FILENAME, str)
        self.assertEqual(DEFAULT_SETTINGS_FILENAME, "user_settings.json")

        self.assertIsInstance(DEFAULT_USER_NAME, str)
        self.assertEqual(DEFAULT_USER_NAME, "User")

        self.assertIsInstance(DEFAULT_OPTION_KEY, str)
        self.assertEqual(DEFAULT_OPTION_KEY, "#settings.option_a")

if __name__ == '__main__':
    # tests ディレクトリが存在しない場合に作成
    if not os.path.exists(os.path.join(project_root, 'tests')):
        os.makedirs(os.path.join(project_root, 'tests'))
        print("Created 'tests' directory.")

    # このファイルを tests/test_config.py として保存
    test_file_path = os.path.join(project_root, 'tests', 'test_config.py')
    # 現在のファイルパスと保存先パスが異なる場合（初回実行時など）は保存
    # Note: スクリプトとして直接実行される場合、__file__ は絶対パスになる
    if os.path.abspath(__file__) != os.path.abspath(test_file_path):
        try:
            # 自分自身のコードを取得して保存
            with open(__file__, 'r', encoding='utf-8') as f_read:
                current_code = f_read.read()
            with open(test_file_path, 'w', encoding='utf-8') as f_write:
                f_write.write(current_code)
            print(f"Saved test file to: {test_file_path}")
        except Exception as e:
            print(f"Error saving test file: {e}")

    # unittest を実行
    print("\nRunning tests for config.py...")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

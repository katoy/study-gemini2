# tests/test_user_settings.py
import unittest
import os
import sys
import json
from unittest.mock import patch, mock_open, MagicMock

# テスト対象のモジュールをインポートするためにパスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# テスト対象のクラスと定数をインポート
from user_settings import UserSettings, DEFAULT_SETTINGS_FILENAME, DEFAULT_USER_NAME, DEFAULT_OPTION_KEY

# --- テスト用定数 ---
TEST_FILENAME = "test_settings_for_unittest.json"
# テスト実行ディレクトリにテスト用ファイルを作成/削除する
TEST_FILEPATH = os.path.join(project_root, TEST_FILENAME)

class TestUserSettings(unittest.TestCase):
    """
    user_settings.py の UserSettings クラスをテストするクラス。
    """

    def setUp(self):
        """各テストメソッドの前に実行: テスト用ファイルを削除"""
        if os.path.exists(TEST_FILEPATH):
            os.remove(TEST_FILEPATH)
        # UserSettings インスタンスは各テストメソッド内で必要に応じて作成

    def tearDown(self):
        """各テストメソッドの後に実行: テスト用ファイルを削除"""
        if os.path.exists(TEST_FILEPATH):
            os.remove(TEST_FILEPATH)

    # --- _get_settings_path のテスト ---

    @patch('user_settings.sys')
    def test_get_settings_path_dev_environment(self, mock_sys):
        """開発環境での設定ファイルパス取得をテスト"""
        # sys.frozen が False (または存在しない) 場合をシミュレート
        mock_sys.frozen = False
        # __file__ が user_settings.py のパスを指すように設定
        # このテストファイルは tests/ にあるので、親ディレクトリがプロジェクトルート
        expected_path = os.path.join(project_root, DEFAULT_SETTINGS_FILENAME)

        settings = UserSettings() # デフォルトファイル名で初期化
        actual_path = settings._get_settings_path(DEFAULT_SETTINGS_FILENAME)

        self.assertEqual(actual_path, expected_path)

    @patch('user_settings.sys')
    def test_get_settings_path_frozen_environment(self, mock_sys):
        """PyInstaller バンドル環境での設定ファイルパス取得をテスト"""
        # sys.frozen が True で、sys.executable が実行ファイルのパスを指す場合
        mock_sys.frozen = True
        mock_executable_path = '/path/to/frozen/executable'
        mock_sys.executable = mock_executable_path
        expected_path = os.path.join(os.path.dirname(mock_executable_path), DEFAULT_SETTINGS_FILENAME)

        settings = UserSettings() # デフォルトファイル名で初期化
        actual_path = settings._get_settings_path(DEFAULT_SETTINGS_FILENAME)

        self.assertEqual(actual_path, expected_path)

    # --- 初期化 (__init__ と load) のテスト ---

    @patch('user_settings.os.path.exists', return_value=False)
    @patch('builtins.print') # print 出力をキャプチャ
    def test_initialization_file_not_found_uses_defaults(self, mock_print, mock_exists):
        """初期化時にファイルが存在しない場合、デフォルト値が使用されるかテスト"""
        settings = UserSettings(filename=TEST_FILENAME)

        # デフォルト値が設定されているか確認
        self.assertEqual(settings.user_name, DEFAULT_USER_NAME)
        self.assertEqual(settings.selected_option_key, DEFAULT_OPTION_KEY)
        # ファイルパスが正しく設定されているか確認 (開発環境を想定)
        self.assertEqual(settings.filepath, os.path.join(project_root, TEST_FILENAME))
        # ファイルが存在しない旨のログが出力されるか確認
        mock_print.assert_any_call(f"Info: Settings file not found at '{settings.filepath}'. Using default settings.")
        mock_exists.assert_called_once_with(settings.filepath)

    @patch('user_settings.os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='{"user_name": "Loaded User", "selected_option_key": "#settings.option_c"}')
    @patch('builtins.print')
    def test_initialization_loads_from_existing_file(self, mock_print, mock_file, mock_exists):
        """初期化時に存在するファイルから正しく読み込めるかテスト"""
        settings = UserSettings(filename=TEST_FILENAME)

        # ファイルから読み込んだ値が設定されているか確認
        self.assertEqual(settings.user_name, "Loaded User")
        self.assertEqual(settings.selected_option_key, "#settings.option_c")
        # ファイルパスが正しく設定されているか確認
        self.assertEqual(settings.filepath, os.path.join(project_root, TEST_FILENAME))
        # 読み込み成功のログが出力されるか確認
        mock_print.assert_any_call(f"Info: Settings loaded from '{settings.filepath}'")
        mock_exists.assert_called_once_with(settings.filepath)
        mock_file.assert_called_once_with(settings.filepath, 'r', encoding='utf-8')

    # --- load メソッドのテスト ---

    @patch('user_settings.os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='this is not valid json')
    @patch('builtins.print')
    def test_load_invalid_json_uses_defaults(self, mock_print, mock_file, mock_exists):
        """不正なJSONファイルを読み込んだ場合、デフォルト値が使用されるかテスト"""
        settings = UserSettings(filename=TEST_FILENAME) # 初期化時に load が呼ばれる

        # デフォルト値に戻っているか確認
        self.assertEqual(settings.user_name, DEFAULT_USER_NAME)
        self.assertEqual(settings.selected_option_key, DEFAULT_OPTION_KEY)
        # エラーログが出力されるか確認
        mock_print.assert_any_call(f"Error: Failed to decode JSON from '{settings.filepath}'. Using default settings.")
        mock_exists.assert_called_once_with(settings.filepath)
        mock_file.assert_called_once_with(settings.filepath, 'r', encoding='utf-8')

    @patch('user_settings.os.path.exists', return_value=True)
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    @patch('builtins.print')
    def test_load_io_error_uses_defaults(self, mock_print, mock_open_error, mock_exists):
        """ファイル読み込み中にIOErrorが発生した場合、デフォルト値が使用されるかテスト"""
        settings = UserSettings(filename=TEST_FILENAME) # 初期化時に load が呼ばれる

        # デフォルト値に戻っているか確認
        self.assertEqual(settings.user_name, DEFAULT_USER_NAME)
        self.assertEqual(settings.selected_option_key, DEFAULT_OPTION_KEY)
        # エラーログが出力されるか確認
        mock_print.assert_any_call(f"Error: Failed to load settings from '{settings.filepath}': Permission denied. Using default settings.")
        mock_exists.assert_called_once_with(settings.filepath)
        mock_open_error.assert_called_once_with(settings.filepath, 'r', encoding='utf-8')

    @patch('user_settings.os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='{"user_name": "Partial User"}') # キーが一部欠けている
    @patch('builtins.print')
    def test_load_missing_keys_uses_defaults_for_missing(self, mock_print, mock_file, mock_exists):
        """JSONファイルにキーが欠けている場合、欠けているキーはデフォルト値で補完されるかテスト"""
        settings = UserSettings(filename=TEST_FILENAME)

        # 存在するキーは読み込まれ、欠けているキーはデフォルト値になるか確認
        self.assertEqual(settings.user_name, "Partial User")
        self.assertEqual(settings.selected_option_key, DEFAULT_OPTION_KEY) # デフォルト値
        # 読み込み成功のログが出力されるか確認
        mock_print.assert_any_call(f"Info: Settings loaded from '{settings.filepath}'")
        mock_exists.assert_called_once_with(settings.filepath)
        mock_file.assert_called_once_with(settings.filepath, 'r', encoding='utf-8')

    # --- save メソッドのテスト ---

    @patch('builtins.print')
    def test_save_writes_correct_data(self, mock_print):
        """設定を正しくファイルに保存できるかテスト"""
        settings = UserSettings(filename=TEST_FILENAME)
        new_name = "Saved User"
        new_option = "#settings.option_b"

        # 設定を変更
        settings.user_name = new_name
        settings.selected_option_key = new_option

        # 保存実行
        settings.save()

        # 保存成功のログが出力されるか確認
        mock_print.assert_any_call(f"Info: Settings saved to '{settings.filepath}'")

        # ファイルが実際に作成され、内容が正しいか確認
        self.assertTrue(os.path.exists(TEST_FILEPATH))
        with open(TEST_FILEPATH, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data['user_name'], new_name)
        self.assertEqual(saved_data['selected_option_key'], new_option)

    @patch('builtins.open', side_effect=IOError("Disk full"))
    @patch('builtins.print')
    def test_save_io_error_logs_error(self, mock_print, mock_open_error):
        """ファイル保存中にIOErrorが発生した場合、エラーログが出力されるかテスト"""
        settings = UserSettings(filename=TEST_FILENAME)
        settings.user_name = "Cannot Save"

        # 保存実行
        settings.save()

        # エラーログが出力されるか確認
        mock_print.assert_any_call(f"Error: Failed to save settings to '{settings.filepath}': Disk full")
        # open が呼ばれたか確認
        mock_open_error.assert_called_once_with(settings.filepath, 'w', encoding='utf-8')

    @patch('user_settings.json.dump', side_effect=TypeError("Unexpected type"))
    @patch('builtins.open', new_callable=mock_open) # open は成功するが dump で失敗
    @patch('builtins.print')
    def test_save_unexpected_error_logs_error(self, mock_print, mock_file, mock_dump_error):
        """ファイル保存中に予期せぬエラーが発生した場合、エラーログが出力されるかテスト"""
        settings = UserSettings(filename=TEST_FILENAME)
        settings.user_name = "Weird Save"

        # 保存実行
        settings.save()

        # エラーログが出力されるか確認
        mock_print.assert_any_call(f"Error: An unexpected error occurred while saving settings: Unexpected type")
        # open と dump が呼ばれたか確認
        mock_file.assert_called_once_with(settings.filepath, 'w', encoding='utf-8')
        mock_dump_error.assert_called_once()


if __name__ == '__main__':
    # このファイルを tests/test_user_settings.py として保存
    test_file_path = os.path.join(project_root, 'tests', 'test_user_settings.py')
    if os.path.abspath(__file__) != os.path.abspath(test_file_path):
        try:
            with open(__file__, 'r', encoding='utf-8') as f_read:
                current_code = f_read.read()
            with open(test_file_path, 'w', encoding='utf-8') as f_write:
                f_write.write(current_code)
            print(f"Saved test file to: {test_file_path}")
        except Exception as e:
            print(f"Error saving test file: {e}")

    print("\nRunning tests for user_settings.py...")
    unittest.main(argv=['first-arg-is-ignored'], exit=False, verbosity=2)

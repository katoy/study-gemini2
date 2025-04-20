# user_settings.py
import json
import os
import sys
from config import DEFAULT_SETTINGS_FILENAME, DEFAULT_USER_NAME, DEFAULT_OPTION_KEY

class UserSettings:
    """
    ユーザー設定 (名前、選択オプション) を JSON ファイルに保存・読み込みするクラス。
    """
    def __init__(self, filename: str = DEFAULT_SETTINGS_FILENAME):
        """
        UserSettings を初期化し、設定ファイルを読み込みます。

        Args:
            filename (str): 設定ファイル名。
        """
        self.filepath = self._get_settings_path(filename)
        self.user_name: str = DEFAULT_USER_NAME
        self.selected_option_key: str = DEFAULT_OPTION_KEY
        self.load()

    def _get_settings_path(self, filename: str) -> str:
        """
        設定ファイルの絶対パスを取得します。
        開発環境でも PyInstaller バンドル時でも、
        実行ファイルの隣に設定ファイルが配置されるようにします。
        """
        if getattr(sys, 'frozen', False):
            # PyInstaller でバンドルされている場合 (実行ファイルと同じディレクトリ)
            application_path = os.path.dirname(sys.executable)
        else:
            # 通常の Python 環境の場合 (main.py と同じディレクトリ)
            # __file__ はこの user_settings.py のパスなので、そのディレクトリを取得
            application_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(application_path, filename)

    def load(self):
        """
        設定ファイルから設定を読み込みます。
        ファイルが存在しない場合や読み込みに失敗した場合は、デフォルト値が使用されます。
        """
        if not os.path.exists(self.filepath):
            print(f"Info: Settings file not found at '{self.filepath}'. Using default settings.")
            # ファイルが存在しない場合はデフォルト値のままなので何もしない
            # 必要であれば、ここでデフォルト設定でファイルを新規作成しても良い
            # self.save() # 初回起動時にデフォルト設定ファイルを作成する場合
            return

        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)
                # キーが存在しない場合に備えて .get() を使用し、デフォルト値を指定
                self.user_name = settings_data.get('user_name', DEFAULT_USER_NAME)
                self.selected_option_key = settings_data.get('selected_option_key', DEFAULT_OPTION_KEY)
                print(f"Info: Settings loaded from '{self.filepath}'")
        except json.JSONDecodeError:
            print(f"Error: Failed to decode JSON from '{self.filepath}'. Using default settings.")
            # デフォルト値に戻す (念のため)
            self.user_name = DEFAULT_USER_NAME
            self.selected_option_key = DEFAULT_OPTION_KEY
        except Exception as e:
            print(f"Error: Failed to load settings from '{self.filepath}': {e}. Using default settings.")
            # デフォルト値に戻す (念のため)
            self.user_name = DEFAULT_USER_NAME
            self.selected_option_key = DEFAULT_OPTION_KEY

    def save(self):
        """
        現在の設定を JSON ファイルに保存します。
        """
        settings_data = {
            'user_name': self.user_name,
            'selected_option_key': self.selected_option_key
        }
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                # indent=4 で整形して書き込む
                json.dump(settings_data, f, ensure_ascii=False, indent=4)
            print(f"Info: Settings saved to '{self.filepath}'")
        except IOError as e:
            print(f"Error: Failed to save settings to '{self.filepath}': {e}")
        except Exception as e:
            print(f"Error: An unexpected error occurred while saving settings: {e}")

# --- テスト用 ---
if __name__ == '__main__':
    print("Testing UserSettings...")
    settings = UserSettings("test_settings.json") # テスト用に別ファイル名

    print(f"Initial settings: Name='{settings.user_name}', Option='{settings.selected_option_key}'")

    # 設定を変更して保存
    settings.user_name = "Test User"
    settings.selected_option_key = "#settings.option_b"
    settings.save()

    # 再度読み込んで確認
    settings_reloaded = UserSettings("test_settings.json")
    print(f"Reloaded settings: Name='{settings_reloaded.user_name}', Option='{settings_reloaded.selected_option_key}'")

    # テスト用ファイルを削除
    try:
        os.remove(settings_reloaded.filepath)
        print("Info: Test settings file removed.")
    except OSError as e:
        print(f"Warning: Could not remove test settings file: {e}")

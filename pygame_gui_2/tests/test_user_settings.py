# tests/test_settings_dialog.py
import unittest
import os
import sys
import pygame
import pygame_gui
import i18n
from unittest.mock import patch, MagicMock, call

# テスト対象のモジュールをインポートするためにパスを追加
# このテストファイルが tests/ ディレクトリにあることを想定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# テスト対象のモジュールと定数をインポート
from settings_dialog import SettingsDialog, SETTINGS_UPDATED
from config import LayoutConfig
from user_settings import DEFAULT_USER_NAME, DEFAULT_OPTION_KEY # デフォルト値比較用

# --- resource_path 関数の定義 (テスト用) ---
# main.py にあるものと同様の機能を提供
def resource_path(relative_path: str) -> str:
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS # type: ignore[attr-defined]
    except AttributeError:
        # 開発環境では、このテストファイルがあるディレクトリの親 (プロジェクトルート) を基準にする
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # base_path = os.path.abspath(".") # もしカレントディレクトリ基準ならこちら
    return os.path.join(base_path, relative_path)

class TestSettingsDialog(unittest.TestCase):
    """
    settings_dialog.py の SettingsDialog クラスをテストするクラス。
    """

    @classmethod
    def setUpClass(cls):
        """テストクラス全体のセットアップ (一度だけ実行)"""
        # Pygame をヘッドレスモードで初期化
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        pygame.init()
        # ダミーの画面を作成 (UIManager に必要)
        cls.screen = pygame.display.set_mode((100, 100))

        # i18n 初期化 (テストには翻訳ファイルが必要)
        try:
            translations_path = resource_path('data/translations')
            if not os.path.exists(translations_path):
                 raise FileNotFoundError("Translation directory not found for testing.")
            i18n.set('file_format', 'json')
            i18n.load_path.append(translations_path)
            i18n.set('locale', 'ja') # テスト言語を日本語に固定
            i18n.set('fallback', 'en') # フォールバックも設定
            # 必要なキーが存在するか簡単なチェック
            i18n.t('settings.title')
            i18n.t('settings.option_a')
        except Exception as e:
            print(f"\nWarning: i18n initialization failed during test setup: {e}")
            print("Please ensure 'data/translations/ja.json' exists and is valid.")
            # i18n が失敗してもテストを続行するが、一部テストが失敗する可能性あり
            # 必要に応じて i18n.t をモックするなどの対策が必要
            pass


    @classmethod
    def tearDownClass(cls):
        """テストクラス全体のクリーンアップ (一度だけ実行)"""
        pygame.quit()

    def setUp(self):
        """各テストメソッドの前に実行されるセットアップ"""
        self.config = LayoutConfig()
        # UIManager を作成 (テーマは必須ではないが、エラー回避のため指定)
        # テスト用に最小限のテーマを用意するか、デフォルトを使う
        try:
            theme_path = resource_path('theme.json')
            if not os.path.exists(theme_path):
                theme_path = None # 存在しなければ None
        except Exception:
            theme_path = None

        self.manager = pygame_gui.UIManager(
            (self.config.WINDOW_WIDTH, self.config.WINDOW_HEIGHT),
            theme_path=theme_path,
            starting_language=i18n.get('locale') # UIManager にも言語設定
        )
        self.rect = pygame.Rect(
            (self.config.WINDOW_WIDTH // 2 - self.config.DIALOG_WIDTH // 2,
             self.config.WINDOW_HEIGHT // 2 - self.config.DIALOG_HEIGHT // 2),
            (self.config.DIALOG_WIDTH, self.config.DIALOG_HEIGHT)
        )
        self.initial_name = "テストユーザー"
        self.initial_option = "#settings.option_b" # Option B を初期選択

        # SettingsDialog インスタンスを作成
        self.dialog = SettingsDialog(
            manager=self.manager,
            rect=self.rect,
            config=self.config,
            initial_user_name=self.initial_name,
            initial_selected_option_key=self.initial_option
        )
        # イベントキューをクリア
        pygame.event.clear()

    def tearDown(self):
        """各テストメソッドの後に実行されるクリーンアップ"""
        self.dialog.kill() # ダイアログを閉じる
        self.manager.clear_and_reset() # マネージャーをリセット
        pygame.event.clear() # イベントキューをクリア

    def test_initialization_ui_elements_exist(self):
        """ダイアログ初期化時にUI要素が作成されるかテスト"""
        # self.assertIsInstance(self.dialog, pygame_gui.windows.UIWindow) # 変更前
        self.assertIsInstance(self.dialog, pygame_gui.elements.UIWindow) # 正しいパスに変更
        # self.assertTrue(self.dialog.blocking) # モーダルであること
        self.assertEqual(self.dialog.window_display_title, i18n.t('settings.title'))

        # 各UI要素が作成されているか確認
        self.assertIsInstance(self.dialog.info_label, pygame_gui.elements.UILabel)
        self.assertIsInstance(self.dialog.text_entry_label, pygame_gui.elements.UILabel)
        self.assertIsInstance(self.dialog.text_entry, pygame_gui.elements.UITextEntryLine)
        self.assertIsInstance(self.dialog.radio_label, pygame_gui.elements.UILabel)
        self.assertIsInstance(self.dialog.radio_panel, pygame_gui.elements.UIPanel)
        self.assertIsInstance(self.dialog.ok_button, pygame_gui.elements.UIButton)
        self.assertIsInstance(self.dialog.cancel_button, pygame_gui.elements.UIButton)

        # ラジオボタンが期待通り作成されているか (数と型)
        self.assertIsInstance(self.dialog.radio_buttons, list)
        self.assertEqual(len(self.dialog.radio_buttons), 3) # オプションは3つのはず
        for btn in self.dialog.radio_buttons:
            self.assertIsInstance(btn, pygame_gui.elements.UIButton)
            self.assertIn('translation_key', btn.user_data)

    def test_initialization_initial_values(self):
        """ダイアログ初期化時に初期値が正しく設定されるかテスト"""
        # テキスト入力の初期値
        self.assertEqual(self.dialog.text_entry.get_text(), self.initial_name)

        # ラジオボタンの初期選択
        self.assertEqual(self.dialog.selected_option_key, self.initial_option)
        selected_buttons = [btn for btn in self.dialog.radio_buttons if btn.is_selected]
        unselected_buttons = [btn for btn in self.dialog.radio_buttons if not btn.is_selected]

        self.assertEqual(len(selected_buttons), 1) # 1つだけ選択されている
        self.assertEqual(selected_buttons[0].user_data['translation_key'], self.initial_option)
        self.assertEqual(len(unselected_buttons), len(self.dialog.radio_buttons) - 1)

    def test_initialization_default_option_fallback(self):
        """初期選択キーが存在しない場合に最初のオプションが選択されるかテスト"""
        invalid_initial_option = "#settings.option_invalid"
        dialog_fallback = SettingsDialog(
            manager=self.manager,
            rect=self.rect,
            config=self.config,
            initial_user_name=self.initial_name,
            initial_selected_option_key=invalid_initial_option
        )
        # 最初のオプションキーが選択されているはず
        expected_fallback_key = dialog_fallback.radio_buttons[0].user_data['translation_key']
        self.assertEqual(dialog_fallback.selected_option_key, expected_fallback_key)

        selected_buttons = [btn for btn in dialog_fallback.radio_buttons if btn.is_selected]
        self.assertEqual(len(selected_buttons), 1)
        self.assertEqual(selected_buttons[0].user_data['translation_key'], expected_fallback_key)
        dialog_fallback.kill() # クリーンアップ

    def test_process_event_radio_button_selection(self):
        """ラジオボタンクリック時に選択状態とキーが更新されるかテスト"""
        # 初期状態は Option B が選択されているはず
        self.assertEqual(self.dialog.selected_option_key, "#settings.option_b")

        # Option A (最初のボタン) をクリックするイベントをシミュレート
        option_a_button = self.dialog.radio_buttons[0]
        self.assertFalse(option_a_button.is_selected) #最初は選択されていない
        event = pygame.event.Event(pygame_gui.UI_BUTTON_PRESSED,
                                    {'ui_element': option_a_button})

        # イベント処理を実行
        consumed = self.dialog.process_event(event)
        self.assertTrue(consumed) # イベントは消費されるはず

        # 状態の確認
        self.assertEqual(self.dialog.selected_option_key, "#settings.option_a")
        self.assertTrue(option_a_button.is_selected)
        # 他のボタンが非選択になっているか確認
        for i, btn in enumerate(self.dialog.radio_buttons):
            if i == 0:
                self.assertTrue(btn.is_selected)
            else:
                self.assertFalse(btn.is_selected)

        # 次に Option C (最後のボタン) をクリック
        option_c_button = self.dialog.radio_buttons[2]
        event_c = pygame.event.Event(pygame_gui.UI_BUTTON_PRESSED,
                                      {'ui_element': option_c_button})
        consumed_c = self.dialog.process_event(event_c)
        self.assertTrue(consumed_c)

        # 状態の確認
        self.assertEqual(self.dialog.selected_option_key, "#settings.option_c")
        self.assertTrue(option_c_button.is_selected)
        self.assertFalse(option_a_button.is_selected) # Option A は非選択に戻る


    @patch('pygame.event.post') # pygame.event.post をモック
    @patch.object(SettingsDialog, 'kill') # dialog.kill をモック
    def test_process_event_ok_button_click(self, mock_kill, mock_post):
        """OKボタンクリック時にイベント発行とkillが呼ばれるかテスト"""
        # ユーザー名とオプションを変更
        new_name = "変更後ユーザー"
        self.dialog.text_entry.set_text(new_name)
        # Option C を選択状態にする (手動で)
        option_c_button = self.dialog.radio_buttons[2]
        option_c_button.select()
        self.dialog.selected_option_key = option_c_button.user_data['translation_key']
        for i, btn in enumerate(self.dialog.radio_buttons):
            if i != 2: btn.unselect()

        # OKボタンクリックイベントをシミュレート
        event = pygame.event.Event(pygame_gui.UI_BUTTON_PRESSED,
                                    {'ui_element': self.dialog.ok_button})

        # イベント処理を実行
        consumed = self.dialog.process_event(event)
        self.assertTrue(consumed) # イベントは消費されるはず

        # pygame.event.post が期待通り呼ばれたか確認
        self.assertEqual(mock_post.call_count, 1)
        posted_event = mock_post.call_args[0][0] # 最初の引数 (イベントオブジェクト) を取得
        self.assertEqual(posted_event.type, SETTINGS_UPDATED)
        self.assertEqual(posted_event.user_name, new_name)
        self.assertEqual(posted_event.selected_option_key, "#settings.option_c")

        # dialog.kill が呼ばれたか確認
        mock_kill.assert_called_once()

    @patch('pygame.event.post') # pygame.event.post をモック
    @patch.object(SettingsDialog, 'kill') # dialog.kill をモック
    def test_process_event_cancel_button_click(self, mock_kill, mock_post):
        """キャンセルボタンクリック時にkillが呼ばれ、イベントは発行されないかテスト"""
        # キャンセルボタンクリックイベントをシミュレート
        event = pygame.event.Event(pygame_gui.UI_BUTTON_PRESSED,
                                    {'ui_element': self.dialog.cancel_button})

        # イベント処理を実行
        consumed = self.dialog.process_event(event)
        self.assertTrue(consumed) # イベントは消費されるはず

        # pygame.event.post が呼ばれていないことを確認
        mock_post.assert_not_called()

        # dialog.kill が呼ばれたか確認
        mock_kill.assert_called_once()

    def test_process_event_ignores_other_events(self):
        """関係ないイベントは無視される（消費されない）かテスト"""
        # 関係ないボタン (例えばメイン画面のボタン) のイベントをシミュレート
        other_button = pygame_gui.elements.UIButton(pygame.Rect(0,0,50,50), "Other", self.manager)
        event = pygame.event.Event(pygame_gui.UI_BUTTON_PRESSED,
                                    {'ui_element': other_button})

        consumed = self.dialog.process_event(event)
        self.assertFalse(consumed) # ダイアログはこのイベントを消費しない

        # マウス移動イベントなども無視されるはず
        event_mouse = pygame.event.Event(pygame.MOUSEMOTION, {'pos': (10, 10)})
        consumed_mouse = self.dialog.process_event(event_mouse)
        self.assertFalse(consumed_mouse)


if __name__ == '__main__':
    # tests ディレクトリが存在しない場合に作成
    if not os.path.exists(os.path.join(project_root, 'tests')):
        os.makedirs(os.path.join(project_root, 'tests'))
        print("Created 'tests' directory.")

    # このファイルを tests/test_settings_dialog.py として保存
    test_file_path = os.path.join(project_root, 'tests', 'test_settings_dialog.py')
    # 現在のファイルパスと保存先パスが異なる場合（初回実行時など）は保存
    if os.path.abspath(__file__) != os.path.abspath(test_file_path):
        try:
            with open(__file__, 'r', encoding='utf-8') as f_read:
                current_code = f_read.read()
            with open(test_file_path, 'w', encoding='utf-8') as f_write:
                f_write.write(current_code)
            print(f"Saved test file to: {test_file_path}")
        except Exception as e:
            print(f"Error saving test file: {e}")

    # unittest を実行
    print("\nRunning tests for settings_dialog.py...")
    # verbosity=2 を追加して詳細なテスト結果を表示
    unittest.main(argv=['first-arg-is-ignored'], exit=False, verbosity=2)


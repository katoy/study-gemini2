# tests/test_main.py
import unittest
import os
import sys
import pygame
import pygame_gui
import i18n
from unittest.mock import patch, MagicMock, call, ANY # ANY をインポート

# テスト対象のモジュールをインポートするためにパスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# テスト対象のモジュール
import main
from config import LayoutConfig
from user_settings import UserSettings
from settings_dialog import SETTINGS_UPDATED, SettingsDialog

# --- resource_path 関数の定義 (テスト用) ---
# main.py から resource_path を直接テストするために、ここでは定義しない
# 代わりに main.resource_path をテストする

class TestMainIntegration(unittest.TestCase):
    """
    main.py の主要な関数とループを統合テストに近い形でテストするクラス。
    pygame と pygame_gui を実際に初期化して使用します。
    """

    @classmethod
    def setUpClass(cls):
        """テストクラス全体のセットアップ"""
        print("Initializing Pygame for testing...")
        os.environ['SDL_VIDEODRIVER'] = 'dummy' # ヘッドレスモード
        pygame.init()
        pygame.display.set_mode((1, 1)) # 最小限の画面 (UIManager初期化に必要)
        print("Initializing i18n for testing...")
        try:
            # main.resource_path を使ってパスを取得
            translations_path = main.resource_path('data/translations')
            if not os.path.exists(translations_path):
                 raise FileNotFoundError("Translation directory not found for testing.")
            i18n.set('file_format', 'json')
            i18n.load_path.append(translations_path)
            i18n.set('locale', 'ja')
            i18n.set('fallback', 'en')
            i18n.t('main.window_title') # キーの存在確認
            print("i18n initialized successfully.")
        except Exception as e:
            print(f"\nWarning: i18n initialization failed: {e}")

    @classmethod
    def tearDownClass(cls):
        """テストクラス全体のクリーンアップ"""
        print("Quitting Pygame after testing...")
        pygame.quit()

    def setUp(self):
        """各テストメソッドの前に実行されるセットアップ"""
        print(f"\n--- Setting up for {self.id()} ---")
        self.config = LayoutConfig()
        self.user_settings = UserSettings(filename="test_main_settings.json")
        if os.path.exists(self.user_settings.filepath):
            os.remove(self.user_settings.filepath)
        self.user_settings.load()

        print("Setting up display and UIManager...")
        self.screen = pygame.display.set_mode((self.config.WINDOW_WIDTH, self.config.WINDOW_HEIGHT))
        try:
            theme_path = main.resource_path('theme.json')
            if not os.path.exists(theme_path):
                print("Warning: theme.json not found, using default theme.")
                theme_path = pygame_gui.PackageResource(package='pygame_gui.data', resource='default_theme.json')
        except Exception as e:
             print(f"Warning: Error finding theme.json: {e}. Using default theme.")
             theme_path = pygame_gui.PackageResource(package='pygame_gui.data', resource='default_theme.json')

        self.manager = pygame_gui.UIManager(
            (self.config.WINDOW_WIDTH, self.config.WINDOW_HEIGHT),
            theme_path=theme_path,
            starting_language=i18n.get('locale')
        )
        print("Creating UI elements...")
        self.settings_button, self.quit_button = main.create_ui_elements(self.manager, self.config)
        pygame.event.clear()

        self.patchers = []
        patcher_pygame_time_clock = patch('main.pygame.time.Clock')
        patcher_pygame_display_update = patch('main.pygame.display.update')
        patcher_settings_dialog = patch('main.SettingsDialog', spec=SettingsDialog)
        patcher_user_settings_save = patch.object(UserSettings, 'save')
        # --- ↓↓↓ pygame.event.get をモック対象に追加 ---
        patcher_pygame_event_get = patch('main.pygame.event.get')
        # --- ↑↑↑ ここまで追加 ↑↑↑ ---

        self.MockPygameClock = patcher_pygame_time_clock.start()
        self.patchers.append(patcher_pygame_time_clock)
        self.MockPygameDisplayUpdate = patcher_pygame_display_update.start()
        self.patchers.append(patcher_pygame_display_update)
        self.mock_settings_dialog_class = patcher_settings_dialog.start()
        self.patchers.append(patcher_settings_dialog)
        self.mock_settings_dialog_instance = self.mock_settings_dialog_class.return_value
        self.mock_settings_dialog_instance.alive.return_value = True
        self.mock_user_settings_save = patcher_user_settings_save.start()
        self.patchers.append(patcher_user_settings_save)
        # --- ↓↓↓ pygame.event.get のモックを開始 ---
        self.mock_event_get = patcher_pygame_event_get.start()
        self.patchers.append(patcher_pygame_event_get)
        # --- ↑↑↑ ここまで追加 ↑↑↑ ---

        self.mock_clock_instance = self.MockPygameClock.return_value
        self.mock_clock_instance.tick.return_value = 16.0

        main.SETTINGS_UPDATED = pygame.USEREVENT + 10

        print("Setup complete.")

    def tearDown(self):
        """各テストメソッドの後に実行されるクリーンアップ"""
        print(f"--- Tearing down {self.id()} ---")
        self.manager.clear_and_reset()
        for patcher in self.patchers:
            patcher.stop()
        if os.path.exists(self.user_settings.filepath):
            os.remove(self.user_settings.filepath)
        pygame.event.clear()
        print("Teardown complete.")

    # --- resource_path のテスト ---
    def test_resource_path_dev_environment(self):
        """resource_path: 開発環境でのパス取得をテスト"""
        # sys._MEIPASS がない状態をデフォルトとする
        # main.py と同じディレクトリをベースとする
        expected_base = os.path.dirname(os.path.abspath(main.__file__))
        self.assertEqual(main.resource_path("test.txt"), os.path.join(expected_base, "test.txt"))

    @patch('main.sys')
    def test_resource_path_frozen_environment(self, mock_sys):
        """resource_path: PyInstaller バンドル環境でのパス取得をテスト"""
        # sys._MEIPASS が存在する場合をシミュレート
        mock_sys._MEIPASS = '/frozen/path'
        # AttributeError を発生させないように __file__ も設定 (実際には使われないはず)
        mock_sys.__file__ = '/frozen/path/main.pyc'
        # frozen 属性は AttributeError 回避のため不要かも
        # delattr(mock_sys, 'frozen') # AttributeError を発生させる場合

        self.assertEqual(main.resource_path("test.txt"), '/frozen/path/test.txt')


    # --- initialize_* 関数のテスト (変更なし) ---
    @patch('pygame.init')
    @patch('pygame.display.set_mode')
    def test_initialize_pygame(self, mock_set_mode, mock_init):
        """initialize_pygame が pygame.init と set_mode を呼ぶかテスト"""
        screen = main.initialize_pygame(self.config)
        mock_init.assert_called_once()
        mock_set_mode.assert_called_once_with((self.config.WINDOW_WIDTH, self.config.WINDOW_HEIGHT))
        self.assertEqual(screen, mock_set_mode.return_value)

    @patch('main.resource_path', return_value='mock/translations')
    def test_initialize_i18n(self, mock_resource_path):
        """initialize_i18n が i18n の設定関数を正しく呼ぶかテスト"""
        original_load_path = list(i18n.load_path)
        i18n.load_path.clear()
        with patch('i18n.set') as mock_i18n_set:
             main.initialize_i18n()
             mock_resource_path.assert_called_once_with('data/translations')
             mock_i18n_set.assert_any_call('file_format', 'json')
             self.assertIn('mock/translations', i18n.load_path)
             mock_i18n_set.assert_any_call('locale', 'ja')
        i18n.load_path.clear()
        i18n.load_path.extend(original_load_path)

    @patch('main.resource_path')
    @patch('main.UIManager')
    def test_initialize_ui_manager(self, MockUIManager, mock_resource_path):
        """initialize_ui_manager が UIManager を正しく初期化するかテスト"""
        mock_resource_path.side_effect = lambda p: f'mock/{p}'
        manager = main.initialize_ui_manager(self.config)
        mock_resource_path.assert_has_calls([
            call('theme.json'),
            call('data/translations')
        ], any_order=True)
        MockUIManager.assert_called_once_with(
            (self.config.WINDOW_WIDTH, self.config.WINDOW_HEIGHT),
            theme_path='mock/theme.json',
            starting_language='ja',
            translation_directory_paths=['mock/data/translations']
        )
        self.assertEqual(manager, MockUIManager.return_value)

    # --- create_ui_elements のテスト (変更なし) ---
    def test_create_ui_elements(self):
        """create_ui_elements が UIButton を2つ作成するかテスト"""
        self.assertIsInstance(self.settings_button, pygame_gui.elements.UIButton)
        self.assertIsInstance(self.quit_button, pygame_gui.elements.UIButton)
        self.assertEqual(self.settings_button.text, i18n.t('main.settings_button'))
        self.assertEqual(self.quit_button.text, i18n.t('main.quit_button'))
        expected_settings_rect = pygame.Rect(
            (self.config.WINDOW_WIDTH // 2 - self.config.BUTTON_WIDTH - self.config.MARGIN,
             self.config.BUTTON_Y),
            (self.config.BUTTON_WIDTH, self.config.BUTTON_HEIGHT)
        )
        self.assertEqual(self.settings_button.relative_rect.topleft, expected_settings_rect.topleft)
        self.assertEqual(self.settings_button.relative_rect.size, expected_settings_rect.size)

    # --- run_main_loop のテスト (イベント処理と状態変化) ---
    # --- ↓↓↓ _run_loop_once を削除し、run_main_loop を直接呼び出すように変更 ---

    def test_run_main_loop_quit_event(self):
        """run_main_loop: QUIT イベントでループが終了するかテスト"""
        # 1回目はQUITイベント、2回目以降は呼ばれない想定 (ループが終了するため)
        self.mock_event_get.side_effect = [[pygame.event.Event(pygame.QUIT)]]
        main.run_main_loop(self.screen, self.manager, self.settings_button, self.quit_button, self.config, self.user_settings)
        # ループが1回実行されたことを確認
        self.mock_clock_instance.tick.assert_called_once()
        self.MockPygameDisplayUpdate.assert_called_once()
        # event.get が1回だけ呼ばれたことを確認
        self.mock_event_get.assert_called_once()

    def test_run_main_loop_quit_button_press(self):
        """run_main_loop: Quit ボタンクリックでループが終了するかテスト"""
        quit_event = pygame.event.Event(main.pygame_gui.UI_BUTTON_PRESSED, ui_element=self.quit_button)
        self.mock_event_get.side_effect = [[quit_event]]
        main.run_main_loop(self.screen, self.manager, self.settings_button, self.quit_button, self.config, self.user_settings)
        self.mock_clock_instance.tick.assert_called_once()
        self.MockPygameDisplayUpdate.assert_called_once()
        self.mock_event_get.assert_called_once()

    def test_run_main_loop_settings_button_press(self):
        """run_main_loop: Settings ボタンクリックでダイアログ表示とボタン無効化が行われるかテスト"""
        self.assertTrue(self.settings_button.is_enabled)
        settings_event = pygame.event.Event(main.pygame_gui.UI_BUTTON_PRESSED, ui_element=self.settings_button)
        # 1回目はSettingsボタン、2回目はQUIT
        self.mock_event_get.side_effect = [[settings_event], [pygame.event.Event(pygame.QUIT)]]
        main.run_main_loop(self.screen, self.manager, self.settings_button, self.quit_button, self.config, self.user_settings)

        # SettingsDialog が呼ばれたか確認
        self.mock_settings_dialog_class.assert_called_once()
        call_args, call_kwargs = self.mock_settings_dialog_class.call_args
        self.assertEqual(call_kwargs['manager'], self.manager)
        self.assertEqual(call_kwargs['initial_user_name'], self.user_settings.user_name)
        # ボタンが無効化されたか確認
        self.assertFalse(self.settings_button.is_enabled)
        # ループが2回実行されたことを確認
        self.assertEqual(self.mock_clock_instance.tick.call_count, 2)
        self.assertEqual(self.MockPygameDisplayUpdate.call_count, 2)
        self.assertEqual(self.mock_event_get.call_count, 2)

    def test_run_main_loop_settings_updated_event(self):
        """run_main_loop: SETTINGS_UPDATED イベントで設定保存とボタン有効化が行われるかテスト"""
        self.settings_button.disable()
        self.assertFalse(self.settings_button.is_enabled)
        new_name = "Updated Name"
        new_option = "#settings.option_c"
        updated_event = pygame.event.Event(main.SETTINGS_UPDATED,
                                           user_name=new_name,
                                           selected_option_key=new_option)
        # 1回目は設定更新イベント、2回目はQUIT
        self.mock_event_get.side_effect = [[updated_event], [pygame.event.Event(pygame.QUIT)]]
        main.run_main_loop(self.screen, self.manager, self.settings_button, self.quit_button, self.config, self.user_settings)

        # UserSettings の値が更新されたか確認
        self.assertEqual(self.user_settings.user_name, new_name)
        self.assertEqual(self.user_settings.selected_option_key, new_option)
        # save が呼ばれたか確認
        self.mock_user_settings_save.assert_called_once()
        # ボタンが有効化されたか確認
        self.assertTrue(self.settings_button.is_enabled)
        # ループが2回実行されたことを確認
        self.assertEqual(self.mock_clock_instance.tick.call_count, 2)
        self.assertEqual(self.MockPygameDisplayUpdate.call_count, 2)
        self.assertEqual(self.mock_event_get.call_count, 2)

    def test_run_main_loop_window_close_event(self):
        """run_main_loop: UI_WINDOW_CLOSE イベントでボタン有効化が行われるかテスト"""
        # 1. Settings ボタンを押すイベント
        settings_event = pygame.event.Event(main.pygame_gui.UI_BUTTON_PRESSED, ui_element=self.settings_button)
        # 2. Window Close イベント
        close_event = pygame.event.Event(main.pygame_gui.UI_WINDOW_CLOSE, ui_element=self.mock_settings_dialog_instance)
        # 3. QUIT イベント
        quit_event = pygame.event.Event(pygame.QUIT)
        self.mock_event_get.side_effect = [[settings_event], [close_event], [quit_event]]

        main.run_main_loop(self.screen, self.manager, self.settings_button, self.quit_button, self.config, self.user_settings)

        # ダイアログが開かれたことを確認
        self.mock_settings_dialog_class.assert_called_once()
        # ボタンが無効化され、その後有効化されたことを確認
        # (状態変化の最終結果を確認)
        self.assertTrue(self.settings_button.is_enabled)
        # ループが3回実行されたことを確認
        self.assertEqual(self.mock_clock_instance.tick.call_count, 3)
        self.assertEqual(self.MockPygameDisplayUpdate.call_count, 3)
        self.assertEqual(self.mock_event_get.call_count, 3)

    def test_run_main_loop_theme_error(self):
        """run_main_loop: テーマからの色取得失敗時にデフォルト色を使うかテスト"""
        # manager.get_theme().get_colour が例外を発生するようにモック
        with patch.object(self.manager.get_theme(), 'get_colour', side_effect=AttributeError("Mock theme error")):
            # print 出力をキャプチャ
            with patch('builtins.print') as mock_print:
                # 1回目は空イベント、2回目はQUIT
                self.mock_event_get.side_effect = [[], [pygame.event.Event(pygame.QUIT)]]
                main.run_main_loop(self.screen, self.manager, self.settings_button, self.quit_button, self.config, self.user_settings)

                # 警告メッセージが出力されたか確認
                mock_print.assert_any_call("Warning: Could not get 'normal_bg' from theme. Using default black.")
                # ループが2回実行されたことを確認
                self.assertEqual(self.mock_clock_instance.tick.call_count, 2)
                self.assertEqual(self.MockPygameDisplayUpdate.call_count, 2)
                self.assertEqual(self.mock_event_get.call_count, 2)

    # --- main 関数のテスト (変更なし) ---
    @patch('main.initialize_i18n')
    @patch('main.initialize_pygame')
    @patch('main.initialize_ui_manager')
    @patch('main.create_ui_elements')
    @patch('main.run_main_loop')
    @patch('main.LayoutConfig')
    @patch('main.UserSettings')
    @patch('main.pygame.quit') # main 内の pygame.quit をモック
    def test_main_function_calls(self, mock_pygame_quit, mock_user_settings, mock_layout_config, mock_run_main_loop,
                                 mock_create_ui_elements, mock_initialize_ui_manager,
                                 mock_initialize_pygame, mock_initialize_i18n):
        """main 関数が初期化関数とメインループを正しい順序で呼び出すかテスト"""
        mock_layout_config.return_value = self.config
        mock_user_settings.return_value = self.user_settings
        mock_screen = MagicMock(spec=pygame.Surface)
        mock_initialize_pygame.return_value = mock_screen
        mock_manager = MagicMock(spec=pygame_gui.UIManager)
        mock_initialize_ui_manager.return_value = mock_manager
        mock_settings_button = MagicMock(spec=pygame_gui.elements.UIButton)
        mock_quit_button = MagicMock(spec=pygame_gui.elements.UIButton)
        mock_create_ui_elements.return_value = (mock_settings_button, mock_quit_button)

        main.main()

        mock_layout_config.assert_called_once()
        mock_user_settings.assert_called_once()
        mock_initialize_i18n.assert_called_once()
        mock_initialize_pygame.assert_called_once_with(self.config)
        mock_initialize_ui_manager.assert_called_once_with(self.config)
        mock_create_ui_elements.assert_called_once_with(mock_manager, self.config)
        mock_run_main_loop.assert_called_once_with(
            mock_screen,
            mock_manager,
            mock_settings_button,
            mock_quit_button,
            self.config,
            self.user_settings
        )
        mock_pygame_quit.assert_called_once()


if __name__ == '__main__':
    # (変更なし)
    test_file_path = os.path.join(project_root, 'tests', 'test_main.py')
    if os.path.abspath(__file__) != os.path.abspath(test_file_path):
        try:
            with open(__file__, 'r', encoding='utf-8') as f_read:
                current_code = f_read.read()
            with open(test_file_path, 'w', encoding='utf-8') as f_write:
                f_write.write(current_code)
            print(f"Saved test file to: {test_file_path}")
        except Exception as e:
            print(f"Error saving test file: {e}")

    print("\nRunning tests for main.py...")
    unittest.main(argv=['first-arg-is-ignored'], exit=False, verbosity=2)


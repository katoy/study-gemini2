#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import pygame
import pygame_gui
import i18n

from pygame_gui import UIManager
from pygame_gui.elements import UIButton, UIWindow
# --- 必要なインポート ---
from config import LayoutConfig
# --- ↓↓↓ ここから追加 ↓↓↓ ---
from settings_dialog import SettingsDialog, SETTINGS_UPDATED # SETTINGS_UPDATED をインポート
from user_settings import UserSettings # UserSettings をインポート
# --- ↑↑↑ ここまで追加 ↑↑↑ ---

# --- 定数 ---
FPS = 60

def resource_path(relative_path: str) -> str:
    """
    実行環境（開発時または PyInstaller バンドル時）に応じて
    リソースファイルへの絶対パスを取得します。
    """
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def initialize_pygame(config: LayoutConfig) -> pygame.Surface:
    """
    Pygame の初期化、ウィンドウ作成を行います。
    """
    pygame.init()
    screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    return screen

def initialize_i18n():
    """
    i18n ライブラリの初期設定を行います。
    """
    translations_path = resource_path('data/translations')
    i18n.set('file_format', 'json')
    i18n.load_path.append(translations_path)
    i18n.set('locale', 'ja')

def initialize_ui_manager(config: LayoutConfig) -> UIManager:
    """
    Pygame GUI の UIManager を初期化し、テーマと翻訳を設定します。
    """
    manager = UIManager(
        (config.WINDOW_WIDTH, config.WINDOW_HEIGHT),
        theme_path=resource_path('theme.json'),
        starting_language=i18n.get('locale'),
        translation_directory_paths=[resource_path('data/translations')]
    )
    return manager

def create_ui_elements(manager: UIManager, config: LayoutConfig) -> tuple[UIButton, UIButton]:
    """
    メインウィンドウに表示する UI 要素（ボタンなど）を作成します。
    """
    settings_button = UIButton(
        relative_rect=pygame.Rect(
            (config.WINDOW_WIDTH // 2 - config.BUTTON_WIDTH - config.MARGIN,
            config.BUTTON_Y),
            (config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
        ),
        text=i18n.t('main.settings_button'),
        manager=manager,
        object_id='#settings_button'
    )

    quit_button = UIButton(
        relative_rect=pygame.Rect(
            (config.WINDOW_WIDTH // 2 + config.MARGIN,
            config.BUTTON_Y),
            (config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
        ),
        text=i18n.t('main.quit_button'),
        manager=manager,
        object_id='#quit_button'
    )
    return settings_button, quit_button

def run_main_loop(
    screen: pygame.Surface,
    manager: UIManager,
    settings_button: UIButton,
    quit_button: UIButton,
    config: LayoutConfig,
    user_settings: UserSettings # UserSettings インスタンスを受け取る
):
    """
    メインのイベントループを実行します。
    """
    clock = pygame.time.Clock()
    is_running = True
    settings_dialog_window: SettingsDialog | None = None

    try:
        background_colour = manager.get_theme().get_colour('normal_bg')
    except (AttributeError, ValueError):
        print("Warning: Could not get 'normal_bg' from theme. Using default black.")
        background_colour = pygame.Color(0, 0, 0)

    while is_running:
        time_delta = clock.tick(FPS) / 1000.0

        # --- イベント処理 ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False

            # --- ↓↓↓ ここから修正 ↓↓↓ ---
            # --- 設定更新イベント処理 ---
            elif event.type == SETTINGS_UPDATED:
                # イベントから更新された設定値を取得
                updated_user_name = event.user_name
                updated_selected_option_key = event.selected_option_key

                # UserSettings インスタンスを更新
                user_settings.user_name = updated_user_name
                user_settings.selected_option_key = updated_selected_option_key

                # 設定をファイルに保存
                user_settings.save()

                # ダイアログが閉じたので、ボタンを有効化し、参照をクリア
                settings_button.enable()
                settings_dialog_window = None # ダイアログ参照をクリア
                print(f"Settings updated and saved: Name='{updated_user_name}', Option='{updated_selected_option_key}'")

            # --- Pygame GUI イベント処理 ---
            elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == settings_button:
                    # 設定ダイアログが既に開いていなければ開く
                    if settings_dialog_window is None or not settings_dialog_window.alive():
                        settings_dialog_window = SettingsDialog(
                            manager=manager, # manager を最初に渡すように修正
                            rect=pygame.Rect(
                                (config.WINDOW_WIDTH // 2 - config.DIALOG_WIDTH // 2,
                                 config.WINDOW_HEIGHT // 2 - config.DIALOG_HEIGHT // 2),
                                (config.DIALOG_WIDTH, config.DIALOG_HEIGHT)
                            ),
                            config=config, # config 引数を渡す
                            # --- UserSettings から初期値を渡す ---
                            initial_user_name=user_settings.user_name,
                            initial_selected_option_key=user_settings.selected_option_key
                        )
                        settings_button.disable() # ダイアログ表示中はボタンを無効化

                elif event.ui_element == quit_button:
                    is_running = False

            elif event.type == pygame_gui.UI_WINDOW_CLOSE:
                # 設定ダイアログが (Xボタンなどで) 閉じられた場合
                if (settings_dialog_window is not None
                        and event.ui_element == settings_dialog_window):
                    settings_button.enable() # ボタンを再度有効化
                    settings_dialog_window = None # ダイアログ参照をクリア
                    print("Settings dialog closed without saving (via close button).")
            # --- ↑↑↑ ここまで修正 ↑↑↑ ---

            # UIManager にイベントを渡す
            manager.process_events(event)

        # --- 画面更新 ---
        manager.update(time_delta)
        screen.fill(background_colour)
        manager.draw_ui(screen)
        pygame.display.update()

def main():
    """
    アプリケーションのエントリーポイント。
    初期化処理、UI作成、メインループの実行を行います。
    """
    # --- 設定読み込み ---
    layout_config = LayoutConfig()
    # --- ↓↓↓ ここから追加 ↓↓↓ ---
    # UserSettings をインスタンス化 (ここで設定ファイルが読み込まれる)
    user_settings = UserSettings()
    # --- ↑↑↑ ここまで追加 ↑↑↑ ---

    # --- 国際化初期化 ---
    initialize_i18n()

    # --- Pygame 初期化 ---
    screen = initialize_pygame(layout_config)
    pygame.display.set_caption(i18n.t('main.window_title'))

    # --- UI マネージャー初期化 ---
    ui_manager = initialize_ui_manager(layout_config)

    # --- UI 要素作成 ---
    settings_button, quit_button = create_ui_elements(ui_manager, layout_config)

    # --- メインループ実行 ---
    # --- ↓↓↓ ここから修正 ↓↓↓ ---
    # user_settings を run_main_loop に渡す
    run_main_loop(screen, ui_manager, settings_button, quit_button, layout_config, user_settings)
    # --- ↑↑↑ ここまで修正 ↑↑↑ ---

    # --- 終了処理 ---
    pygame.quit()

if __name__ == "__main__":
    main()

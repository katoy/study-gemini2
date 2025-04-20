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
from settings_dialog import SettingsDialog

# --- 定数 ---
FPS = 60

def resource_path(relative_path: str) -> str:
    """
    実行環境（開発時または PyInstaller バンドル時）に応じて
    リソースファイルへの絶対パスを取得します。
    """
    try:
        # PyInstaller によって作成された一時フォルダからパスを取得
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
        # 通常の Python 環境の場合、このファイルのディレクトリを取得
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def initialize_pygame(config: LayoutConfig) -> pygame.Surface: # 戻り値を Surface のみに変更
    """
    Pygame の初期化、ウィンドウ作成を行います。
    """
    pygame.init()
    # ウィンドウタイトルは i18n 初期化後に main 関数で設定します
    screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    # background サーフェスの作成と fill を削除
    return screen # screen のみを返す

def initialize_i18n():
    """
    i18n ライブラリの初期設定を行います。
    """
    translations_path = resource_path('data/translations')
    i18n.set('file_format', 'json')
    i18n.load_path.append(translations_path)
    i18n.set('locale', 'ja') # デフォルト言語を設定
    # pygame_gui の翻訳形式 (#namespace.key) と i18n の形式 (namespace.key) の
    # 違いを吸収するため、必要に応じて設定を追加・調整します。
    # 現状、ウィンドウタイトルのみ i18n.t を使用しています。
    # i18n.set('filename_format', '{locale}.{format}') # 必要に応じて
    # i18n.set('skip_locale_root_data', True) # 必要に応じて

def initialize_ui_manager(config: LayoutConfig) -> UIManager:
    """
    Pygame GUI の UIManager を初期化し、テーマと翻訳を設定します。
    フォントのプリロードも行います。
    """
    manager = UIManager(
        (config.WINDOW_WIDTH, config.WINDOW_HEIGHT),
        theme_path=resource_path('theme.json'),
        starting_language=i18n.get('locale'), # i18n で設定した言語を使用
        translation_directory_paths=[resource_path('data/translations')]
    )
    # フォントのプリロード (テーマファイルで指定されていれば不要な場合もある)
    # theme.json で指定されているため、通常は不要
    # manager.preload_fonts([
    #     {'name': 'notosansjp', 'point_size': config.FONT_SIZE, 'style': 'regular'},
    # ])
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
        # pygame_gui の翻訳形式を使用
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
        # pygame_gui の翻訳形式を使用
        text=i18n.t('main.quit_button'),
        manager=manager,
        object_id='#quit_button'
    )
    return settings_button, quit_button

def run_main_loop(
    screen: pygame.Surface,
    # background 引数を削除
    manager: UIManager,
    settings_button: UIButton,
    quit_button: UIButton,
    config: LayoutConfig # config はダイアログ表示位置計算等で必要なので残す
):
    """
    メインのイベントループを実行します。
    """
    clock = pygame.time.Clock()
    is_running = True
    settings_dialog_window: SettingsDialog | None = None

    # --- テーマから背景色を取得 ---
    try:
        # UIManager が初期化された後でないとテーマを取得できないため、ループ内で取得
        # または、main 関数で manager 初期化後に取得して run_main_loop に渡す
        background_colour = manager.get_theme().get_colour('normal_bg')
    except (AttributeError, ValueError): # テーマや色が存在しない場合のエラーハンドリング
        print("Warning: Could not get 'normal_bg' from theme. Using default black.")
        background_colour = pygame.Color(0, 0, 0) # デフォルトは黒にする

    while is_running:
        time_delta = clock.tick(FPS) / 1000.0

        # --- イベント処理 ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False

            # --- Pygame GUI イベント処理 ---
            elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == settings_button:
                    # 設定ダイアログが既に開いていなければ開く
                    if settings_dialog_window is None or not settings_dialog_window.alive():
                        settings_dialog_window = SettingsDialog(
                            manager,
                            pygame.Rect(
                                (config.WINDOW_WIDTH // 2 - config.DIALOG_WIDTH // 2,
                                 config.WINDOW_HEIGHT // 2 - config.DIALOG_HEIGHT // 2),
                                (config.DIALOG_WIDTH, config.DIALOG_HEIGHT)
                            ),
                            config # config 引数を渡す
                        )
                        settings_button.disable() # ダイアログ表示中はボタンを無効化

                elif event.ui_element == quit_button:
                    is_running = False

            elif event.type == pygame_gui.UI_WINDOW_CLOSE:
                # 設定ダイアログが閉じられた場合
                if (settings_dialog_window is not None
                        and event.ui_element == settings_dialog_window):
                    settings_button.enable() # ボタンを再度有効化
                    settings_dialog_window = None # ダイアログ参照をクリア

            # UIManager にイベントを渡す
            manager.process_events(event)

        # --- 画面更新 ---
        manager.update(time_delta)

        # screen.fill() で画面をクリア
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
    # background を渡さない
    run_main_loop(screen, ui_manager, settings_button, quit_button, layout_config)

    # --- 終了処理 ---
    pygame.quit()

if __name__ == "__main__":
    main()

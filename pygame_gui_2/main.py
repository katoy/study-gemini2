#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import pygame
import pygame_gui
import i18n

from pygame_gui import UIManager
from pygame_gui.elements import UIButton
from config import LayoutConfig
from settings_dialog import SettingsDialog

def resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    """
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def main():
    # --- Pygame 初期化 ---
    pygame.init()

    # --- レイアウト設定読み込み ---
    layout = LayoutConfig()


    # --- 多言語対応設定 ---
    # JSON ファイルを使う設定
    i18n.set('file_format', 'json')
    # 翻訳ファイルのルート要素に "ja:" が無くても読み込む
    # i18n.set('skip_locale_root_data', True)
    # i18n.set('filename_format', '{locale}.{format}')

    translations_path = resource_path('data/translations')

    i18n.load_path.append(translations_path)
    i18n.set('locale', 'ja')

    print("---------------")
    print("Translation files search paths:", i18n.get('load_path'))
    # print("Available locales:", i18n.get('translations').keys())
    print("Lookup test:", i18n.t('main.settings_button'))
    print("Lookup test:", i18n.t('main.quit_button'))


    # --- UIManager の初期化 ---
    manager = UIManager(
    (layout.WINDOW_WIDTH, layout.WINDOW_HEIGHT),
    theme_path=resource_path('theme.json'),
    starting_language='ja',
    translation_directory_paths=[resource_path('data/translations')]
)


    # --- ウィンドウタイトル設定 ---
    pygame.display.set_caption(
        i18n.t('main.window_title')
    )
    screen = pygame.display.set_mode(
        (layout.WINDOW_WIDTH, layout.WINDOW_HEIGHT)
    )

    # --- フォントのプリロード ---
    manager.preload_fonts([
        {'name': 'notosansjp', 'point_size': layout.FONT_SIZE, 'style': 'regular'},
        # {'name': 'notosansjp', 'point_size': layout.FONT_SIZE, 'style': 'bold'},
    ])

    # --- 背景設定 ---
    background = pygame.Surface((layout.WINDOW_WIDTH, layout.WINDOW_HEIGHT))
    background.fill(pygame.Color('#f0f0f0'))

    # --- UI 要素の作成 ---
    settings_button = UIButton(
        relative_rect=pygame.Rect(
            (layout.WINDOW_WIDTH // 2 - layout.BUTTON_WIDTH - layout.MARGIN,
            layout.BUTTON_Y),
            (layout.BUTTON_WIDTH, layout.BUTTON_HEIGHT)
        ),
        text=i18n.t('main.settings_button'),
        manager=manager,
        object_id='#settings_button'
    )

    quit_button = UIButton(
        relative_rect=pygame.Rect(
            (layout.WINDOW_WIDTH // 2 + layout.MARGIN,
            layout.BUTTON_Y),
            (layout.BUTTON_WIDTH, layout.BUTTON_HEIGHT)
        ),
        text=i18n.t('main.quit_button'),
        manager=manager,
        object_id='#quit_button'
    )

    # --- メインループ ---
    clock = pygame.time.Clock()
    is_running = True
    settings_dialog_window = None

    while is_running:
        time_delta = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False

            elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == settings_button:
                    print("設定ボタンが押されました。")
                    if settings_dialog_window is None or not settings_dialog_window.alive():
                        settings_dialog_window = SettingsDialog(
                            manager,
                            pygame.Rect(
                                (layout.WINDOW_WIDTH // 2 - layout.DIALOG_WIDTH // 2,
                                 layout.WINDOW_HEIGHT // 2 - layout.DIALOG_HEIGHT // 2),
                                (layout.DIALOG_WIDTH, layout.DIALOG_HEIGHT)
                            )
                        )
                        settings_button.disable()

                elif event.ui_element == quit_button:
                    print("終了ボタンが押されました。")
                    is_running = False

            elif event.type == pygame_gui.UI_WINDOW_CLOSE:
                if (settings_dialog_window is not None
                        and event.ui_element == settings_dialog_window):
                    print("設定ダイアログが閉じられました。")
                    settings_button.enable()
                    settings_dialog_window = None

            manager.process_events(event)

        manager.update(time_delta)

        screen.blit(background, (0, 0))
        manager.draw_ui(screen)
        pygame.display.update()

    # --- 終了処理 ---
    pygame.quit()

if __name__ == "__main__":
    main()

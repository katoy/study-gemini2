#!/usr/bin/env python3
# minimal_test.py

import os
import sys
import pygame
import pygame_gui

def resource_path(relative_path: str) -> str:
    """
    アプリケーション実行フォルダからの相対パスを絶対パスに変換するユーティリティ。
    PyInstallerなどでバンドルした場合にも対応可能です。
    """
    # PyInstallerの実行時は _MEIPASS がセットされる
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def main():
    # Pygame初期化
    pygame.init()
    pygame.display.set_caption('Minimal Test – 日本語フォント対応')
    window_size = (640, 360)
    screen = pygame.display.set_mode(window_size)

    # UIManager生成
    manager = pygame_gui.UIManager(window_size)

    # フォントファイルのパスを動的に解決
    font_file = resource_path(os.path.join('fonts', 'NotoSansJP-Regular.ttf'))

    # フォントファイルの存在を確認
    if not os.path.isfile(font_file):
        raise FileNotFoundError(f'フォントファイルが見つかりません: {font_file}')

    # add_font_pathsで日本語対応フォントを登録
    manager.add_font_paths(
        font_name='MyFont',
        regular_path=font_file,
        bold_path=None,
        italic_path=None,
        bold_italic_path=None
    )  # :contentReference[oaicite:0]{index=0}

    # preload_fontsで事前に指定サイズのフォントを読み込む
    manager.preload_fonts([{
        'name': 'MyFont',
        'point_size': 24,
        'style': 'regular'
    }])  # :contentReference[oaicite:1]{index=1}

    # サンプルUI要素：日本語ラベル付きUIButton
    hello_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((220, 160), (200, 50)),
        text='こんにちは',
        manager=manager
    )

    clock = pygame.time.Clock()
    is_running = True
    while is_running:
        time_delta = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
            manager.process_events(event)

        manager.update(time_delta)
        screen.fill((30, 30, 30))
        manager.draw_ui(screen)
        pygame.display.update()

    pygame.quit()

if __name__ == '__main__':
    main()

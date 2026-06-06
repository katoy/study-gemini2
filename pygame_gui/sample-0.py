#!/usr/bin/env python3
# sample-0_refactored.py

import os
import sys
import pygame
import pygame_menu

# --- 定数定義 ---
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
WINDOW_CAPTION = 'Minimal Test – pygame-menu 日本語 (Refactored)'
FPS = 60

FONT_DIR = 'fonts'
FONT_FILENAME = 'NotoSansJP-Regular.ttf'
# フォントが見つからない場合の代替フォント (pygame-menu のデフォルトの一つ)
DEFAULT_FALLBACK_FONT = pygame_menu.font.FONT_OPEN_SANS

MENU_WIDTH_RATIO = 0.8  # ウィンドウ幅に対するメニュー幅の比率
MENU_HEIGHT_RATIO = 0.7 # ウィンドウ高さに対するメニュー高さの比率
# 必要に応じてテーマのフォントサイズを指定
# THEME_WIDGET_FONT_SIZE = 24
# THEME_TITLE_FONT_SIZE = 30

# --- ヘルパー関数 ---
def resource_path(relative_path: str) -> str:
    """
    アプリケーション実行フォルダからの相対パスを絶対パスに変換するユーティリティ。
    PyInstallerなどでバンドルした場合にも対応可能です。
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # 通常の実行時はスクリプトのあるディレクトリを基準にする
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# --- 初期化関連 ---
def initialize_pygame(width: int, height: int, caption: str) -> pygame.Surface:
    """ Pygame を初期化し、画面 Surface を返す """
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(caption)
    print("Pygame initialized.")
    return screen

def create_menu_theme(font_dir: str, font_filename: str, fallback_font: str) -> pygame_menu.Theme:
    """ 日本語フォントを含むカスタムテーマを作成する """
    font_path = resource_path(os.path.join(font_dir, font_filename))
    selected_font_path = fallback_font # デフォルトは代替フォント

    if os.path.isfile(font_path):
        print(f'フォントファイルを読み込みます: {font_path}')
        selected_font_path = font_path
    else:
        print(f'警告: 指定されたフォントファイルが見つかりません: {font_path}')
        print(f'pygame-menu のデフォルトフォント ({os.path.basename(fallback_font)}) を使用します。')

    # カスタムテーマを作成 (デフォルトテーマをコピー)
    theme = pygame_menu.themes.THEME_DEFAULT.copy()
    theme.widget_font = selected_font_path
    theme.title_font = selected_font_path

    # 定義されていればフォントサイズを設定
    if 'THEME_WIDGET_FONT_SIZE' in globals():
        theme.widget_font_size = THEME_WIDGET_FONT_SIZE
        print(f"Widget font size set to: {THEME_WIDGET_FONT_SIZE}")
    if 'THEME_TITLE_FONT_SIZE' in globals():
        theme.title_font_size = THEME_TITLE_FONT_SIZE
        print(f"Title font size set to: {THEME_TITLE_FONT_SIZE}")

    print("Menu theme created.")
    return theme

# --- メニュー作成 ---
def create_main_menu(width: int, height: int, theme: pygame_menu.Theme) -> pygame_menu.Menu:
    """ メインメニューを作成し、ウィジェットを追加する """

    menu_width = int(width * MENU_WIDTH_RATIO)
    menu_height = int(height * MENU_HEIGHT_RATIO)

    menu = pygame_menu.Menu(
        title='メインメニュー',
        width=menu_width,
        height=menu_height,
        theme=theme
    )

    # --- ボタンクリック時のアクション ---
    def print_hello_action():
        """ 「こんにちは」ボタンがクリックされたときに呼び出される """
        print("こんにちはボタンが押されました！")

    # --- ウィジェットの追加 ---
    menu.add.text_input('名前 : ', default='山田太郎', maxchar=20) # 最大文字数を追加
    menu.add.vertical_margin(10) # ウィジェット間のスペース
    menu.add.button('こんにちは', print_hello_action)
    menu.add.vertical_margin(10)
    menu.add.button('終了', pygame_menu.events.EXIT) # メニューを閉じるイベント

    print("Main menu created with widgets.")
    return menu

# --- メインループ ---
def run_game_loop(screen: pygame.Surface, menu: pygame_menu.Menu):
    """ メインゲームループを実行する """
    clock = pygame.time.Clock()
    is_running = True

    print("Starting main loop...")
    while is_running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                is_running = False
                break # イベントループを抜ける

        if not is_running:
            break # メインループを抜ける

        # メニューが有効な場合のみ更新と描画を行う
        if menu.is_enabled():
            menu.update(events)
            # 背景はメニューテーマに任せる (必要ならここで screen.fill() を呼ぶ)
            menu.draw(screen)

        pygame.display.update()
        clock.tick(FPS)

    print("Exiting main loop.")

# --- メイン実行ブロック ---
def main():
    """ アプリケーションのエントリーポイント """
    screen = initialize_pygame(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_CAPTION)
    theme = create_menu_theme(FONT_DIR, FONT_FILENAME, DEFAULT_FALLBACK_FONT)
    main_menu = create_main_menu(WINDOW_WIDTH, WINDOW_HEIGHT, theme)
    run_game_loop(screen, main_menu)

    pygame.quit()
    print("Pygame quit. アプリケーションを終了しました。")

if __name__ == '__main__':
    main()

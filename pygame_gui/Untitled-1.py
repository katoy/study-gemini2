#!/usr/bin/env python3
# sample-thorpy.py (修正版)

import os
import sys
import pygame
import thorpy # ThorPy をインポート

# --- 定数定義 ---
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
WINDOW_CAPTION = 'Minimal Test – ThorPy 日本語'
FPS = 60

FONT_DIR = 'fonts'
FONT_FILENAME = 'NotoSansJP-Regular.ttf'
DEFAULT_FONT_SIZE = 18 # デフォルトのフォントサイズ

# --- ヘルパー関数 ---
def resource_path(relative_path: str) -> str:
    """
    アプリケーション実行フォルダからの相対パスを絶対パスに変換するユーティリティ。
    PyInstallerなどでバンドルした場合にも対応可能です。
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# --- 初期化関連 ---
def initialize_pygame_and_thorpy(width: int, height: int, caption: str) -> pygame.Surface:
    """ Pygame を初期化し、画面 Surface を返し、ThorPy を初期化する """
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(caption)
    # ThorPy の初期化 (テーマ指定は要素ごとに行うかデフォルトに任せる)
    thorpy.init(screen)
    print("Pygame and ThorPy initialized.")
    return screen

# setup_thorpy_font 関数は不要なので削除

# --- アクション関数 ---
def print_hello_action():
    """ 「こんにちは」ボタンがクリックされたときに呼び出される """
    print("こんにちはボタンが押されました！")

def quit_action():
    """ 終了ボタンがクリックされたときに呼び出される """
    print("終了ボタンが押されました。アプリケーションを終了します。")
    thorpy.functions.quit_func() # ThorPy の終了関数を呼び出す

# --- メイン実行ブロック ---
def main():
    """ アプリケーションのエントリーポイント """
    screen = initialize_pygame_and_thorpy(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_CAPTION)

    # フォントパスを取得し、存在を確認
    font_path = resource_path(os.path.join(FONT_DIR, FONT_FILENAME))
    if not os.path.isfile(font_path):
        print(f'警告: 指定されたフォントファイルが見つかりません: {font_path}')
        print("ThorPy のデフォルトフォントが使用されます。")
        font_path = None # フォントが見つからない場合は None

    # --- ThorPy 要素の作成 (フォント情報を指定) ---

    # タイトルラベル (thorpy.make_text を使用)
    title_label = thorpy.make_text(
        "メインメニュー",
        font_size=DEFAULT_FONT_SIZE + 4,
        font_path=font_path # 見つからなければ None が渡されデフォルトフォントになる
    )

    # テキスト入力 (thorpy.make_inserter を使用)
    # 注意: IME を使った日本語入力は難しい場合があります。
    name_inserter = thorpy.make_inserter(
        "名前 : ",
        value="山田太郎",
        size=(200, 30), # Inserter のサイズを指定
        font_size=DEFAULT_FONT_SIZE,
        font_path=font_path
    )
    # name_inserter.set_font_auto() # フォントサイズ自動調整 (必要なら)

    # ボタン (thorpy.make_button を使用)
    hello_button = thorpy.make_button(
        "こんにちは",
        func=print_hello_action,
        params={"font_size": DEFAULT_FONT_SIZE, "font_path": font_path} # params でフォント指定
    )

    quit_button = thorpy.make_button(
        "終了",
        func=quit_action,
        params={"font_size": DEFAULT_FONT_SIZE, "font_path": font_path} # params でフォント指定
    )

    # --- 要素を Box にまとめる ---
    # Box は要素を縦に並べるコンテナ
    box = thorpy.Box(elements=[
        title_label,
        name_inserter,
        hello_button,
        quit_button
    ])
    box.set_gap(10) # 要素間のスペースを設定
    box.center()    # Box を画面中央に配置
    # box.add_lift() # add_lift は古いAPIか存在しない可能性があるので削除

    # --- メニュー/イベントループの開始 ---
    # Menu は要素のイベント処理と描画を行う
    menu = thorpy.Menu(box)

    # 背景要素を作成 (画面全体を覆う)
    background = thorpy.Background(color=(30, 30, 30), elements=[menu]) # 背景色とメニューを指定
    thorpy.store(background) # 背景を ThorPy の管理下に置く

    # メインループを開始
    print("Starting ThorPy main loop...")
    menu.play() # イベントループを実行

    # --- 終了処理 ---
    # thorpy.functions.quit_func() が呼ばれるとループが終了する
    pygame.quit()
    print("Pygame quit. アプリケーションを終了しました。")

if __name__ == '__main__':
    main()

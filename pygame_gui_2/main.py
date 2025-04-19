#!/usr/bin/env python3
# main.py (分割後・終了ボタン追加)

# --- ライブラリのインポート ---
import pygame           # Pygame 本体
import pygame_gui       # Pygame GUI ライブラリ
from pygame_gui.elements import UIButton # メインウィンドウで使うボタンのみインポート
from pygame_gui import UIManager # UI 要素を管理するマネージャークラス
import os               # ファイルパス操作用
import sys              # resource_path 関数で PyInstaller 対応などに使用

# --- 他のファイルからインポート ---
from settings_dialog import SettingsDialog # 作成したダイアログクラスをインポート

# --- 定数定義 ---
WINDOW_WIDTH = 600      # メインウィンドウの幅
WINDOW_HEIGHT = 400     # メインウィンドウの高さ
DIALOG_WIDTH = 400      # 設定ダイアログの幅 (ダイアログ生成時に使用)
DIALOG_HEIGHT = 300     # 設定ダイアログの高さ (ダイアログ生成時に使用)
BUTTON_WIDTH = 150      # ボタンの幅
BUTTON_HEIGHT = 50      # ボタンの高さ
BUTTON_MARGIN = 10      # ボタン間の垂直マージン

# --- ヘルパー関数 (フォントパス解決用) ---
def resource_path(relative_path: str) -> str:
    """
    アプリケーション実行フォルダからの相対パスを絶対パスに変換します。
    PyInstaller などで実行ファイル化した場合でもリソースファイル（フォントなど）
    を見つけられるようにするための関数です。
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# --- メイン処理関数 ---
def main():
    # 1. Pygame の初期化
    pygame.init()
    pygame.display.set_caption('モーダルダイアログ サンプル')
    window_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    background = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    background.fill(pygame.Color('#DDDDDD'))

    # 2. UIManager の初期化
    manager = UIManager((WINDOW_WIDTH, WINDOW_HEIGHT), starting_language='ja')

    # 3. カスタム日本語フォントの読み込みと設定
    font_path = resource_path(os.path.join('fonts', 'NotoSansJP-Regular.ttf'))
    if not os.path.isfile(font_path):
        print(f"警告: フォントファイルが見つかりません: {font_path}")
    else:
        manager.add_font_paths('noto_sans_jp', regular_path=font_path)
        manager.preload_fonts([
            {'name': 'noto_sans_jp', 'point_size': 14, 'style': 'regular'},
            {'name': 'noto_sans_jp', 'point_size': 18, 'style': 'regular'}
        ])
        print(f"フォント '{os.path.basename(font_path)}' をロードしました。")

    # 4. メインウィンドウに表示する UI 要素の作成
    # ボタンを中央に縦に並べるための開始Y座標を計算
    total_button_height = BUTTON_HEIGHT * 2 + BUTTON_MARGIN
    start_y = (WINDOW_HEIGHT - total_button_height) // 2
    button_x = (WINDOW_WIDTH - BUTTON_WIDTH) // 2

    # 「設定」ボタン
    settings_button_rect = pygame.Rect(
        (button_x, start_y),
        (BUTTON_WIDTH, BUTTON_HEIGHT)
    )
    settings_button = UIButton(
        relative_rect=settings_button_rect,
        text='設定',
        manager=manager,
        object_id='#settings_button'
    )

    # 「終了」ボタン (設定ボタンの下に配置)
    quit_button_rect = pygame.Rect(
        (button_x, settings_button_rect.bottom + BUTTON_MARGIN),
        (BUTTON_WIDTH, BUTTON_HEIGHT)
    )
    quit_button = UIButton(
        relative_rect=quit_button_rect,
        text='終了',
        manager=manager,
        object_id='#quit_button' # 終了ボタン用のID (任意)
    )


    # 5. メインループ
    clock = pygame.time.Clock()
    is_running = True
    active_dialog: SettingsDialog | None = None # 型ヒントもインポートしたクラスを使う

    while is_running:
        time_delta = clock.tick(60) / 1000.0

        # --- イベント処理ループ ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False

            manager.process_events(event)

            # --- メインウィンドウのボタンクリック処理 ---
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                # 「設定」ボタンが押され、かつダイアログが表示されていない場合
                if event.ui_element == settings_button and active_dialog is None:
                    print("設定ボタンが押されました。ダイアログを開きます。")
                    dialog_rect = pygame.Rect(
                        ((WINDOW_WIDTH - DIALOG_WIDTH) // 2, (WINDOW_HEIGHT - DIALOG_HEIGHT) // 2),
                        (DIALOG_WIDTH, DIALOG_HEIGHT)
                    )
                    # インポートした SettingsDialog クラスを使用
                    active_dialog = SettingsDialog(manager, dialog_rect)
                    # モーダル化: ダイアログ表示中は両方のボタンを無効化
                    settings_button.disable()
                    quit_button.disable()

                # 「終了」ボタンが押された場合
                elif event.ui_element == quit_button:
                    print("終了ボタンが押されました。")
                    is_running = False # メインループを終了させる

            # --- ダイアログが閉じられた時の処理 ---
            if event.type == pygame_gui.UI_WINDOW_CLOSE:
                if active_dialog is not None and event.ui_element == active_dialog:
                    print("設定ダイアログが閉じられました。")
                    active_dialog = None
                    # モーダル化解除: 両方のボタンを再度有効化
                    settings_button.enable()
                    quit_button.enable()

        # --- 状態更新 ---
        manager.update(time_delta)

        # --- 描画 ---
        window_surface.blit(background, (0, 0))
        manager.draw_ui(window_surface)
        pygame.display.update()

    # メインループ終了後、Pygame を終了
    pygame.quit()

# このスクリプトが直接実行された場合に main() 関数を呼び出す
if __name__ == '__main__':
    main()

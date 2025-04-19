#!/usr/bin/env python3
# sample-5_modal_dialog.py (sample-5.py を変更)

import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UILabel, UITextEntryLine, UIWindow, UIPanel
from pygame_gui import UIManager
import os
import sys # resource_path のために追加

# --- 定数 ---
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400
DIALOG_WIDTH = 400
DIALOG_HEIGHT = 300 # ダイアログの高さを調整

# --- ヘルパー関数 (フォントパス解決用) ---
def resource_path(relative_path: str) -> str:
    """ アプリケーション実行フォルダからの相対パスを絶対パスに変換 """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# --- SettingsDialog クラス ---
class SettingsDialog(UIWindow):
    """ 設定ダイアログウィンドウ """
    def __init__(self, manager: UIManager, rect: pygame.Rect):
        super().__init__(rect, manager, window_display_title='設定', object_id='#settings_dialog')

        # --- ダイアログ内の要素 ---
        container_width = self.get_container().get_size()[0] - 40 # コンテナ左右マージン考慮
        current_y = 10

        # 1. 日本語ラベル
        self.info_label = UILabel(
            relative_rect=pygame.Rect((10, current_y), (container_width, 30)),
            text='オプションを選択してください:',
            manager=manager,
            container=self, # このウィンドウをコンテナにする
            object_id='@dialog_label' # テーマでスタイル指定可能
        )
        current_y += 40

        # 2. テキスト入力
        self.text_entry_label = UILabel(
            relative_rect=pygame.Rect((10, current_y), (80, 30)),
            text='名前:',
            manager=manager,
            container=self
        )
        self.text_entry = UITextEntryLine(
            relative_rect=pygame.Rect((100, current_y), (container_width - 90, 30)), # ラベル分引く
            manager=manager,
            container=self
        )
        self.text_entry.set_text('デフォルト値')
        current_y += 40

        # 3. ラジオボタン (UIPanel内に配置)
        self.radio_label = UILabel(
            relative_rect=pygame.Rect((10, current_y), (container_width, 30)),
            text='選択肢:',
            manager=manager,
            container=self
        )
        current_y += 30

        # ラジオボタン用のパネル
        radio_panel_height = 50 # ラジオボタンの高さに応じて調整
        self.radio_panel = UIPanel(
             relative_rect=pygame.Rect((10, current_y), (container_width, radio_panel_height)),
             starting_height=1,
             manager=manager,
             container=self
        )
        current_y += radio_panel_height + 10

        # ラジオボタン本体 (UIButtonを使用)
        self.radio_buttons = []
        self.selected_option = None # 選択されているオプションを保持
        options = ["オプション A", "オプション B", "オプション C"]
        radio_button_width = 110
        radio_button_height = 30
        radio_start_x = 10 # パネル内のX座標
        radio_start_y = (radio_panel_height - radio_button_height) // 2 # パネル内で垂直中央揃え

        for i, option_text in enumerate(options):
            button = UIButton(
                relative_rect=pygame.Rect(
                    (radio_start_x + i * (radio_button_width + 5), radio_start_y), # ボタン間隔調整
                    (radio_button_width, radio_button_height)
                ),
                text=option_text,
                manager=manager,
                container=self.radio_panel, # コンテナをパネルにする
                object_id='#radio_button' # 共通のID
            )
            self.radio_buttons.append(button)
            # 最初のボタンをデフォルトで選択状態にする (例)
            if i == 0:
                 button.select()
                 self.selected_option = option_text

        # 4. OK / Cancel ボタン (ダイアログ下部に配置)
        button_width = 100
        button_height = 40
        margin = 10
        # ダイアログのクライアント領域の高さを取得してY座標を計算
        client_rect = self.get_container().get_rect()
        button_y = client_rect.height - button_height - margin

        ok_button_x = client_rect.width - (button_width * 2 + margin * 3)
        cancel_button_x = client_rect.width - (button_width + margin * 2)

        self.ok_button = UIButton(
            relative_rect=pygame.Rect((ok_button_x, button_y), (button_width, button_height)),
            text='OK',
            manager=manager,
            container=self,
            object_id='#ok_button'
        )
        self.cancel_button = UIButton(
            relative_rect=pygame.Rect((cancel_button_x, button_y), (button_width, button_height)),
            text='キャンセル',
            manager=manager,
            container=self,
            object_id='#cancel_button'
        )

    def process_event(self, event: pygame.event.Event) -> bool:
        # 親クラスのイベント処理を呼び出す (ウィンドウ移動や閉じるボタンなど)
        consumed = super().process_event(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            # ラジオボタンの処理
            if event.ui_element in self.radio_buttons:
                # クリックされたボタンを選択状態にし、他を解除
                for button in self.radio_buttons:
                    if button == event.ui_element:
                        button.select()
                        self.selected_option = button.text # 選択されたテキストを保持
                        print(f"ラジオボタン選択: {self.selected_option}")
                    else:
                        button.unselect()
                consumed = True # イベントを消費した

            # OKボタンの処理
            elif event.ui_element == self.ok_button:
                print("OK ボタンが押されました。")
                print(f"  名前: {self.text_entry.get_text()}")
                print(f"  選択: {self.selected_option}")
                self.kill() # ウィンドウを閉じる
                consumed = True

            # キャンセルボタンの処理
            elif event.ui_element == self.cancel_button:
                print("キャンセル ボタンが押されました。")
                self.kill() # ウィンドウを閉じる
                consumed = True

        return consumed

    # kill() メソッドは親クラスにあるのでオーバーライド不要 (必要なら追加処理)


# --- メイン処理 ---
def main():
    # 1. Pygame 初期化
    pygame.init()
    pygame.display.set_caption('モーダルダイアログ サンプル')
    window_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    background = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    background.fill(pygame.Color('#DDDDDD')) # 背景色を少し明るく

    # 2. UIManager の生成（日本語ロケール設定）
    manager = UIManager((WINDOW_WIDTH, WINDOW_HEIGHT), starting_language='ja')

    # 3. カスタム日本語フォントの追加とプリロード
    font_path = resource_path(os.path.join('fonts', 'NotoSansJP-Regular.ttf'))
    if not os.path.isfile(font_path):
        print(f"警告: フォントファイルが見つかりません: {font_path}")
    else:
        manager.add_font_paths('noto_sans_jp', regular_path=font_path)
        manager.preload_fonts([
            {'name': 'noto_sans_jp', 'point_size': 14, 'style': 'regular'}, # ダイアログ内要素用
            {'name': 'noto_sans_jp', 'point_size': 18, 'style': 'regular'}  # メインボタン用
        ])
        print(f"フォント '{os.path.basename(font_path)}' をロードしました。")


    # 4. メインウィンドウの UI 要素
    settings_button = UIButton(
        relative_rect=pygame.Rect(((WINDOW_WIDTH - 150) // 2, (WINDOW_HEIGHT - 50) // 2), (150, 50)), # ボタンサイズ調整
        text='設定', # ボタンテキスト変更
        manager=manager,
        object_id='#settings_button'
    )

    # 5. メインループ
    clock = pygame.time.Clock()
    is_running = True
    active_dialog: SettingsDialog | None = None # 型ヒントを追加

    while is_running:
        time_delta = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False

            # UIManager にイベントを渡す (ダイアログ内の要素もここで処理される)
            manager.process_events(event)

            # --- ボタンクリック処理 ---
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                # 設定ボタンが押された場合 (かつ、ダイアログが開いていない場合)
                if event.ui_element == settings_button and active_dialog is None:
                    print("設定ボタンが押されました。ダイアログを開きます。")
                    # ダイアログの位置とサイズを計算
                    dialog_rect = pygame.Rect(
                        ((WINDOW_WIDTH - DIALOG_WIDTH) // 2, (WINDOW_HEIGHT - DIALOG_HEIGHT) // 2),
                        (DIALOG_WIDTH, DIALOG_HEIGHT)
                    )
                    active_dialog = SettingsDialog(manager, dialog_rect)
                    # モーダル化: メインボタンを無効化
                    settings_button.disable()

            # --- ダイアログクローズ処理 ---
            if event.type == pygame_gui.UI_WINDOW_CLOSE:
                 # 閉じたウィンドウがアクティブなダイアログか確認
                if active_dialog is not None and event.ui_element == active_dialog:
                    print("設定ダイアログが閉じられました。")
                    active_dialog = None # アクティブなダイアログ参照をクリア
                    # モーダル化: メインボタンを有効化
                    settings_button.enable()


        # --- 更新 ---
        manager.update(time_delta)

        # --- 描画 ---
        window_surface.blit(background, (0, 0))
        manager.draw_ui(window_surface)
        pygame.display.update()

    pygame.quit()

if __name__ == '__main__':
    main()

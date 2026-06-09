import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UILabel, UITextEntryLine
from pygame_gui import UIManager

# 1. Pygame 初期化
pygame.init()
pygame.display.set_caption('日本語UIサンプル')
window_surface = pygame.display.set_mode((400, 300))  # ウィンドウサイズ
background = pygame.Surface((400, 300))
background.fill(pygame.Color('#FFFFFF'))

# 2. UIManager の生成（日本語ロケール設定）
manager = UIManager((400, 300), starting_language='ja')

# 3. カスタム日本語フォントの追加とプリロード
manager.add_font_paths('noto_sans_jp', 'fonts/NotoSansJP-Regular.otf')  # フォント登録 turn3search0
manager.preload_fonts([
    {'name': 'noto_sans_jp', 'point_size': 20, 'style': 'regular'}
])  # フォントプリロード turn3search1

# 4. UI 要素の作成
hello_button = UIButton(
    relative_rect=pygame.Rect((100, 50), (200, 50)),
    text='こんにちは',  # ボタンラベルを日本語で設定 turn1search0
    manager=manager
)
label = UILabel(
    relative_rect=pygame.Rect((100, 120), (200, 30)),
    text='ラベル表示',  # ラベル表示を日本語で設定 turn4search2
    manager=manager
)
text_entry = UITextEntryLine(
    relative_rect=pygame.Rect((100, 160), (200, 30)),
    manager=manager
)
text_entry.set_text('テキスト入力')  # 初期入力文字列に日本語を設定 turn4search14

# 5. メインループ
clock = pygame.time.Clock()
is_running = True
while is_running:
    time_delta = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False

        # ボタン押下イベントの検出
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == hello_button:
                print('ボタンが押されました！')  # コンソール出力
        manager.process_events(event)

    manager.update(time_delta)
    window_surface.blit(background, (0, 0))
    manager.draw_ui(window_surface)
    pygame.display.update()

pygame.quit()

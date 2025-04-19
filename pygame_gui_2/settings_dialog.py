# settings_dialog.py
import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UILabel, UITextEntryLine, UIWindow, UIPanel
from pygame_gui import UIManager

class SettingsDialog(UIWindow):
    """
    設定ダイアログを表示するためのカスタムウィンドウクラス。
    pygame_gui の UIWindow を継承して作成します。
    """
    def __init__(self, manager: UIManager, rect: pygame.Rect):
        """
        ダイアログの初期化処理。
        manager: UIManager のインスタンス
        rect: ダイアログを表示する位置とサイズ (pygame.Rect オブジェクト)
        """
        super().__init__(rect, manager,
                         window_display_title='設定',
                         object_id='#settings_dialog')

        # --- ダイアログ内の UI 要素を作成・配置 ---
        container_width = self.get_container().get_size()[0] - 40
        current_y = 10

        # 1. 情報ラベル (UILabel)
        self.info_label = UILabel(
            relative_rect=pygame.Rect((10, current_y), (container_width, 30)),
            text='オプションを選択してください:',
            manager=manager,
            container=self,
            object_id='@dialog_label'
        )
        current_y += 40

        # 2. テキスト入力欄 (UITextEntryLine) とそのラベル (UILabel)
        self.text_entry_label = UILabel(
            relative_rect=pygame.Rect((10, current_y), (80, 30)),
            text='名前:',
            manager=manager,
            container=self
        )
        self.text_entry = UITextEntryLine(
            relative_rect=pygame.Rect((100, current_y), (container_width - 90, 30)),
            manager=manager,
            container=self
        )
        self.text_entry.set_text('デフォルト値')
        current_y += 40

        # 3. ラジオボタン風の選択肢 (UIButton を UIPanel 内に配置)
        self.radio_label = UILabel(
            relative_rect=pygame.Rect((10, current_y), (container_width, 30)),
            text='選択肢:',
            manager=manager,
            container=self
        )
        current_y += 30

        radio_panel_height = 50
        self.radio_panel = UIPanel(
             relative_rect=pygame.Rect((10, current_y), (container_width, radio_panel_height)),
             starting_height=1,
             manager=manager,
             container=self
        )
        current_y += radio_panel_height + 10

        self.radio_buttons = []
        self.selected_option = None
        options = ["オプション A", "オプション B", "オプション C"]
        radio_button_width = 110
        radio_button_height = 30
        radio_start_x = 10
        radio_start_y = (radio_panel_height - radio_button_height) // 2

        for i, option_text in enumerate(options):
            button = UIButton(
                relative_rect=pygame.Rect(
                    (radio_start_x + i * (radio_button_width + 5), radio_start_y),
                    (radio_button_width, radio_button_height)
                ),
                text=option_text,
                manager=manager,
                container=self.radio_panel,
                object_id='#radio_button'
            )
            self.radio_buttons.append(button)
            if i == 0:
                 button.select()
                 self.selected_option = option_text

        # 4. OK / キャンセルボタン (UIButton) をダイアログ下部に配置
        button_width = 100
        button_height = 40
        margin = 10
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
        """
        ダイアログ内のイベントを処理するメソッド。
        """
        consumed = super().process_event(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element in self.radio_buttons:
                for button in self.radio_buttons:
                    if button == event.ui_element:
                        button.select()
                        self.selected_option = button.text
                        print(f"ラジオボタン選択: {self.selected_option}")
                    else:
                        button.unselect()
                consumed = True

            elif event.ui_element == self.ok_button:
                print("OK ボタンが押されました。")
                print(f"  名前: {self.text_entry.get_text()}")
                print(f"  選択: {self.selected_option}")
                self.kill()
                consumed = True

            elif event.ui_element == self.cancel_button:
                print("キャンセル ボタンが押されました。")
                self.kill()
                consumed = True

        return consumed

    # kill() メソッドは親クラス UIWindow に実装されているため、
    # ここで特にオーバーライドする必要はありません。

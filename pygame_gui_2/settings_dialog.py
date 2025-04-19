# settings_dialog.py
import pygame
import pygame_gui
import i18n
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
        # ★★★ 国際化対応: window_display_title に翻訳キーを指定 ★★★
        super().__init__(rect, manager,
                         window_display_title='#settings.title', # '#' プレフィックスで翻訳キーを指定
                         object_id='#settings_dialog')

        # --- ダイアログ内の UI 要素を作成・配置 ---
        container_width = self.get_container().get_size()[0] - 40
        current_y = 10

        # 1. 情報ラベル (UILabel)
        # ★★★ 国際化対応: text に翻訳キーを指定 ★★★
        self.info_label = UILabel(
            relative_rect=pygame.Rect((10, current_y), (container_width, 30)),
            text=i18n.t('settings.info_label'), # '#' プレフィックスで翻訳キーを指定
            manager=manager,
            container=self,
            object_id='@dialog_label'
        )
        current_y += 40

        # 2. テキスト入力欄 (UITextEntryLine) とそのラベル (UILabel)
        # ★★★ 国際化対応: text に翻訳キーを指定 ★★★
        self.text_entry_label = UILabel(
            relative_rect=pygame.Rect((10, current_y), (80, 30)),
            text=i18n.t('settings.name_label'), # '#' プレフィックスで翻訳キーを指定
            manager=manager,
            container=self
        )
        self.text_entry = UITextEntryLine(
            relative_rect=pygame.Rect((100, current_y), (container_width - 90, 30)),
            manager=manager,
            container=self
        )
        # TODO: デフォルト値も必要に応じて国際化対応を検討
        #       例: manager.get_translation('#settings.default_name') を使うなど
        self.text_entry.set_text('デフォルト値')
        current_y += 40

        # 3. ラジオボタン風の選択肢 (UIButton を UIPanel 内に配置)
        # ★★★ 国際化対応: text に翻訳キーを指定 ★★★
        self.radio_label = UILabel(
            relative_rect=pygame.Rect((10, current_y), (container_width, 30)),
            text=i18n.t('settings.options_label'), # '#' プレフィックスで翻訳キーを指定
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
        self.selected_option_key = None # 選択されたオプションのキーを保持
        # ★★★ 国際化対応: options リストに翻訳キーを使用 ★★★
        options = ["#settings.option_a", "#settings.option_b", "#settings.option_c"]
        # 注意: 翻訳後の文字列長に合わせて幅の調整が必要になる場合があります
        radio_button_width = 110
        radio_button_height = 30
        radio_start_x = 10
        radio_start_y = (radio_panel_height - radio_button_height) // 2

        for i, option_key in enumerate(options):
            button = UIButton(
                relative_rect=pygame.Rect(
                    (radio_start_x + i * (radio_button_width + 5), radio_start_y),
                    (radio_button_width, radio_button_height)
                ),
                text=i18n.t(option_key.lstrip('#')), # '#' プレフィックスで翻訳キーを指定
                manager=manager,
                container=self.radio_panel,
                object_id='#radio_button'
            )
            # ★★★ 内部でキーを保持するように変更 ★★★
            # どのボタンがどのキーに対応するかを user_data に保存
            button.user_data = {'translation_key': option_key}
            self.radio_buttons.append(button)
            if i == 0:
                 button.select()
                 self.selected_option_key = option_key # 初期選択のキーを保持

        # 4. OK / キャンセルボタン (UIButton) をダイアログ下部に配置
        button_width = 100
        button_height = 40
        margin = 10
        client_rect = self.get_container().get_rect()
        button_y = client_rect.height - button_height - margin

        ok_button_x = client_rect.width - (button_width * 2 + margin * 3)
        cancel_button_x = client_rect.width - (button_width + margin * 2)

        # ★★★ 国際化対応: text に翻訳キーを指定 ★★★
        self.ok_button = UIButton(
            relative_rect=pygame.Rect((ok_button_x, button_y), (button_width, button_height)),
            text=i18n.t('settings.ok_button'), # '#' プレフィックスで翻訳キーを指定
            manager=manager,
            container=self,
            object_id='#ok_button'
        )
        # ★★★ 国際化対応: text に翻訳キーを指定 ★★★
        self.cancel_button = UIButton(
            relative_rect=pygame.Rect((cancel_button_x, button_y), (button_width, button_height)),
            text=i18n.t('settings.cancel_button'), # '#' プレフィックスで翻訳キーを指定
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
                        # ★★★ 選択されたキーを更新 ★★★
                        self.selected_option_key = button.user_data['translation_key']
                        # デバッグ出力は翻訳前のキーを表示
                        print(f"ラジオボタン選択 (キー): {self.selected_option_key}")
                        # 必要なら翻訳後のテキストも取得可能:
                        # print(f"ラジオボタン選択 (表示テキスト): {button.text}")
                    else:
                        button.unselect()
                consumed = True

            elif event.ui_element == self.ok_button:
                print("OK ボタンが押されました。")
                print(f"  名前: {self.text_entry.get_text()}")
                # ★★★ 選択されたキーを表示 ★★★
                print(f"  選択 (キー): {self.selected_option_key}")
                # 必要であれば、選択されたキーに対応する翻訳済みテキストを取得:
                # selected_text = self.ui_manager.get_translation(self.selected_option_key)
                # print(f"  選択 (表示テキスト): {selected_text}")
                self.kill() # ダイアログを閉じる
                consumed = True

            elif event.ui_element == self.cancel_button:
                print("キャンセル ボタンが押されました。")
                self.kill() # ダイアログを閉じる
                consumed = True

        return consumed

    # kill() メソッドは親クラス UIWindow に実装されているため、
    # ここで特にオーバーライドする必要はありません。

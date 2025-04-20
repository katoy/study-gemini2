# settings_dialog.py
import pygame
import pygame_gui
import i18n
from pygame_gui.elements import UIButton, UILabel, UITextEntryLine, UIWindow, UIPanel
from pygame_gui import UIManager
from config import LayoutConfig

class SettingsDialog(UIWindow):
    """
    設定ダイアログをモーダル表示するためのカスタムウィンドウクラス。
    pygame_gui の UIWindow を継承し、ダイアログ表示中は背後の UI 操作をブロックします。
    """
    # --- レイアウト定数 (config に移動したため削除) ---

    def __init__(self, manager: UIManager, rect: pygame.Rect, config: LayoutConfig):
        # UIWindow を通常通り初期化
        super().__init__(
            rect=rect,
            manager=manager,
            window_display_title=i18n.t('settings.title'),
            object_id='settings_dialog'
        )
        # このウィンドウが開いている間、他の UI 要素へのクリックをブロック
        # （True にするとウィンドウを前面に上げつつ、背後の要素をクリック不可にする）
        self.set_blocking(True)  # :contentReference[oaicite:0]{index=0}

        self.config = config

        # (container_width, current_y の計算は変更なし)
        self.container_width = self.get_container().get_size()[0] - self.config.MARGIN * 2
        self.current_y = self.config.MARGIN

        # (UI要素作成呼び出しは変更なし)
        self._create_info_label()
        self._create_name_entry()
        self._create_options_panel()
        self._create_action_buttons()

        # (初期選択部分は変更なし)
        if self.radio_buttons:
            btn = self.radio_buttons[0]
            btn.select()
            self.selected_option_key = btn.user_data['translation_key']
        else:
            self.selected_option_key = None

    def kill(self):
        # (変更なし)
        super().kill()

    def _create_info_label(self):
        self.info_label = UILabel(
                # ↓↓↓ relative_rect の指定を修正 ↓↓↓
                relative_rect=pygame.Rect(
                    (self.config.MARGIN, self.current_y),
                    (self.container_width, self.config.DIALOG_LABEL_HEIGHT)
                ),
            text=i18n.t('settings.info_label'),
            manager=self.ui_manager,
            container=self,
            object_id='@dialog_label'
        )
        self.current_y += self.config.DIALOG_LABEL_HEIGHT + self.config.MARGIN

    def _create_name_entry(self):
        # (変更なし)
        label_w = 80
        entry_x = self.config.MARGIN + label_w + self.config.MARGIN
        entry_w = self.container_width - label_w - self.config.MARGIN
        self.text_entry_label = UILabel(
            relative_rect=pygame.Rect(
                (self.config.MARGIN, self.current_y),
                (label_w, self.config.DIALOG_ENTRY_HEIGHT)
            ),
            text=i18n.t('settings.name_label'),
            manager=self.ui_manager,
            container=self
        )
        self.text_entry = UITextEntryLine(
            relative_rect=pygame.Rect(
                (entry_x, self.current_y),
                (entry_w, self.config.DIALOG_ENTRY_HEIGHT)
            ),
            manager=self.ui_manager,
            container=self
        )
        self.text_entry.set_text('')
        self.current_y += self.config.DIALOG_ENTRY_HEIGHT + self.config.MARGIN

    def _create_options_panel(self):
        # (radio_label, radio_panel 作成部分は変更なし)
        self.radio_label = UILabel(
            relative_rect=pygame.Rect(
                (self.config.MARGIN, self.current_y),
                (self.container_width, self.config.DIALOG_LABEL_HEIGHT)
            ),
            text=i18n.t('settings.options_label'),
            manager=self.ui_manager,
            container=self
        )
        self.current_y += self.config.DIALOG_LABEL_HEIGHT

        self.radio_panel = UIPanel(
            relative_rect=pygame.Rect(
                (self.config.MARGIN, self.current_y),
                (self.container_width, self.config.DIALOG_RADIO_PANEL_HEIGHT)
            ),
            starting_height=1,
            manager=self.ui_manager,
            container=self
        )
        self.current_y += self.config.DIALOG_RADIO_PANEL_HEIGHT + self.config.MARGIN

        self.radio_buttons = []
        options = [
            ('#settings.option_a', i18n.t('settings.option_a')),
            ('#settings.option_b', i18n.t('settings.option_b')),
            ('#settings.option_c', i18n.t('settings.option_c'))
        ]
        spacing = 5
        start_x = self.config.MARGIN
        y = (self.config.DIALOG_RADIO_PANEL_HEIGHT - self.config.DIALOG_RADIO_BUTTON_HEIGHT) // 2
        for idx, (key, label) in enumerate(options):
            # ↓↓↓ pygame.Rect の引数の括弧を修正 ↓↓↓
            btn = UIButton(
                relative_rect=pygame.Rect(
                    (start_x + idx * (self.config.DIALOG_RADIO_BUTTON_WIDTH + spacing), y), # (left, top) タプル
                    (self.config.DIALOG_RADIO_BUTTON_WIDTH, self.config.DIALOG_RADIO_BUTTON_HEIGHT) # (width, height) タプル
                ), # pygame.Rect の正しい閉じ括弧
                # ↑↑↑ ----------------------------- ↑↑↑
                text=label,
                manager=self.ui_manager,
                container=self.radio_panel,
                object_id='#radio_button'
            )
            btn.user_data = {'translation_key': key}
            self.radio_buttons.append(btn)

    def _create_action_buttons(self):
        # (変更なし)
        c_rect = self.get_container().get_rect()
        y = c_rect.height - self.config.DIALOG_ACTION_BUTTON_HEIGHT - self.config.MARGIN
        cancel_x = c_rect.width - self.config.DIALOG_ACTION_BUTTON_WIDTH - self.config.MARGIN
        ok_x = cancel_x - self.config.DIALOG_ACTION_BUTTON_WIDTH - self.config.MARGIN

        self.ok_button = UIButton(
            relative_rect=pygame.Rect((ok_x, y),
                                      (self.config.DIALOG_ACTION_BUTTON_WIDTH, self.config.DIALOG_ACTION_BUTTON_HEIGHT)),
            text=i18n.t('settings.ok_button'),
            manager=self.ui_manager,
            container=self,
            object_id='#ok_button'
        )
        self.cancel_button = UIButton(
            relative_rect=pygame.Rect((cancel_x, y),
                                      (self.config.DIALOG_ACTION_BUTTON_WIDTH, self.config.DIALOG_ACTION_BUTTON_HEIGHT)),
            text=i18n.t('settings.cancel_button'),
            manager=self.ui_manager,
            container=self,
            object_id='#cancel_button'
        )

    def process_event(self, event: pygame.event.Event) -> bool:
        # (変更なし)
        consumed = super().process_event(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element in self.radio_buttons:
                for btn in self.radio_buttons:
                    if btn == event.ui_element:
                        btn.select()
                        self.selected_option_key = btn.user_data['translation_key']
                    else:
                        btn.unselect()
                return True
            if event.ui_element == self.ok_button or event.ui_element == self.cancel_button:
                self.kill()
                return True
        return consumed

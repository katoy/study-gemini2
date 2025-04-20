# settings_dialog.py
import pygame # pygame イベントのためにインポート
import pygame_gui
import i18n
from pygame_gui.elements import UIButton, UILabel, UITextEntryLine, UIWindow, UIPanel
from pygame_gui import UIManager
from config import LayoutConfig

# カスタムイベントタイプを定義 (他の USEREVENT と衝突しないように番号を選ぶ)
SETTINGS_UPDATED = pygame.USEREVENT + 10

class SettingsDialog(UIWindow):
    """
    設定ダイアログをモーダル表示するためのカスタムウィンドウクラス。
    pygame_gui の UIWindow を継承し、ダイアログ表示中は背後の UI 操作をブロックします。
    初期値を設定し、OK時に設定内容をイベントで通知します。
    """
    # --- レイアウト定数 (config に移動したため削除) ---

    def __init__(self,
                 manager: UIManager,
                 rect: pygame.Rect,
                 config: LayoutConfig,
                 initial_user_name: str,           # 初期ユーザー名を追加
                 initial_selected_option_key: str  # 初期選択オプションキーを追加
                 ):
        # UIWindow を通常通り初期化
        super().__init__(
            rect=rect,
            manager=manager,
            window_display_title=i18n.t('settings.title'),
            object_id='settings_dialog'
        )
        # このウィンドウが開いている間、他の UI 要素へのクリックをブロック
        self.set_blocking(True)

        self.config = config
        self.initial_user_name = initial_user_name
        self.initial_selected_option_key = initial_selected_option_key

        # コンテナ幅と初期Y座標の計算
        self.container_width = self.get_container().get_size()[0] - self.config.MARGIN * 2
        self.current_y = self.config.MARGIN

        # UI要素作成呼び出し
        self._create_info_label()
        self._create_name_entry() # この中で初期ユーザー名を設定
        self._create_options_panel() # この中で初期選択オプションを設定
        self._create_action_buttons()

        # # --- 初期選択処理を _create_options_panel 内に移動 ---
        # # ラジオボタン作成後に初期選択を行う必要があるため、
        # # _create_options_panel の最後で実行するように変更します。
        # if self.radio_buttons:
        #     # 初期選択キーに合致するボタンを探す
        #     initial_button_found = False
        #     for btn in self.radio_buttons:
        #         if btn.user_data['translation_key'] == self.initial_selected_option_key:
        #             btn.select()
        #             self.selected_option_key = btn.user_data['translation_key']
        #             initial_button_found = True
        #             break
        #     # 合致するものがなければ最初のボタンを選択
        #     if not initial_button_found:
        #         btn = self.radio_buttons[0]
        #         btn.select()
        #         self.selected_option_key = btn.user_data['translation_key']
        # else:
        #     self.selected_option_key = None

    def kill(self):
        # (変更なし)
        super().kill()

    def _create_info_label(self):
        # (変更なし)
        self.info_label = UILabel(
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
        # (変更なし - ただし初期値設定を追加)
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
        # --- 初期ユーザー名を設定 ---
        self.text_entry.set_text(self.initial_user_name)
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
            btn = UIButton(
                relative_rect=pygame.Rect(
                    (start_x + idx * (self.config.DIALOG_RADIO_BUTTON_WIDTH + spacing), y),
                    (self.config.DIALOG_RADIO_BUTTON_WIDTH, self.config.DIALOG_RADIO_BUTTON_HEIGHT)
                ),
                text=label,
                manager=self.ui_manager,
                container=self.radio_panel,
                object_id='#radio_button'
            )
            btn.user_data = {'translation_key': key}
            self.radio_buttons.append(btn)

        # --- ラジオボタン作成後に初期選択を行う ---
        initial_button_found = False
        if self.radio_buttons:
            for btn in self.radio_buttons:
                if btn.user_data['translation_key'] == self.initial_selected_option_key:
                    btn.select() # select() メソッドで選択状態にする
                    self.selected_option_key = btn.user_data['translation_key']
                    initial_button_found = True
                    # 他のボタンは非選択状態にする (念のため)
                    for other_btn in self.radio_buttons:
                        if other_btn != btn:
                            other_btn.unselect()
                    break # 一致するものが見つかったらループを抜ける

            # 初期選択キーに合致するボタンがなかった場合、最初のボタンを選択状態にする
            if not initial_button_found:
                first_btn = self.radio_buttons[0]
                first_btn.select()
                self.selected_option_key = first_btn.user_data['translation_key']
                # 他のボタンを非選択状態にする
                for other_btn in self.radio_buttons[1:]:
                    other_btn.unselect()
        else:
            self.selected_option_key = None # ラジオボタンがない場合は None

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
        # スーパークラスのイベント処理を先に呼び出す
        consumed = super().process_event(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            # ラジオボタン (UIButton) が押された場合
            if event.ui_element in self.radio_buttons:
                for btn in self.radio_buttons:
                    if btn == event.ui_element:
                        btn.select() # 押されたボタンを選択状態に
                        self.selected_option_key = btn.user_data['translation_key'] # 選択キーを更新
                    else:
                        btn.unselect() # 他のボタンは非選択状態に
                consumed = True # イベントを消費

            # OKボタンが押された場合
            elif event.ui_element == self.ok_button:
                # 現在の入力値と選択キーを取得
                current_user_name = self.text_entry.get_text()
                current_selected_option_key = self.selected_option_key

                # 設定更新イベントを発行
                pygame.event.post(pygame.event.Event(SETTINGS_UPDATED,
                                                      {'user_name': current_user_name,
                                                       'selected_option_key': current_selected_option_key}))
                self.kill() # ダイアログを閉じる
                consumed = True # イベントを消費

            # キャンセルボタンが押された場合
            elif event.ui_element == self.cancel_button:
                self.kill() # ダイアログを閉じる
                consumed = True # イベントを消費

        return consumed

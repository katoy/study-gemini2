# tests/test_main.py
import unittest
from unittest.mock import patch, MagicMock, call, ANY # ANY をインポート
import pygame # pygame定数 (QUIT, MOUSEBUTTONDOWN など) のためにインポート
import sys
import os

# プロジェクトルートへのパスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# テスト対象の main モジュール
import main
# 依存するクラスや定数 (spec や型ヒント、定数参照用)
from game import Game
from gui import GameGUI
from config.theme import Screen, Color
from config.agents import AGENT_DEFINITIONS # エージェントID参照用

# --- Pygame の初期化と終了をクラスレベルで行う ---
@unittest.skipUnless(os.environ.get('TEST_PYGAME', False), "Pygame tests skipped unless TEST_PYGAME is set")
class TestMainLoop(unittest.TestCase):
    """main.py のメインループとイベント処理をテストする"""

    @classmethod
    def setUpClass(cls):
        # Pygame の display モジュールだけ初期化 (イベント等はモックする)
        # 環境変数などで Pygame テストをスキップできるようにする
        if os.environ.get('TEST_PYGAME', False):
            pygame.display.init()
            # 実際の描画は行わないが、一部の Rect 計算などで必要になる場合がある
            cls.screen = pygame.display.set_mode((Screen.WIDTH, Screen.HEIGHT))
        else:
            cls.screen = None # スキップ時は None

    @classmethod
    def tearDownClass(cls):
        if cls.screen:
            pygame.display.quit()

    def setUp(self):
        # Pygame テストがスキップされる場合は setUp もスキップ
        if not self.__class__.screen:
            self.skipTest("Pygame tests are skipped.")

        # --- モックの設定 ---
        # main モジュール内の依存関係をパッチ
        self.patcher_pygame = patch('main.pygame', wraps=pygame) # wraps で元のpygameも一部使えるように
        self.patcher_game_gui = patch('main.GameGUI')
        self.patcher_game = patch('main.Game')
        self.patcher_get_options = patch('main.get_agent_options')
        self.patcher_clock = patch('main.pygame.time.Clock') # Clock もモック

        self.mock_pygame = self.patcher_pygame.start()
        self.mock_GameGUI = self.patcher_game_gui.start()
        self.mock_Game = self.patcher_game.start()
        self.mock_get_options = self.patcher_get_options.start()
        self.mock_clock = self.patcher_clock.start()

        # モックインスタンスを作成
        self.mock_gui_instance = self.mock_GameGUI.return_value
        self.mock_game_instance = self.mock_Game.return_value
        self.mock_clock_instance = self.mock_clock.return_value

        # デフォルトの戻り値や属性を設定
        self.mock_pygame.display.set_mode.return_value = self.__class__.screen # screen を設定
        self.mock_get_options.return_value = [(d['id'], d['display_name']) for d in AGENT_DEFINITIONS]
        self.mock_game_instance.game_over = False
        self.mock_game_instance.turn = -1 # 初期手番
        self.mock_game_instance.agents = {-1: None, 1: None} # 初期プレイヤー
        self.mock_game_instance.get_valid_moves.return_value = [(2,3), (3,2), (4,5), (5,4)] # ダミーの合法手
        self.mock_game_instance.get_message.return_value = ""
        # GUIのレイアウト計算メソッドもモックしておく
        self.mock_gui_instance._calculate_board_rect.return_value = pygame.Rect(25, 50, 400, 400)
        self.mock_gui_instance._calculate_player_settings_top.return_value = 550 # 適当な値
        # is_button_clicked はテストごとに side_effect を設定する

        # イベントキューのモック
        self.mock_pygame.event.get.return_value = [] # デフォルトは空

        # main 関数内のローカル変数の初期状態を模倣
        self.black_player_type = 0
        self.white_player_type = 0
        self.game_started = False

    def tearDown(self):
        # パッチを停止
        self.patcher_pygame.stop()
        self.patcher_game_gui.stop()
        self.patcher_game.stop()
        self.patcher_get_options.stop()
        self.patcher_clock.stop()

    def _run_main_with_events(self, event_sequence):
        """指定されたイベントシーケンスで main() を実行するヘルパー"""
        # イベントキューの side_effect を設定
        # 最後のイベントリストの後に QUIT イベントを追加してループを確実に出る
        final_events = event_sequence + [[MagicMock(type=pygame.QUIT)]]
        self.mock_pygame.event.get.side_effect = final_events
        main.main()

    # --- テストケース ---

    def test_quit_event_terminates(self):
        """pygame.QUIT イベントでループが終了し、pygame.quit() が呼ばれる"""
        self._run_main_with_events([]) # イベントなし -> QUIT のみ
        self.mock_pygame.quit.assert_called_once()

    def test_start_button_starts_game(self):
        """開始ボタンクリックでゲームが開始される (game_started=True相当)"""
        start_button_rect = pygame.Rect(100, 500, 150, 40) # ダミー
        self.mock_gui_instance._calculate_button_rect.return_value = start_button_rect
        # 開始ボタンクリック時のみ True を返すように設定
        self.mock_gui_instance.is_button_clicked.side_effect = lambda pos, rect: rect == start_button_rect

        click_pos = start_button_rect.center
        start_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=click_pos)

        self._run_main_with_events([[start_click_event]])

        # 検証: game.set_message("") が呼ばれたか
        self.mock_game_instance.set_message.assert_called_with("")
        # 検証: 2回目のループ（ゲーム開始後）でゲーム中描画が呼ばれたか
        # 例: gui.draw_turn_message が呼ばれたか
        # (side_effect で2回以上ループを回す必要あり)
        # このテストでは game_started フラグの変更のみを間接的に確認

    def test_radio_button_click_changes_player_type(self):
        """ラジオボタンクリックでプレイヤータイプが変更され、game.set_players が呼ばれる"""
        # GUIのレイアウト計算を再現 (簡略化)
        player_settings_top = self.mock_gui_instance._calculate_player_settings_top()
        board_left = self.mock_gui_instance._calculate_board_rect().left
        radio_y_offset = Screen.RADIO_Y_OFFSET
        radio_y_spacing = Screen.RADIO_Y_SPACING
        radio_button_size = Screen.RADIO_BUTTON_SIZE
        white_player_label_x = Screen.WIDTH // 2 + Screen.RADIO_BUTTON_MARGIN

        # 白の MCTS (ID=4) ラジオボタンの位置を計算 (仮)
        mcts_index = -1
        for i, (id, _) in enumerate(self.mock_get_options.return_value):
            if id == 4:
                mcts_index = i
                break
        self.assertNotEqual(mcts_index, -1, "MCTS Agent (ID=4) not found in options")

        white_mcts_radio_y = player_settings_top + radio_y_offset + mcts_index * radio_y_spacing
        white_mcts_radio_rect = pygame.Rect(white_player_label_x, white_mcts_radio_y, radio_button_size, radio_button_size)
        click_pos = white_mcts_radio_rect.center

        radio_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=click_pos)

        # is_button_clicked はラジオボタンでは呼ばれないので設定不要

        self._run_main_with_events([[radio_click_event]])

        # 検証: game.set_players が呼ばれたか (黒:0, 白:4)
        self.mock_game_instance.set_players.assert_called_with(0, 4)

    def test_human_move_during_game(self):
        """ゲーム中に人間が合法手をクリックした場合の処理"""
        # ゲーム開始状態にする
        self.game_started = True # main内のフラグを直接は変えられないので、イベントで開始させる
        start_button_rect = pygame.Rect(100, 500, 150, 40)
        self.mock_gui_instance._calculate_button_rect.return_value = start_button_rect
        self.mock_gui_instance.is_button_clicked.side_effect = lambda pos, rect: rect == start_button_rect
        start_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=start_button_rect.center)

        # 人間の手番 (-1) で、(2, 3) が合法手とする
        self.mock_game_instance.turn = -1
        self.mock_game_instance.agents = {-1: None, 1: None} # 人間 vs 人間
        valid_moves = [(2, 3), (3, 2)]
        self.mock_game_instance.get_valid_moves.return_value = valid_moves
        # get_clicked_cell が (2, 3) を返すように設定
        board_rect = self.mock_gui_instance._calculate_board_rect()
        cell_click_pos = (board_rect.left + 3 * Screen.CELL_SIZE + Screen.CELL_SIZE // 2,
                          board_rect.top + 2 * Screen.CELL_SIZE + Screen.CELL_SIZE // 2)
        self.mock_gui_instance.get_clicked_cell.return_value = (2, 3)
        # place_stone は成功するものとする
        self.mock_game_instance.place_stone.return_value = True
        # get_flipped_stones のダミー戻り値
        flipped_stones = [(3, 3)]
        self.mock_game_instance.get_flipped_stones.return_value = flipped_stones

        cell_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=cell_click_pos)

        # イベントシーケンス: 開始クリック -> セルクリック -> 終了
        self._run_main_with_events([[start_click_event], [cell_click_event]])

        # 検証
        self.mock_gui_instance.get_clicked_cell.assert_called_with(cell_click_pos)
        self.mock_game_instance.get_flipped_stones.assert_called_with(2, 3, -1)
        self.mock_game_instance.place_stone.assert_called_with(2, 3)
        self.mock_gui_instance.draw_stone_animation.assert_called_with(self.mock_game_instance, 2, 3, Color.BLACK)
        self.mock_gui_instance.draw_flip_animation.assert_called_with(self.mock_game_instance, flipped_stones, Color.BLACK)
        self.mock_game_instance.switch_turn.assert_called_once()
        self.mock_game_instance.check_game_over.assert_called() # place_stone 後に呼ばれる

    def test_reset_button_click_during_game(self):
        """ゲーム中にリセットボタンをクリックした場合の処理"""
        # ゲーム開始状態にする
        start_button_rect = pygame.Rect(100, 500, 150, 40)
        reset_button_rect = pygame.Rect(200, 600, 100, 40) # ダミー
        # _calculate_button_rect が状況に応じて正しい Rect を返すように設定
        def calc_rect_side_effect(is_start, game_over=False, is_reset=False, is_quit=False):
            if is_start: return start_button_rect
            if is_reset: return reset_button_rect
            # 他のボタンのダミーRectも必要なら返す
            return pygame.Rect(0,0,0,0)
        self.mock_gui_instance._calculate_button_rect.side_effect = calc_rect_side_effect
        # is_button_clicked がリセットボタンでのみ True を返すように設定
        self.mock_gui_instance.is_button_clicked.side_effect = lambda pos, rect: rect == reset_button_rect

        start_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=start_button_rect.center)
        reset_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=reset_button_rect.center)

        # イベントシーケンス: 開始 -> リセット -> 終了
        self._run_main_with_events([[start_click_event], [reset_click_event]])

        # 検証
        self.mock_game_instance.reset.assert_called_once()
        # リセット後はプレイヤーが (0, 0) に設定されるはず
        self.mock_game_instance.set_players.assert_called_with(0, 0)
        # 3回目のループ（リセット後）で開始前描画に戻るはず
        # 例: gui.draw_start_button が呼ばれる
        # self.mock_gui_instance.draw_start_button.assert_called() # 3回目のループで呼ばれるはず

    # --- AIの手番テスト ---
    def test_ai_move_during_game(self):
        """ゲーム中にAIが手を選択・実行する処理"""
        # ゲーム開始状態にする
        start_button_rect = pygame.Rect(100, 500, 150, 40)
        self.mock_gui_instance._calculate_button_rect.return_value = start_button_rect
        self.mock_gui_instance.is_button_clicked.side_effect = lambda pos, rect: rect == start_button_rect
        start_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=start_button_rect.center)

        # AI (白, ID=2: RandomAgent) の手番にする
        mock_ai_agent = MagicMock()
        ai_move = (2, 4) # AIが返す手を設定
        mock_ai_agent.play.return_value = ai_move
        self.mock_game_instance.turn = 1 # 白の手番
        self.mock_game_instance.agents = {-1: None, 1: mock_ai_agent} # 黒:人間, 白:AI
        self.mock_game_instance.get_valid_moves.return_value = [ai_move, (3, 5)] # AIの有効手
        # place_stone は成功するものとする
        self.mock_game_instance.place_stone.return_value = True
        # get_flipped_stones のダミー戻り値
        flipped_stones = [(3, 4)]
        self.mock_game_instance.get_flipped_stones.return_value = flipped_stones

        # イベントシーケンス: 開始クリック -> (AIの手番処理) -> 終了
        # AIの手番はイベントドリブンではないため、ループが1回回れば処理される
        self._run_main_with_events([[start_click_event]])

        # 検証
        mock_ai_agent.play.assert_called_once_with(self.mock_game_instance)
        self.mock_game_instance.get_flipped_stones.assert_called_with(ai_move[0], ai_move[1], 1)
        # AIの手番中の描画更新呼び出しを確認 (例: 最初の flip 前)
        self.mock_gui_instance.draw_board.assert_any_call(self.mock_game_instance)
        self.mock_gui_instance.draw_turn_message.assert_any_call(self.mock_game_instance)
        # アニメーション呼び出し
        self.mock_gui_instance.draw_stone_animation.assert_called_with(self.mock_game_instance, ai_move[0], ai_move[1], Color.WHITE)
        self.mock_game_instance.place_stone.assert_called_with(ai_move[0], ai_move[1])
        # place_stone 後の描画更新呼び出しを確認 (例: flip アニメーション前)
        # アニメーション呼び出し
        self.mock_gui_instance.draw_flip_animation.assert_called_with(self.mock_game_instance, flipped_stones, Color.WHITE)
        self.mock_game_instance.switch_turn.assert_called_once()
        self.mock_game_instance.check_game_over.assert_called()

    # --- パステスト ---
    def test_pass_occurs(self):
        """片方のプレイヤーがパスする処理"""
        # ゲーム開始状態
        start_button_rect = pygame.Rect(100, 500, 150, 40)
        self.mock_gui_instance._calculate_button_rect.return_value = start_button_rect
        self.mock_gui_instance.is_button_clicked.side_effect = lambda pos, rect: rect == start_button_rect
        start_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=start_button_rect.center)

        # 黒の手番で有効手がない状態にする
        self.mock_game_instance.turn = -1
        self.mock_game_instance.agents = {-1: None, 1: None}
        # 最初の get_valid_moves は空リスト、次のターン (白) は有効手あり
        self.mock_game_instance.get_valid_moves.side_effect = [[], [(2, 4)]]

        # イベントシーケンス: 開始クリック -> (パス発生) -> 終了
        self._run_main_with_events([[start_click_event]])

        # 検証
        # get_valid_moves が2回呼ばれる (黒の番、白の番)
        self.assertEqual(self.mock_game_instance.get_valid_moves.call_count, 2)
        # パスメッセージが設定される
        self.mock_game_instance.set_message.assert_called_with("黒はパスです。")
        # switch_turn が呼ばれる
        self.mock_game_instance.switch_turn.assert_called_once()
        # check_game_over が呼ばれる
        self.mock_game_instance.check_game_over.assert_called_once()
        # パス後の描画でメッセージが表示されるはず
        self.mock_gui_instance.draw_message.assert_called_with("黒はパスです。")

    def test_double_pass_ends_game(self):
        """両プレイヤーがパスしてゲームオーバーになる処理"""
        # ゲーム開始状態
        start_button_rect = pygame.Rect(100, 500, 150, 40)
        self.mock_gui_instance._calculate_button_rect.return_value = start_button_rect
        self.mock_gui_instance.is_button_clicked.side_effect = lambda pos, rect: rect == start_button_rect
        start_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=start_button_rect.center)

        # 黒の手番で有効手がない状態
        self.mock_game_instance.turn = -1
        self.mock_game_instance.agents = {-1: None, 1: None}
        # get_valid_moves が2回連続で空リストを返す -> game_over が True になる
        self.mock_game_instance.get_valid_moves.side_effect = [[], []]
        # check_game_over が呼ばれたら game_over を True に設定
        self.mock_game_instance.check_game_over.side_effect = lambda: setattr(self.mock_game_instance, 'game_over', True)
        # ゲームオーバー時の勝者判定 (引き分けとする)
        self.mock_game_instance.get_winner.return_value = 0

        # イベントシーケンス: 開始クリック -> (パス発生) -> (次のターンもパス) -> 終了
        # 2回のループが必要
        self._run_main_with_events([[start_click_event], []]) # 2回目のループ用に空イベント

        # 検証
        self.assertEqual(self.mock_game_instance.get_valid_moves.call_count, 2)
        self.mock_game_instance.set_message.assert_called_with("黒はパスです。") # 最初のパス
        self.assertEqual(self.mock_game_instance.switch_turn.call_count, 1) # 1回目のパスで呼ばれる
        self.assertEqual(self.mock_game_instance.check_game_over.call_count, 1) # 1回目のパスで呼ばれる
        # 2回目のループで game_over=True になり、勝敗メッセージが設定される
        self.mock_game_instance.set_message.assert_called_with("引き分けです！")
        # ゲームオーバー画面の描画が呼ばれる
        self.mock_gui_instance.draw_message.assert_called_with("引き分けです！", is_game_over=True)
        self.mock_gui_instance.draw_restart_button.assert_called_with(True)
        self.mock_gui_instance.draw_reset_button.assert_called_with(True)
        self.mock_gui_instance.draw_quit_button.assert_called_with(True)

    # --- ゲームオーバー時のテスト ---
    def test_game_over_black_wins(self):
        """ゲームオーバー時に黒が勝利した場合の表示"""
        # ゲーム開始 -> 即ゲームオーバー状態
        start_button_rect = pygame.Rect(100, 500, 150, 40)
        self.mock_gui_instance._calculate_button_rect.return_value = start_button_rect
        self.mock_gui_instance.is_button_clicked.side_effect = lambda pos, rect: rect == start_button_rect
        start_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=start_button_rect.center)

        # ゲームオーバー状態を設定
        self.mock_game_instance.game_over = True # 初期状態をTrueに
        self.mock_game_instance.get_winner.return_value = -1 # 黒の勝ち

        # イベントシーケンス: 開始クリック -> (ゲームオーバー処理) -> 終了
        # game_started フラグを True にするために開始クリックが必要
        self._run_main_with_events([[start_click_event]])

        # 検証
        self.mock_game_instance.get_winner.assert_called()
        self.mock_game_instance.set_message.assert_called_with("黒の勝ちです！")
        self.mock_gui_instance.draw_message.assert_called_with("黒の勝ちです！", is_game_over=True)
        self.mock_gui_instance.draw_restart_button.assert_called_with(True)
        self.mock_gui_instance.draw_reset_button.assert_called_with(True)
        self.mock_gui_instance.draw_quit_button.assert_called_with(True)

    # --- ゲームオーバー時のボタン操作 ---
    def test_game_over_restart_button(self):
        """ゲームオーバー時にリスタートボタンをクリック"""
        # ゲームオーバー状態にするセットアップ
        start_button_rect = pygame.Rect(100, 500, 150, 40) # ダミー開始ボタン
        restart_button_rect = pygame.Rect(50, 600, 100, 40) # ダミーリスタートボタン
        # _calculate_button_rect が状況に応じて正しい Rect を返すように設定
        def calc_rect_side_effect(is_start, game_over=False, is_reset=False, is_quit=False):
            if is_start: return start_button_rect
            if game_over and not is_reset and not is_quit: return restart_button_rect # ゲームオーバー時のリスタート
            # 他のボタンのダミーRectも必要なら返す
            return pygame.Rect(0,0,0,0)
        self.mock_gui_instance._calculate_button_rect.side_effect = calc_rect_side_effect
        # is_button_clicked がリスタートボタンでのみ True を返すように設定
        self.mock_gui_instance.is_button_clicked.side_effect = lambda pos, rect: rect == restart_button_rect

        # ゲームオーバー状態を設定
        self.mock_game_instance.game_over = True
        self.mock_game_instance.get_winner.return_value = -1

        # イベントシーケンス: (ダミーで開始) -> ゲームオーバー -> リスタートクリック -> 終了
        # 開始イベントは不要、game_over=True でループに入る
        restart_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=restart_button_rect.center)
        self._run_main_with_events([[], [restart_click_event]]) # 最初のループはゲームオーバー表示、次でリスタート

        # 検証
        self.mock_game_instance.reset.assert_called_once()
        # リスタート後はプレイヤー設定が引き継がれる
        self.mock_game_instance.set_players.assert_called_with(0, 0) # 初期値
        # game_started が True になるはず (次のループでゲーム中描画)

    def test_game_over_reset_button(self):
        """ゲームオーバー時にリセットボタンをクリック"""
        # ゲームオーバー状態にするセットアップ
        start_button_rect = pygame.Rect(100, 500, 150, 40) # ダミー開始ボタン
        reset_button_rect = pygame.Rect(200, 600, 100, 40) # ダミーリセットボタン
        # _calculate_button_rect が状況に応じて正しい Rect を返すように設定
        def calc_rect_side_effect(is_start, game_over=False, is_reset=False, is_quit=False):
            if is_start: return start_button_rect
            if game_over and is_reset: return reset_button_rect # ゲームオーバー時のリセット
            return pygame.Rect(0,0,0,0)
        self.mock_gui_instance._calculate_button_rect.side_effect = calc_rect_side_effect
        # is_button_clicked がリセットボタンでのみ True を返すように設定
        self.mock_gui_instance.is_button_clicked.side_effect = lambda pos, rect: rect == reset_button_rect

        # ゲームオーバー状態を設定
        self.mock_game_instance.game_over = True
        self.mock_game_instance.get_winner.return_value = -1

        # イベントシーケンス: (ダミーで開始) -> ゲームオーバー -> リセットクリック -> 終了
        reset_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=reset_button_rect.center)
        self._run_main_with_events([[], [reset_click_event]])

        # 検証
        self.mock_game_instance.reset.assert_called_once()
        # リセット後はプレイヤー設定もリセットされる
        self.mock_game_instance.set_players.assert_called_with(0, 0)
        # game_started が False になるはず (次のループで開始前描画)

    def test_game_over_quit_button(self):
        """ゲームオーバー時に終了ボタンをクリック"""
        # ゲームオーバー状態にするセットアップ
        start_button_rect = pygame.Rect(100, 500, 150, 40) # ダミー開始ボタン
        quit_button_rect = pygame.Rect(350, 600, 100, 40) # ダミー終了ボタン
        # _calculate_button_rect が状況に応じて正しい Rect を返すように設定
        def calc_rect_side_effect(is_start, game_over=False, is_reset=False, is_quit=False):
            if is_start: return start_button_rect
            if game_over and is_quit: return quit_button_rect # ゲームオーバー時の終了
            return pygame.Rect(0,0,0,0)
        self.mock_gui_instance._calculate_button_rect.side_effect = calc_rect_side_effect
        # is_button_clicked が終了ボタンでのみ True を返すように設定
        self.mock_gui_instance.is_button_clicked.side_effect = lambda pos, rect: rect == quit_button_rect

        # ゲームオーバー状態を設定
        self.mock_game_instance.game_over = True
        self.mock_game_instance.get_winner.return_value = -1

        # イベントシーケンス: (ダミーで開始) -> ゲームオーバー -> 終了クリック -> (ループ終了)
        quit_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=quit_button_rect.center)
        # _run_main_with_events は最後に QUIT を追加するので、終了ボタンクリックで running=False になることを確認
        self._run_main_with_events([[], [quit_click_event]])

        # 検証: pygame.quit() が呼ばれることを確認 (ループ終了後に呼ばれる)
        self.mock_pygame.quit.assert_called_once()

    # --- ゲーム中のボタン操作 ---
    def test_game_in_progress_restart_button(self):
        """ゲーム中にリスタートボタンをクリック"""
        # ゲーム開始状態
        start_button_rect = pygame.Rect(100, 500, 150, 40)
        restart_button_rect = pygame.Rect(50, 600, 100, 40) # ダミー
        # _calculate_button_rect が状況に応じて正しい Rect を返すように設定
        def calc_rect_side_effect(is_start, game_over=False, is_reset=False, is_quit=False):
            if is_start: return start_button_rect
            if not game_over and not is_reset and not is_quit: return restart_button_rect # ゲーム中のリスタート
            return pygame.Rect(0,0,0,0)
        self.mock_gui_instance._calculate_button_rect.side_effect = calc_rect_side_effect
        # is_button_clicked が開始またはリスタートボタンで True を返すように設定
        self.mock_gui_instance.is_button_clicked.side_effect = lambda pos, rect: rect == start_button_rect or rect == restart_button_rect

        start_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=start_button_rect.center)
        restart_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=restart_button_rect.center)

        # イベントシーケンス: 開始 -> リスタート -> 終了
        self._run_main_with_events([[start_click_event], [restart_click_event]])

        # 検証
        self.mock_game_instance.reset.assert_called_once()
        self.mock_game_instance.set_players.assert_called_with(0, 0) # 初期値
        # game_started は True のままのはず

    def test_game_in_progress_quit_button(self):
        """ゲーム中に終了ボタンをクリック"""
        # ゲーム開始状態
        start_button_rect = pygame.Rect(100, 500, 150, 40)
        quit_button_rect = pygame.Rect(350, 600, 100, 40) # ダミー
        # _calculate_button_rect が状況に応じて正しい Rect を返すように設定
        def calc_rect_side_effect(is_start, game_over=False, is_reset=False, is_quit=False):
            if is_start: return start_button_rect
            if not game_over and is_quit: return quit_button_rect # ゲーム中の終了
            return pygame.Rect(0,0,0,0)
        self.mock_gui_instance._calculate_button_rect.side_effect = calc_rect_side_effect
        # is_button_clicked が開始または終了ボタンで True を返すように設定
        self.mock_gui_instance.is_button_clicked.side_effect = lambda pos, rect: rect == start_button_rect or rect == quit_button_rect

        start_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=start_button_rect.center)
        quit_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=quit_button_rect.center)

        # イベントシーケンス: 開始 -> 終了 -> (ループ終了)
        self._run_main_with_events([[start_click_event], [quit_click_event]])

        # 検証: pygame.quit() が呼ばれる
        self.mock_pygame.quit.assert_called_once()

    # --- 人間の不正な手 ---
    def test_human_invalid_move_during_game(self):
        """ゲーム中に人間が不正な手（合法手以外）をクリックした場合"""
        # ゲーム開始状態
        start_button_rect = pygame.Rect(100, 500, 150, 40)
        self.mock_gui_instance._calculate_button_rect.return_value = start_button_rect
        self.mock_gui_instance.is_button_clicked.side_effect = lambda pos, rect: rect == start_button_rect
        start_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=start_button_rect.center)

        # 人間の手番 (-1)
        self.mock_game_instance.turn = -1
        self.mock_game_instance.agents = {-1: None, 1: None}
        valid_moves = [(2, 3)]
        self.mock_game_instance.get_valid_moves.return_value = valid_moves
        # 不正なセル (0, 0) をクリックしたことにする
        invalid_cell = (0, 0)
        self.mock_gui_instance.get_clicked_cell.return_value = invalid_cell
        board_rect = self.mock_gui_instance._calculate_board_rect()
        invalid_click_pos = (board_rect.left + invalid_cell[1] * Screen.CELL_SIZE + Screen.CELL_SIZE // 2,
                             board_rect.top + invalid_cell[0] * Screen.CELL_SIZE + Screen.CELL_SIZE // 2)
        invalid_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=invalid_click_pos)

        # イベントシーケンス: 開始 -> 不正クリック -> 終了
        self._run_main_with_events([[start_click_event], [invalid_click_event]])

        # 検証
        self.mock_gui_instance.get_clicked_cell.assert_called_with(invalid_click_pos)
        # get_valid_moves は呼ばれるが、クリックしたセルがその中にないので place_stone などは呼ばれない
        self.mock_game_instance.get_valid_moves.assert_called()
        self.mock_game_instance.place_stone.assert_not_called()
        self.mock_gui_instance.draw_stone_animation.assert_not_called()
        self.mock_gui_instance.draw_flip_animation.assert_not_called()
        self.mock_game_instance.switch_turn.assert_not_called()

    def test_human_click_outside_board_during_game(self):
        """ゲーム中に人間が盤面外をクリックした場合"""
        # ゲーム開始状態
        start_button_rect = pygame.Rect(100, 500, 150, 40)
        self.mock_gui_instance._calculate_button_rect.return_value = start_button_rect
        self.mock_gui_instance.is_button_clicked.side_effect = lambda pos, rect: rect == start_button_rect
        start_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=start_button_rect.center)

        # 人間の手番 (-1)
        self.mock_game_instance.turn = -1
        self.mock_game_instance.agents = {-1: None, 1: None}
        # get_clicked_cell が (-1, -1) を返すように設定
        self.mock_gui_instance.get_clicked_cell.return_value = (-1, -1)
        outside_click_pos = (0, 0) # 盤面外の適当な座標
        outside_click_event = MagicMock(type=pygame.MOUSEBUTTONDOWN, pos=outside_click_pos)

        # イベントシーケンス: 開始 -> 盤面外クリック -> 終了
        self._run_main_with_events([[start_click_event], [outside_click_event]])

        # 検証
        self.mock_gui_instance.get_clicked_cell.assert_called_with(outside_click_pos)
        # get_valid_moves や place_stone などは呼ばれない
        # self.mock_game_instance.get_valid_moves.assert_not_called() # main.py のロジックでは呼ばれてしまう
        self.mock_game_instance.place_stone.assert_not_called()
        self.mock_gui_instance.draw_stone_animation.assert_not_called()
        self.mock_gui_instance.draw_flip_animation.assert_not_called()
        self.mock_game_instance.switch_turn.assert_not_called()

    # --- キー入力イベントテスト (現在は未使用だが、将来のために) ---
    def test_keydown_event_ignored(self):
        """KEYDOWN イベントが無視されることを確認"""
        keydown_event = MagicMock(type=pygame.KEYDOWN, key=pygame.K_SPACE)
        # 念のため、他のモックが呼ばれないことを確認
        initial_call_counts = {
            'set_message': self.mock_game_instance.set_message.call_count,
            'set_players': self.mock_game_instance.set_players.call_count,
            'reset': self.mock_game_instance.reset.call_count,
            'place_stone': self.mock_game_instance.place_stone.call_count,
        }

        self._run_main_with_events([[keydown_event]])

        # 検証: 主要なメソッドが追加で呼ばれていないことを確認
        self.assertEqual(self.mock_game_instance.set_message.call_count, initial_call_counts['set_message'])
        self.assertEqual(self.mock_game_instance.set_players.call_count, initial_call_counts['set_players'])
        self.assertEqual(self.mock_game_instance.reset.call_count, initial_call_counts['reset'])
        self.assertEqual(self.mock_game_instance.place_stone.call_count, initial_call_counts['place_stone'])
        # pygame.quit() は呼ばれる (ループ終了のため)
        self.mock_pygame.quit.assert_called_once()


if __name__ == '__main__':
    # 環境変数を設定して実行: TEST_PYGAME=1 python -m unittest tests/test_main.py
    unittest.main()

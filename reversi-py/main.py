# main.py
import pygame
import sys
import logging # ロギングを追加
from game import Game
from gui import GameGUI
from config.theme import Screen, Color
# from config.agents import get_agent_options # gui が内部で使うので不要かも

# --- gui.py に追加が必要なメソッド ---
# def get_clicked_radio_button(self, click_pos, player_settings_top):
#     """クリックされたラジオボタンの情報を返す (gui.py に実装)"""
#     # ... (実装は gui.py に記述) ...
#     # return player, agent_id or None, None
# ------------------------------------

def main():
    print("[main] Initializing...") # Debug
    # --- 初期化 ---
    pygame.init()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # ロギング設定
    game = Game()
    gui = GameGUI()
    clock = pygame.time.Clock()

    # --- プレイヤー設定の初期値 ---
    black_player_id = 0
    white_player_id = 0
    print(f"[main] Setting initial players: Black={black_player_id}, White={white_player_id}") # Debug
    game.set_players(black_player_id, white_player_id)

    # --- ゲーム状態 ---
    game_started = False
    running = True
    print("[main] Initialization complete. Starting main loop...") # Debug

    # --- アニメーション管理用フラグ (簡易的な例、必要なら拡張) ---
    # is_animating = False

    # --- メインループ ---
    loop_count = 0 # Debug
    while running:
        loop_count += 1 # Debug
        print(f"\n--- [main loop #{loop_count}] Top ---") # Debug
        print(f"[main loop] State: running={running}, game_started={game_started}, game_over={game.game_over}, turn={game.turn}") # Debug
        time_delta = clock.tick(60) / 1000.0 # FPS制限とデルタタイム

        # --- イベント処理 ---
        mouse_click_pos = None
        print("[main loop] Getting events...") # Debug
        for event in pygame.event.get():
            print(f"[main loop] Processing event: {event}") # Debug
            if event.type == pygame.QUIT:
                print("[main loop] QUIT event received. Setting running = False.") # Debug
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # 左クリックのみ
                    print(f"[main loop] Left mouse button down at {event.pos}") # Debug
                    # --- アニメーション中はクリックを無視する場合 ---
                    # if not is_animating:
                    #     mouse_click_pos = event.pos
                    mouse_click_pos = event.pos # 現状はアニメーション中でもクリックを受け付ける

        # --- 状態更新 (イベントに基づく) ---
        if mouse_click_pos:
            print(f"[main loop] Processing click at {mouse_click_pos}") # Debug
            if not game_started:
                print("[main loop] Click processing: Before game start") # Debug
                # --- ゲーム開始前 ---
                start_button_rect = gui._calculate_button_rect(is_start_button=True)
                is_start_clicked = gui.is_button_clicked(mouse_click_pos, start_button_rect)
                print(f"[main loop] Start button clicked? {is_start_clicked}") # Debug
                if is_start_clicked:
                    game_started = True
                    game.set_message("")
                    print("[main loop] Game started!") # Debug
                else:
                    # ラジオボタン判定 (GUIに移譲)
                    player_settings_top = gui._calculate_player_settings_top()
                    clicked_player, clicked_agent_id = gui.get_clicked_radio_button(
                        mouse_click_pos, player_settings_top
                    )
                    print(f"[main loop] Radio button clicked? Player={clicked_player}, AgentID={clicked_agent_id}") # Debug
                    if clicked_player is not None:
                        if clicked_player == -1 and black_player_id != clicked_agent_id:
                            print(f"[main loop] Changing Black player to ID: {clicked_agent_id}") # Debug
                            black_player_id = clicked_agent_id
                            game.set_players(black_player_id, white_player_id)
                        elif clicked_player == 1 and white_player_id != clicked_agent_id:
                            print(f"[main loop] Changing White player to ID: {clicked_agent_id}") # Debug
                            white_player_id = clicked_agent_id
                            game.set_players(black_player_id, white_player_id)

            elif game.game_over:
                print("[main loop] Click processing: Game over") # Debug
                # --- ゲームオーバー時 ---
                restart_button_rect = gui._calculate_button_rect(False, True, False, False)
                reset_button_rect = gui._calculate_button_rect(False, True, True, False)
                quit_button_rect = gui._calculate_button_rect(False, True, False, True)

                is_restart_clicked = gui.is_button_clicked(mouse_click_pos, restart_button_rect)
                is_reset_clicked = gui.is_button_clicked(mouse_click_pos, reset_button_rect)
                is_quit_clicked = gui.is_button_clicked(mouse_click_pos, quit_button_rect)
                print(f"[main loop] Game Over Buttons: Restart={is_restart_clicked}, Reset={is_reset_clicked}, Quit={is_quit_clicked}") # Debug

                if is_restart_clicked:
                    print("[main loop] Restart button clicked (Game Over). Resetting game...") # Debug
                    game.reset()
                    game.set_players(black_player_id, white_player_id) # 設定引き継ぎ
                    game_started = True
                    # is_animating = False # アニメーション状態リセット
                elif is_reset_clicked:
                    print("[main loop] Reset button clicked (Game Over). Resetting game and settings...") # Debug
                    game.reset()
                    black_player_id = 0 # 設定リセット
                    white_player_id = 0
                    game.set_players(black_player_id, white_player_id)
                    game_started = False
                    # is_animating = False # アニメーション状態リセット
                elif is_quit_clicked:
                    print("[main loop] Quit button clicked (Game Over). Setting running = False.") # Debug
                    running = False

            else:
                print("[main loop] Click processing: During game") # Debug
                # --- ゲーム中 ---
                restart_button_rect = gui._calculate_button_rect(False, False, False, False)
                reset_button_rect = gui._calculate_button_rect(False, False, True, False)
                quit_button_rect = gui._calculate_button_rect(False, False, False, True)

                is_restart_clicked = gui.is_button_clicked(mouse_click_pos, restart_button_rect)
                is_reset_clicked = gui.is_button_clicked(mouse_click_pos, reset_button_rect)
                is_quit_clicked = gui.is_button_clicked(mouse_click_pos, quit_button_rect)
                print(f"[main loop] In-Game Buttons: Restart={is_restart_clicked}, Reset={is_reset_clicked}, Quit={is_quit_clicked}") # Debug

                if is_restart_clicked:
                    print("[main loop] Restart button clicked (In Game). Resetting game...") # Debug
                    game.reset()
                    game.set_players(black_player_id, white_player_id) # 設定引き継ぎ
                    game_started = True
                    # is_animating = False
                elif is_reset_clicked:
                    print("[main loop] Reset button clicked (In Game). Resetting game and settings...") # Debug
                    game.reset()
                    black_player_id = 0 # 設定リセット
                    white_player_id = 0
                    game.set_players(black_player_id, white_player_id)
                    game_started = False
                    # is_animating = False
                elif is_quit_clicked:
                    print("[main loop] Quit button clicked (In Game). Setting running = False.") # Debug
                    running = False
                elif game.agents[game.turn] is None: # 人間の手番
                    print("[main loop] Human turn. Checking cell click...") # Debug
                    row, col = gui.get_clicked_cell(mouse_click_pos)
                    print(f"[main loop] Clicked cell: ({row}, {col})") # Debug
                    valid_moves = game.get_valid_moves()
                    print(f"[main loop] Valid moves: {valid_moves}") # Debug
                    if (row, col) in valid_moves:
                        print(f"[main loop] Placing stone at ({row}, {col}) for turn {game.turn}") # Debug
                        # --- 人間の手 ---
                        if game.place_stone(row, col):
                            game.set_message("")
                            print("[main loop] Stone placed. Switching turn and checking game over.") # Debug
                            game.switch_turn()
                            game.check_game_over() # ゲームオーバーチェック
                        else:
                            print(f"[main loop] Error: place_stone({row}, {col}) returned False unexpectedly.") # Debug
                    else:
                        print("[main loop] Clicked cell is not a valid move.") # Debug
                else:
                    print("[main loop] Click occurred during AI turn, ignoring cell click.") # Debug

        # --- 状態更新 (AIの手番、パス) ---
        # --- アニメーション中はAIやパス処理をスキップする場合 ---
        # if not is_animating:
        if game_started and not game.game_over:
            print("[main loop] Checking AI/Pass...") # Debug
            current_turn = game.turn
            current_agent = game.agents[current_turn]
            valid_moves = game.get_valid_moves()
            print(f"[main loop] Turn: {current_turn}, Agent: {type(current_agent).__name__}, Valid moves: {valid_moves}") # Debug

            if not valid_moves:
                print("[main loop] No valid moves. Checking for pass...") # Debug
                # --- パス処理 ---
                current_player_color = '黒' if current_turn == -1 else '白'
                pass_message = f"{current_player_color}はパスです。"
                print(f"[main loop] {pass_message}") # Debug
                game.set_message(pass_message)
                game.switch_turn()
                print(f"[main loop] Switched turn to {game.turn}. Checking opponent's moves...") # Debug
                # 相手もパスかチェック -> ゲームオーバー判定
                opponent_valid_moves = game.get_valid_moves()
                print(f"[main loop] Opponent valid moves: {opponent_valid_moves}") # Debug
                if not opponent_valid_moves:
                    print("[main loop] Double pass detected. Setting game_over = True.") # Debug
                    game.game_over = True
                    # 勝敗メッセージ設定は描画セクションで行う
                else:
                    print("[main loop] Opponent has moves. Continuing game.") # Debug
            elif current_agent is not None:
                print(f"[main loop] AI turn ({type(current_agent).__name__}). Calling play...") # Debug
                # --- AIの手番 ---
                move = current_agent.play(game)
                print(f"[main loop] AI returned move: {move}") # Debug
                if move and move in valid_moves: # AIが有効な手を返したか確認
                    print(f"[main loop] Placing AI stone at {move} for turn {current_turn}") # Debug
                    if game.place_stone(move[0], move[1]):
                        game.set_message("")
                        print("[main loop] AI Stone placed. Switching turn and checking game over.") # Debug
                        game.switch_turn()
                        game.check_game_over()
                    else:
                         print(f"[main loop] Error: AI place_stone({move[0]}, {move[1]}) returned False unexpectedly.") # Debug
                else:
                    # AIが手を返さなかった、または無効な手を返した場合
                    log_message = f"AI ({type(current_agent).__name__}) returned invalid move: {move}. Valid moves: {valid_moves}"
                    logging.warning(log_message)
                    print(f"[main loop] {log_message}") # Debug
                    # 必要であればここでエラー処理やフォールバック処理を追加
            else:
                print("[main loop] Human turn, waiting for click.") # Debug

        # --- 描画処理 ---
        print("[main loop] Drawing...") # Debug
        gui.screen.fill(Color.BACKGROUND)
        player_settings_top = gui._calculate_player_settings_top() # 描画前に計算

        # --- アニメーション描画 (必要なら) ---
        # if is_animating:
        #     # アニメーションのステップ描画関数を呼び出す
        #     # is_animating = gui.draw_animation_step(animation_type, animation_data) # アニメ完了したらFalseを返すように
        #     pass # アニメーション描画処理
        # else:
        # --- 通常描画 ---
        if not game_started:
            print("[main loop] Drawing: Before game start screen") # Debug
            # --- ゲーム開始前画面 ---
            gui.draw_board(game)
            gui.draw_start_button()
            gui.draw_player_settings(game, player_settings_top, enabled=True)

        elif game.game_over:
            print("[main loop] Drawing: Game over screen") # Debug
            # --- ゲームオーバー画面 ---
            winner = game.get_winner()
            winner_message = ""
            if winner == -1: winner_message = "黒の勝ちです！"
            elif winner == 1: winner_message = "白の勝ちです！"
            else: winner_message = "引き分けです！"
            print(f"[main loop] Game over message: {winner_message}") # Debug
            game.set_message(winner_message)

            gui.draw_board(game)
            gui.draw_message(game.get_message(), is_game_over=True)
            gui.draw_player_settings(game, player_settings_top, enabled=True) # リセット用に有効
            gui.draw_restart_button(game_over=True)
            gui.draw_reset_button(game_over=True)
            gui.draw_quit_button(game_over=True)

        else:
            print("[main loop] Drawing: In-game screen") # Debug
            # --- ゲーム中画面 ---
            gui.draw_board(game)
            if game.agents[game.turn] is None: # 人間の番なら合法手表示
                print("[main loop] Drawing valid moves for human.") # Debug
                gui.draw_valid_moves(game)
            gui.draw_turn_message(game)
            gui.draw_restart_button(game_over=False)
            gui.draw_reset_button(game_over=False)
            gui.draw_quit_button(game_over=False)
            current_message = game.get_message()
            if current_message: print(f"[main loop] Drawing message: {current_message}") # Debug
            gui.draw_message(current_message) # パスメッセージなど
            gui.draw_player_settings(game, player_settings_top, enabled=False) # ゲーム中は設定無効

        # --- 画面更新 ---
        print("[main loop] Flipping display.") # Debug
        pygame.display.flip()
        print("-" * 20) # ループの区切り

    # --- 終了処理 ---
    print("[main] Exiting main loop.") # Debug
    print("[main] Quitting Pygame...") # Debug
    pygame.quit()
    print("[main] Exiting system...") # Debug
    sys.exit()

if __name__ == "__main__":
    main()

# main.py
import pygame
import sys
import os

# --- 定数 ---
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)

# --- Pygameの初期化 ---
print("Initializing Pygame...")
try:
    # Docker内でDISPLAY環境変数が設定されているか確認
    # X11転送が設定されていない場合、ダミーのビデオドライバを使用
    if "DISPLAY" not in os.environ:
        print("DISPLAY environment variable not set. Using dummy video driver.")
        # ダミードライバを使う場合、画面表示はされないがテストは可能
        # os.environ["SDL_VIDEODRIVER"] = "dummy"
        # ただし、今回はGUI表示が目的なので、DISPLAYがない場合はエラーにする方が親切かもしれない
        print("Error: DISPLAY environment variable is required for GUI.")
        print("Ensure XQuartz is running and configured, and run the container with '-e DISPLAY=...'")
        sys.exit(1)
    else:
        print(f"Using DISPLAY: {os.environ['DISPLAY']}")

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Simple Pygame App in Docker")
    print("Pygame initialized successfully.")
except pygame.error as e:
    print(f"Error initializing Pygame or setting display mode: {e}")
    # SDL_AUDIODRIVER=dummy を試す (音声関連のエラーの場合)
    if "audio" in str(e).lower():
         print("Trying with dummy audio driver...")
         os.environ["SDL_AUDIODRIVER"] = "dummy"
         try:
             pygame.quit() # 一度終了
             pygame.init() # 再度初期化
             screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
             pygame.display.set_caption("Simple Pygame App in Docker (Dummy Audio)")
             print("Pygame initialized with dummy audio driver.")
         except pygame.error as e2:
             print(f"Still failed after setting dummy audio driver: {e2}")
             sys.exit(1)
    else:
        print("exit(1)")
        sys.exit(1)


# --- ゲームループ ---
print("Start game")
running = True
while running:
    # --- イベント処理 ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: # ESCキーで終了
                running = False

    # --- 描画処理 ---
    screen.fill(WHITE)  # 背景を白で塗りつぶし
    pygame.draw.circle(screen, BLUE, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 50) # 中央に青い円を描画

    # --- 画面更新 ---
    pygame.display.flip()

# --- 終了処理 ---
print("Quitting Pygame...")
pygame.quit()
sys.exit()
print("Exited.")


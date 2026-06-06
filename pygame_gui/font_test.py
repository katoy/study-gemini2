# font_test.py
import pygame
import sys
import os

pygame.init()

# --- 設定 ---
FONT_FILENAME = 'MPLUS1p-Regular.ttf'
FONT_DIR = 'fonts'
FONT_SIZE = 30
TEXT_TO_RENDER = "設定 テスト Test" # 描画するテキスト (日本語と英語を混ぜる)
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 200
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
# -----------

# フォントファイルの絶対パスを取得
script_dir = os.path.dirname(__file__)
font_path = os.path.join(script_dir, FONT_DIR, FONT_FILENAME)

print(f"Attempting to load font from: {font_path}")

# フォントが存在するか確認
if not os.path.exists(font_path):
    print(f"Error: Font file not found at the specified path.")
    pygame.quit()
    sys.exit()

# フォントをロード
try:
    # pygame.font.Font はファイルパスを直接受け取る
    font = pygame.font.Font(font_path, FONT_SIZE)
    print(f"Font '{FONT_FILENAME}' loaded successfully.")
except pygame.error as e:
    print(f"Error loading font with pygame.font.Font: {e}")
    # 代替として pygame.freetype を試す (インストールされていれば)
    try:
        import pygame.freetype
        print("Trying with pygame.freetype...")
        game_font = pygame.freetype.Font(font_path, FONT_SIZE)
        print(f"Font '{FONT_FILENAME}' loaded successfully using freetype.")
        font = game_font # freetype オブジェクトを font 変数に入れる
    except ImportError:
        print("pygame.freetype module not found.")
        pygame.quit()
        sys.exit()
    except Exception as e_ft:
        print(f"Error loading font with pygame.freetype: {e_ft}")
        pygame.quit()
        sys.exit()
except Exception as e:
    print(f"An unexpected error occurred during font loading: {e}")
    pygame.quit()
    sys.exit()


# テキストを描画 (freetypeか通常かでメソッドが異なる)
text_surface = None
try:
    if isinstance(font, pygame.font.Font): # 通常の Font オブジェクトの場合
         # render(text, antialias, color, background=None)
        text_surface = font.render(TEXT_TO_RENDER, True, WHITE)
    elif 'freetype' in sys.modules and isinstance(font, pygame.freetype.Font): # freetype の場合
        # render_to(surf, dest, text, fgcolor=None, bgcolor=None, style=STYLE_DEFAULT, rotation=0, size=0)
        # まずサイズを取得してSurfaceを作成する必要がある
        text_rect = font.get_rect(TEXT_TO_RENDER)
        text_surface = pygame.Surface(text_rect.size, pygame.SRCALPHA) # 透明背景のSurface
        font.render_to(text_surface, (0, 0), TEXT_TO_RENDER, WHITE)
    else:
         print("Error: Font object type not recognized.")
         pygame.quit()
         sys.exit()

    print("Text rendered successfully.")
    print(f"Rendered text surface size: {text_surface.get_size()}")

except Exception as e:
    print(f"Error rendering text: {e}")
    pygame.quit()
    sys.exit()

# 簡単なウィンドウ表示
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Font Test")

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BLACK)
    # 画面中央に描画
    text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
    screen.blit(text_surface, text_rect)
    pygame.display.flip()

pygame.quit()
print("Font test finished.")

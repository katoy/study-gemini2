import pygame
import random

# 初期化
pygame.init()

# 画面設定
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("ブロック崩し")

# 色定義
white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)
blue = (0, 0, 255)
green = (0, 255, 0)
yellow = (255, 255, 0)

# パドル設定
paddle_width = 100
paddle_height = 20
paddle_x = (screen_width - paddle_width) // 2
paddle_y = screen_height - paddle_height - 10
paddle_speed = 8

# ボール設定
ball_radius = 10
ball_x = screen_width // 2
ball_y = screen_height // 2
ball_speed_x = 5
ball_speed_y = -5

# ブロック設定
block_width = 75
block_height = 20
block_rows = 5
block_cols = 10
block_gap = 5
block_colors = [red, blue, green, yellow]
blocks = []

# ブロック作成
def create_blocks():
    blocks_list = []
    for row in range(block_rows):
        for col in range(block_cols):
            block_x = col * (block_width + block_gap) + block_gap
            block_y = row * (block_height + block_gap) + block_gap + 50
            block_rect = pygame.Rect(block_x, block_y, block_width, block_height)
            blocks_list.append([block_rect, random.choice(block_colors)])
    return blocks_list

blocks = create_blocks()

# スコア
score = 0
font = pygame.font.Font(None, 36)

# ゲームオーバー
game_over = False

# パドルの移動処理
def move_paddle(keys):
    global paddle_x
    if keys[pygame.K_LEFT] and paddle_x > 0:
        paddle_x -= paddle_speed
    if keys[pygame.K_RIGHT] and paddle_x < screen_width - paddle_width:
        paddle_x += paddle_speed
    return paddle_x

# ボールの移動処理
def move_ball():
    global ball_x, ball_y, ball_speed_x, ball_speed_y, game_over
    ball_x += ball_speed_x
    ball_y += ball_speed_y

    # 壁との衝突判定
    if ball_x <= 0 or ball_x >= screen_width - ball_radius:
        ball_speed_x *= -1
    if ball_y <= 0:
        ball_speed_y *= -1
    if ball_y >= screen_height:
        game_over = True
    return ball_x, ball_y, ball_speed_x, ball_speed_y, game_over

# パドルとの衝突判定
def check_paddle_collision():
    global ball_speed_y, ball_x, ball_y, paddle_x, paddle_y, paddle_width, paddle_height, ball_radius
    paddle_rect = pygame.Rect(paddle_x, paddle_y, paddle_width, paddle_height)
    ball_rect = pygame.Rect(ball_x, ball_y, ball_radius, ball_radius)
    if ball_rect.colliderect(paddle_rect):
        ball_speed_y *= -1
    return ball_speed_y

# ブロックとの衝突判定
def check_block_collision():
    global blocks, score, ball_speed_y, ball_x, ball_y, ball_radius
    ball_rect = pygame.Rect(ball_x, ball_y, ball_radius, ball_radius)
    for block in blocks[:]:
        if ball_rect.colliderect(block[0]):
            blocks.remove(block)
            ball_speed_y *= -1
            score += 1
    return blocks, score

# ゲームループ
def game_loop():
    global running, paddle_x, ball_x, ball_y, ball_speed_x, ball_speed_y, game_over, blocks, score
    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # パドルの移動
        keys = pygame.key.get_pressed()
        paddle_x = move_paddle(keys)

        # ボールの移動
        ball_x, ball_y, ball_speed_x, ball_speed_y, game_over = move_ball()

        # パドルとの衝突判定
        ball_speed_y = check_paddle_collision()

        # ブロックとの衝突判定
        blocks, score = check_block_collision()

        # 画面描画
        screen.fill(black)

        # パドル描画
        pygame.draw.rect(screen, white, (paddle_x, paddle_y, paddle_width, paddle_height))

        # ボール描画
        pygame.draw.circle(screen, white, (int(ball_x), int(ball_y)), ball_radius)

        # ブロック描画
        for block in blocks:
            pygame.draw.rect(screen, block[1], block[0])

        # スコア表示
        score_text = font.render(f"Score: {score}", True, white)
        screen.blit(score_text, (10, 10))

        # ゲームオーバー表示
        if game_over:
            game_over_text = font.render("Game Over", True, white)
            text_rect = game_over_text.get_rect(center=(screen_width // 2, screen_height // 2))
            screen.blit(game_over_text, text_rect)
            ball_speed_x = 0
            ball_speed_y = 0

        # 画面更新
        pygame.display.flip()

        # フレームレート設定
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    game_loop()

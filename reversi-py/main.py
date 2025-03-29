import pygame
import random

# 色の定義
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 128, 0)
GRAY = (128, 128, 128)

# 画面サイズ
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600

# 盤面のサイズ
BOARD_SIZE = 8
CELL_SIZE = SCREEN_WIDTH // BOARD_SIZE

class Reversi:
    def __init__(self):
        self.board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.board[3][3] = self.board[4][4] = 1  # 白
        self.board[3][4] = self.board[4][3] = -1 # 黒
        self.turn = -1  # 黒から開始
        self.game_over = False

    def is_valid_move(self, row, col, turn):
        # 盤面の範囲外、すでに石がある場所は無効
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE) or self.board[row][col] != 0:
            return False

        # 8方向をチェック
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                flipped = False
                while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                    if self.board[r][c] == 0:
                        break
                    if self.board[r][c] == turn:
                        if flipped:
                            return True
                        break
                    flipped = True
                    r += dr
                    c += dc
        return False

    def get_valid_moves(self, turn):
        valid_moves = []
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.is_valid_move(row, col, turn):
                    valid_moves.append((row, col))
        return valid_moves

    def place_stone(self, row, col, turn):
        if not self.is_valid_move(row, col, turn):
            return False

        self.board[row][col] = turn
        # 8方向をチェックして石をひっくり返す
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                to_flip = []
                while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                    if self.board[r][c] == 0:
                        break
                    if self.board[r][c] == turn:
                        for fr, fc in to_flip:
                            self.board[fr][fc] = turn
                        break
                    to_flip.append((r, c))
                    r += dr
                    c += dc
        return True

    def switch_turn(self):
        self.turn *= -1

    def check_game_over(self):
        if not self.get_valid_moves(-1) and not self.get_valid_moves(1):
            self.game_over = True

    def get_winner(self):
        black_count = sum(row.count(-1) for row in self.board)
        white_count = sum(row.count(1) for row in self.board)
        if black_count > white_count:
            return -1  # 黒の勝ち
        elif white_count > black_count:
            return 1  # 白の勝ち
        else:
            return 0  # 引き分け

class Agent:
    def play(self, game):
        raise NotImplementedError

class RandomAgent(Agent):
    def play(self, game):
        valid_moves = game.get_valid_moves(game.turn)
        if valid_moves:
            return random.choice(valid_moves)
        return None

class HumanAgent(Agent):
    def play(self, game):
        # マウス入力から石を置く場所を決定
        pass

class GameGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Reversi")
        self.font = pygame.font.Font(None, 36)

    def draw_board(self, game):
        self.screen.fill(GREEN)
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                pygame.draw.rect(self.screen, BLACK, (col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)
                if game.board[row][col] == 1:
                    pygame.draw.circle(self.screen, WHITE, (col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2), CELL_SIZE // 2 - 5)
                elif game.board[row][col] == -1:
                    pygame.draw.circle(self.screen, BLACK, (col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2), CELL_SIZE // 2 - 5)

    def draw_valid_moves(self, game):
        valid_moves = game.get_valid_moves(game.turn)
        for row, col in valid_moves:
            pygame.draw.circle(self.screen, GRAY, (col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2), CELL_SIZE // 8)

    def draw_message(self, message):
        text = self.font.render(message, True, WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(text, text_rect)

    def run(self, agent1, agent2):
        game = Reversi()
        agents = {
            -1: agent1,
            1: agent2
        }
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and isinstance(agents[game.turn], HumanAgent):
                    x, y = pygame.mouse.get_pos()
                    col = x // CELL_SIZE
                    row = y // CELL_SIZE
                    if game.place_stone(row, col, game.turn):
                        game.switch_turn()
                        game.check_game_over()

            if not game.game_over and not isinstance(agents[game.turn], HumanAgent):
                move = agents[game.turn].play(game)
                if move:
                    row, col = move
                    game.place_stone(row, col, game.turn)
                    game.switch_turn()
                    game.check_game_over()
                else:
                    game.switch_turn()
                    game.check_game_over()

            self.draw_board(game)
            self.draw_valid_moves(game)

            if game.game_over:
                winner = game.get_winner()
                if winner == -1:
                    self.draw_message("Black wins!")
                elif winner == 1:
                    self.draw_message("White wins!")
                else:
                    self.draw_message("Draw!")
            else:
                self.draw_message("Black's turn" if game.turn == -1 else "White's turn")

            pygame.display.flip()

        pygame.quit()

if __name__ == "__main__":
    gui = GameGUI()

    # 対戦モードの選択
    mode = input("Select mode (1: Human vs Random, 2: Human vs Human, 3: Random vs Random): ")
    if mode == "1":
        agent1 = HumanAgent()
        agent2 = RandomAgent()
    elif mode == "2":
        agent1 = HumanAgent()
        agent2 = HumanAgent()
    elif mode == "3":
        agent1 = RandomAgent()
        agent2 = RandomAgent()
    else:
        print("Invalid mode selected.")
        exit()

    gui.run(agent1, agent2)

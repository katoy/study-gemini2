import pygame
import pygame_gui


class PygameApp:

    def __init__(self, width=800, height=600):
        pygame.init()
        self.width = width
        self.height = height
        self.setup_display()
        self.setup_manager()
        self.clock = pygame.time.Clock()
        self.is_running = True

    def setup_display(self):
        pygame.display.set_caption('Quick Start')
        self.window_surface = pygame.display.set_mode((self.width, self.height))
        self.background = pygame.Surface((self.width, self.height))
        self.background.fill(pygame.Color('#000000'))

    def setup_manager(self):
        self.manager = pygame_gui.UIManager((self.width, self.height))
        self.hello_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((self.width//2 - 50, self.height//2 - 25), (100, 50)),
            text='Say Hello',
            manager=self.manager
        )

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            self.manager.process_events(event)

    def run(self):
        while self.is_running:
            time_delta = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.manager.update(time_delta)
            self.draw()

    def draw(self):
        self.window_surface.blit(self.background, (0, 0))
        self.manager.draw_ui(self.window_surface)
        pygame.display.update()


if __name__ == "__main__":
    app = PygameApp()
    app.run()

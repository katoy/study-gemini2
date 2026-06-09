import sys
import traceback
import os
import pygame

# Initialize pygame as early as possible to avoid circular import issues in font module.
pygame.init()

# Ensure the project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    print("Testing GUI initialization without mocks...")
    try:
        # These imports may trigger pygame.font initialization
        from game import Game
        from gui import GameGUI

        print("Imports successful. Instantiating Game and GameGUI...")

        _game = Game()
        _gui = GameGUI()

        print("GUI Instantiation successful. Integration test passed.")
        pygame.quit()
        sys.exit(0)
    except Exception as e:
        print(f"GUI Initialization failed: {e}")
        traceback.print_exc()
        try:
            pygame.quit()
        except Exception:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()

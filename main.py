# main.py
import pygame

from ai.basic_agent import BasicAgent
from api.api import GameAPI
from backend.board import GameState, create_random_map
from backend.game_engine import GameEngine
from backend.logic import GameLogic
from backend.units import Archer, Swordsman
from frontend.renderer import Renderer
from frontend.ui import UI
from utils.constants import (
    CELL_SIZE,
    GRID_H,
    GRID_W,
    SCREEN_H,
    SCREEN_W,
    SIDEBAR_WIDTH,
    TeamType,
)
from utils.logging import create_log_file, logger


def create_game(ui: UI):
    """Create a new game state and return a GameAPI instance."""
    game_state = GameState(
        width=GRID_W,
        height=GRID_H,
        cell_size=CELL_SIZE,
        tile_map=create_random_map(GRID_W, GRID_H),
    )
    game_logic = GameLogic(game_state=game_state)
    game_renderer = ui.renderer  # Use the same renderer as the UI

    game_api = GameAPI(
        game_ui=ui,
        renderer=game_renderer,
        game_board=game_state,
        game_logic=game_logic,
        agent=BasicAgent(),
        player_team=TeamType.PLAYER,
        ai_team=TeamType.AI,
    )

    # Add units
    p1 = [Swordsman(1, 1, team=TeamType.PLAYER), Archer(2, 2, team=TeamType.PLAYER)]
    p2 = [
        Swordsman(GRID_W - 2, GRID_H - 2, team=TeamType.AI),
        Archer(GRID_W - 3, GRID_H - 2, team=TeamType.AI),
    ]
    for u in p1 + p2:
        game_api.game_board.add_unit(u)

    return game_api


def main():
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((SCREEN_W + SIDEBAR_WIDTH, SCREEN_H))
    pygame.display.set_caption("Commanders' Arena")
    font = pygame.font.Font(None, 28)

    # Create renderer first
    game_renderer = Renderer(cell_size=CELL_SIZE, font=font)

    # Single UI instance with renderer
    ui = UI(cell_size=CELL_SIZE, renderer=game_renderer)
    clock = pygame.time.Clock()

    running = True
    while running:
        # --- Main menu ---
        choice = ui.start_menu(screen, font)
        if choice == "quit":
            break

        create_log_file()

        # --- Start a new game ---
        game_api = create_game(ui)
        engine = GameEngine(game_api, screen, font, clock)
        result = engine.run()

        # --- Handle sidebar actions from GameEngine ---
        if result is False:  # Quit requested
            running = False
        elif result == "menu":  # Return to main menu
            continue
        else:
            # Finished game normally → back to menu automatically
            continue

    pygame.quit()
    logger("Exited game loop")


if __name__ == "__main__":
    main()

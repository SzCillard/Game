"""
main.py

Entry point for Commanders' Arena.

This module:
- Initializes pygame and the display window.
- Creates the renderer and UI.
- Starts the main menu and game loop.
- Connects all backend (logic, engine, AI) and frontend (renderer, UI) components.
"""

import pygame

from ai.basic_agent import BasicAgent
from api.api import GameAPI
from backend.board import GameState, create_random_map
from backend.game_engine import GameEngine
from backend.logic import GameLogic
from backend.units import Archer, Horseman, Spearman, Swordsman
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
from utils.music_utils import play_menu_music

# ======================================================================
# 🎮 Game Setup Helper
# ======================================================================


def create_game(ui: UI) -> GameAPI:
    """
    Create a new game session with map, logic, renderer, and units.

    Args:
        ui (UI): The active user interface instance (used for rendering and menus).

    Returns:
        GameAPI: The fully initialized game API instance ready for GameEngine.
    """
    # --- Initialize core game state ---
    game_state = GameState(
        width=GRID_W,
        height=GRID_H,
        cell_size=CELL_SIZE,
        tile_map=create_random_map(GRID_W, GRID_H),  # Procedurally generate terrain
    )

    # --- Create supporting systems ---
    game_logic = GameLogic(game_state=game_state)
    game_renderer = ui.renderer  # Share same renderer between UI and gameplay

    # --- Combine everything into the API interface ---
    game_api = GameAPI(
        game_ui=ui,
        renderer=game_renderer,
        game_board=game_state,
        game_logic=game_logic,
        agent=BasicAgent(),  # Default AI
        player_team=TeamType.PLAYER,
        ai_team=TeamType.AI,
    )

    # --- Place units on both teams ---
    # Player units (bottom-left area)
    p1 = [
        Swordsman(1, 1, team=TeamType.PLAYER),
        Archer(2, 2, team=TeamType.PLAYER),
        Horseman(1, 2, team=TeamType.PLAYER),
        Spearman(2, 1, team=TeamType.PLAYER),
    ]

    # AI units (top-right area)
    p2 = [
        Swordsman(GRID_W - 2, GRID_H - 2, team=TeamType.AI),
        Archer(GRID_W - 3, GRID_H - 2, team=TeamType.AI),
        Horseman(GRID_W - 2, GRID_H - 3, team=TeamType.AI),
        Horseman(GRID_W - 3, GRID_H - 3, team=TeamType.AI),
        Spearman(GRID_W - 4, GRID_H - 2, team=TeamType.AI),
    ]

    # Register all units on the board
    for u in p1 + p2:
        game_api.game_board.add_unit(u)

    return game_api


# ======================================================================
# 🧠 Main Loop
# ======================================================================


def main():
    """Main entry function. Handles initialization, menus, and game loop."""
    # --- Initialize pygame systems ---
    pygame.init()
    pygame.font.init()

    # --- Set up window ---
    screen = pygame.display.set_mode((SCREEN_W + SIDEBAR_WIDTH, SCREEN_H))
    pygame.display.set_caption("Commanders' Arena")
    icon = pygame.image.load("assets/images/game_icon/roman-helmet.png")
    pygame.display.set_icon(icon)

    # --- Prepare default font ---
    font = pygame.font.Font(None, 28)

    # --- Renderer and UI setup ---
    game_renderer = Renderer(cell_size=CELL_SIZE)
    ui = UI(cell_size=CELL_SIZE, renderer=game_renderer)

    # --- Frame rate limiter ---
    clock = pygame.time.Clock()

    # ==================================================================
    # 🏁 Main Game Loop
    # ==================================================================
    running = True
    while running:
        # --- Display the main menu ---
        play_menu_music()
        choice = ui.start_menu(screen, font)

        if choice == "quit":
            # Player chose to exit directly from menu
            break

        # Create a new log file for the session
        create_log_file()

        # --- Start a new match ---
        game_api = create_game(ui)
        engine = GameEngine(game_api, screen, font, clock)

        # Run the main game loop
        result = engine.run()

        # --- Handle post-game result ---
        if result is False:  # Quit requested mid-game
            running = False
        elif result == "menu":  # Back to main menu
            continue
        else:
            # Normal match completion → automatically return to menu
            continue

    # --- Cleanup ---
    pygame.quit()
    logger("Exited game loop")


# ======================================================================
# 🚀 Entry Point
# ======================================================================

if __name__ == "__main__":
    main()

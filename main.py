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
from ai.draft_helper import get_ai_draft_units
from api.api import GameAPI
from backend.board import GameState, create_random_map
from backend.game_engine import GameEngine
from backend.logic import GameLogic
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
from utils.path_utils import get_asset_path

# ======================================================================
# 🎮 Game Setup Helper
# ======================================================================


def create_game(ui: UI, player_unit_names: list[str]) -> GameAPI:
    """
    Create a new game session with map, logic, renderer, and units.

    Args:
        ui (UI): The active user interface instance (used for rendering and menus).
        player_unit_names (list[str]): Names of units selected
        by the player in the draft.

    Returns:
        GameAPI: The fully initialized game API instance ready for GameEngine.
    """
    try:
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

        # --- Add PLAYER units based on selection ---

        game_api.add_units(player_unit_names, team=TeamType.PLAYER)

        # --- AI units (basic mirror for now) ---

        ai_draft_names: list[str] = get_ai_draft_units(funds=100)

        game_api.add_units(ai_draft_names, team=TeamType.AI)

        return game_api
    except Exception as e:
        logger(f"Error during game creation: {e}")
        raise


# ======================================================================
# 🧠 Main Loop
# ======================================================================


def main():
    """Main entry function. Handles initialization, menus, and game loop."""
    # --- Initialize pygame systems ---
    try:
        pygame.init()
        pygame.font.init()

        # --- Set up window icon and caption BEFORE creating the window ---
        icon_path = get_asset_path("assets/images/game_icon/roman-helmet-32.png")
        try:
            icon = pygame.image.load(icon_path)
            pygame.display.set_icon(icon)
        except Exception as e:
            logger(f"[Warning] Could not load window icon: {e} -> {icon_path}")

        screen = pygame.display.set_mode((SCREEN_W + SIDEBAR_WIDTH, SCREEN_H))
        pygame.display.set_caption("Commanders' Arena")

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
                break

            if choice == "start_game":
                # --- Draft / Army Selection Phase ---
                selected_units = ui.draft_menu(screen)
                if not selected_units:
                    continue  # Return to main menu if canceled

                # --- Create a new log file for the session ---
                create_log_file()

                # --- Start a new match with selected units ---
                game_api = create_game(ui, selected_units)
                engine = GameEngine(game_api, screen, font, clock)

                # --- Run the main battle loop ---
                result = engine.run()

                # --- Handle post-game result ---
                if result is False:  # Quit mid-game
                    running = False
                elif result == "menu":
                    continue
                else:
                    # Normal match completion → return to menu
                    continue

    except Exception as e:
        logger(f"Critical error in main: {e}")
    finally:
        # --- Cleanup ---
        pygame.quit()
        logger("Exited game loop")


# ======================================================================
# 🚀 Entry Point
# ======================================================================

if __name__ == "__main__":
    main()

"""
main.py

Entry point for Commanders' Arena.
"""

import os

import pygame

from ai.agents.runtime_neat_agent import RuntimeNeatAgent
from ai.draft_helper import get_ai_draft_units
from ai.neat.neat_network import NeatNetwork
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
# 🤖 Helper: load runtime NEAT agent (if possible)
# ======================================================================


def create_runtime_neat_agent() -> RuntimeNeatAgent | None:
    """
    Try to load a NEAT network from a best_genome.pkl file.
    If successful, return a RuntimeNeatAgent. Otherwise, return None.
    """
    # Candidate paths – adjust if your trainer saves elsewhere
    genome_candidates = [
        "ai/neat/genomes/best_genome.pkl",
        "ai/neat/best_genome.pkl",
        "best_genome.pkl",
    ]
    config_path = "ai/neat/neat_config.txt"

    for path in genome_candidates:
        if not os.path.exists(path):
            continue
        try:
            brain = NeatNetwork(genome_path=path, config_path=config_path)
            logger(f"Loaded NEAT genome from: {path}")
            return RuntimeNeatAgent(brain)
        except Exception as e:
            logger(f"Failed to load NEAT genome at {path}: {e}")

    logger("No NEAT genome found. Falling back to BasicAgent.")
    return None


# ======================================================================
# 🎮 Game Setup Helper
# ======================================================================


def create_game(ui: UI, player_unit_names: list[str]) -> GameAPI:
    """
    Create a new game session with map, logic, renderer, and units.
    """
    try:
        # --- Initialize core game state ---
        game_state = GameState(
            width=GRID_W,
            height=GRID_H,
            cell_size=CELL_SIZE,
            tile_map=create_random_map(GRID_W, GRID_H),
        )

        # --- Create supporting systems ---
        game_logic = GameLogic(game_state=game_state)
        game_renderer = ui.renderer

        neat_agent = create_runtime_neat_agent()
        if neat_agent is None:
            # You said you don't want to use BasicAgent anymore.
            # So if there's no NEAT genome, we abort game creation.
            raise RuntimeError(
                "No NEAT genome found (best_genome.pkl). "
                "Please run NEAT training first to generate one."
            )

        agent = neat_agent

        # --- Combine everything into the API interface ---
        game_api = GameAPI(
            game_ui=ui,
            renderer=game_renderer,
            game_board=game_state,
            game_logic=game_logic,
            agent=agent,
            team1_type=TeamType.HUMAN,
            team2_type=TeamType.AI,
        )

        # --- Add PLAYER units based on selection ---
        game_api.add_units(
            unit_name_list=player_unit_names,
            team_id=1,
            team=TeamType.HUMAN,
        )

        # --- AI units ---
        ai_draft_names: list[str] = get_ai_draft_units(funds=100)
        game_api.add_units(
            unit_name_list=ai_draft_names,
            team_id=2,
            team=TeamType.AI,
        )

        return game_api
    except Exception as e:
        logger(f"Error during game creation: {e}")
        raise


# ======================================================================
# 🧠 Main Loop
# ======================================================================


def main():
    """Main entry function. Handles initialization, menus, and game loop."""
    try:
        pygame.init()
        pygame.font.init()

        icon_path = get_asset_path("assets/images/game_icon/roman-helmet-32.png")
        try:
            icon = pygame.image.load(icon_path)
            pygame.display.set_icon(icon)
        except Exception as e:
            logger(f"[Warning] Could not load window icon: {e} -> {icon_path}")

        screen = pygame.display.set_mode((SCREEN_W + SIDEBAR_WIDTH, SCREEN_H))
        pygame.display.set_caption("Commanders' Arena")

        font = pygame.font.Font(None, 28)

        game_renderer = Renderer(cell_size=CELL_SIZE)
        ui = UI(cell_size=CELL_SIZE, renderer=game_renderer)

        clock = pygame.time.Clock()

        running = True
        while running:
            play_menu_music()
            choice = ui.start_menu(screen, font)
            if choice == "quit":
                break

            if choice == "start_game":
                selected_units = ui.draft_menu(screen)
                if not selected_units:
                    continue

                create_log_file()

                game_api = create_game(ui, selected_units)
                engine = GameEngine(game_api, screen, font, clock)

                result = engine.run()

                if result is False:
                    running = False
                elif result == "menu":
                    continue
                else:
                    continue

    except Exception as e:
        logger(f"Critical error in main: {e}")
    finally:
        pygame.quit()
        logger("Exited game loop")


if __name__ == "__main__":
    main()

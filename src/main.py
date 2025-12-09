"""
main.py — Entry point for Commanders' Arena
"""

import argparse
from pathlib import Path

import pygame

from ai.agents.agent_factory import AgentFactory
from ai.neat.neat_network import NeatNetwork
from ai.utils.draft_helper import get_ai_draft_units
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
from utils.logging import logger
from utils.music_utils import play_menu_music
from utils.path_utils import get_asset_path

# ======================================================================
# 🔧 Command-line Arguments
# ======================================================================


def parse_args():
    parser = argparse.ArgumentParser(description="Run Commanders' Arena.")
    parser.add_argument(
        "-g",
        "--genome",
        type=str,
        default=None,
        help="Path to a specific NEAT genome to load.",
    )
    parser.add_argument(
        "--agent",
        type=str,
        default="NEATAgent",
        choices=["NEATAgent", "MinimaxAgent", "MCTSAgent"],
        help="Choose which agent to use during training.",
    )
    return parser.parse_args()


# ======================================================================
# 🤖 NEAT Agent Loader
# ======================================================================


def load_neat_agent(genome_override: str | None, agent):
    """
    Load NEAT genome.

    If --genome is just a filename, it will be resolved inside:
        assets/neat/genomes/<file>

    If --genome is a full path, it will be used as-is.
    """

    # Default genome path
    default_path = Path(get_asset_path("assets/neat/genomes/best_genome.pkl"))

    if genome_override:
        override_path = Path(genome_override)

        # Case 1 — user passed only filename: use assets/neat/genomes/<file>
        if not override_path.is_absolute() and len(override_path.parts) == 1:
            genome_path = Path(get_asset_path("assets/neat/genomes")) / override_path
        else:
            # User gave full path
            genome_path = override_path
    else:
        genome_path = default_path
        logger.info(f"🔍 Using DEFAULT genome: {genome_path}")

    config_path = Path(get_asset_path("assets/neat/configs/neat_config.txt"))

    try:
        brain = NeatNetwork(
            genome_path=str(genome_path),
            config_path=str(config_path),
        )
        logger.info(f"Loaded NEAT genome from: {genome_path}")
        agent = AgentFactory.create(agent, brain)
        return agent

    except Exception as e:
        logger.info(f"❌ Failed to load NEAT genome at {genome_path}: {e}")
        return None


# ======================================================================
# 🎮 Game Setup
# ======================================================================


def create_game(ui: UI, player_unit_names: list[str], agent) -> GameAPI:
    """Initialize game systems and return a configured GameAPI."""

    game_state = GameState(
        width=GRID_W,
        height=GRID_H,
        cell_size=CELL_SIZE,
        tile_map=create_random_map(GRID_W, GRID_H),
    )

    game_logic = GameLogic(game_state=game_state)
    game_renderer = ui.renderer

    game_api = GameAPI(
        game_ui=ui,
        renderer=game_renderer,
        game_board=game_state,
        game_logic=game_logic,
        agent=agent,
        team1_type=TeamType.HUMAN,
        team2_type=TeamType.AI,
    )

    # --- Add player units ---
    game_api.add_units(
        unit_name_list=player_unit_names,
        team_id=1,
        team=TeamType.HUMAN,
    )

    # --- Add AI units ---
    ai_units = get_ai_draft_units(funds=100)
    game_api.add_units(
        unit_name_list=ai_units,
        team_id=2,
        team=TeamType.AI,
    )

    return game_api


# ======================================================================
# 🧠 Main Loop
# ======================================================================


def main():
    args = parse_args()

    pygame.init()
    pygame.font.init()

    # Window icon
    icon_path = get_asset_path("assets/images/game_icon/roman-helmet-32.png")
    try:
        icon = pygame.image.load(icon_path)
        pygame.display.set_icon(icon)
    except Exception as e:
        logger.info(f"[Warning] Could not load window icon: {e}")

    # Screen setup
    screen = pygame.display.set_mode((SCREEN_W + SIDEBAR_WIDTH, SCREEN_H))
    pygame.display.set_caption("Commanders' Arena")

    font = pygame.font.Font(None, 28)
    clock = pygame.time.Clock()
    renderer = Renderer(cell_size=CELL_SIZE)
    ui = UI(cell_size=CELL_SIZE, renderer=renderer)

    # Load agent
    agent = load_neat_agent(args.genome, args.agent)
    if agent is None:
        raise RuntimeError(
            "❌ No usable NEAT genome found.\n"
            "Run NEAT training first or specify one using --genome."
        )

    running = True
    while running:
        play_menu_music()
        choice = ui.start_menu(screen, font)

        if choice == "quit":
            break

        if choice == "start_game":
            logger.info("New match started.")

            selected_units = ui.draft_menu(screen)
            if not selected_units:
                continue

            # create_log_file()

            game_api = create_game(ui, selected_units, agent)
            engine = GameEngine(game_api, screen, font, clock)

            result = engine.run()

            if result is False:
                running = False
            elif result == "menu":
                continue
            else:
                continue

    pygame.quit()
    logger.info("Exited game loop")


if __name__ == "__main__":
    main()

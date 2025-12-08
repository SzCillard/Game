# api/simulation_api.py
from __future__ import annotations

from ai.utils.draft_helper import get_ai_draft_units
from api.api import GameAPI
from backend.board import GameState, create_random_map
from backend.logic import GameLogic
from utils.constants import TeamType


class SimulationAPI(GameAPI):
    def __init__(self, game_board):
        super().__init__(
            game_ui=None,
            renderer=None,
            game_board=game_board,
            game_logic=GameLogic(game_board),
            agent=None,
        )

    def clone(self):
        new_board = self.game_board.fast_clone()
        return SimulationAPI(new_board)

    @staticmethod
    def from_snapshot(snapshot: dict) -> "SimulationAPI":
        """
        Rebuild SimulationAPI from a board snapshot.
        Used for multiprocessing workers in MCTS.
        """
        # Create empty board and load snapshot into it
        from backend.board import GameState

        board = GameState.from_snapshot(snapshot)
        sim = SimulationAPI(board)
        return sim

    @staticmethod
    def new_default_game() -> "SimulationAPI":
        """
        Creates a fresh headless simulation with:
        - 8x8 random map
        - AI-draft units for both teams (funds=100)
        - No UI, no renderer
        """

        # Build board
        board = GameState(
            width=8,
            height=8,
            cell_size=64,
            tile_map=create_random_map(8, 8),
        )

        sim = SimulationAPI(board)

        # Draft units for both teams (same as NEAT training)
        team1_units = get_ai_draft_units(funds=100)
        team2_units = get_ai_draft_units(funds=100)

        sim.add_units(team1_units, team_id=1, team=TeamType.AI)
        sim.add_units(team2_units, team_id=2, team=TeamType.AI)

        return sim

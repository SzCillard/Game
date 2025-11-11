# ai/neat/neat_selfplay.py

from typing import TYPE_CHECKING, Any

from ai.agents.neat_agent import NeatAgent
from ai.draft_helper import get_ai_draft_units
from ai.neat.neat_network import NeatNetwork

if TYPE_CHECKING:
    from api.headless_api import HeadlessGameAPI
from backend.board import GameState, create_random_map
from utils.constants import TeamType


class SelfPlaySimulator:
    """
    Simulates a match between two NEAT agents using your existing game logic.
    """

    def __init__(self, config, match_api: "HeadlessGameAPI"):
        self.config = config
        self.match_api = match_api.clone()
        self.agent = NeatAgent()

    def setup_match(self):
        # Create new game board
        game_board = GameState(
            width=8,
            height=8,
            cell_size=64,
            tile_map=create_random_map(8, 8),
        )
        self.match_api.reset(game_board=game_board)

        # Add AI units for both teams
        team1_draft_names = get_ai_draft_units(funds=100)
        team2_draft_names = get_ai_draft_units(funds=100)

        self.match_api.add_units(team1_draft_names, team_id=1, team=TeamType.AI)
        self.match_api.add_units(team2_draft_names, team_id=2, team=TeamType.AI)

    def play_match(self, genome_a, genome_b):
        self.setup_match()

        # Create neural nets
        net_a = NeatNetwork.from_genome(genome_a, self.config)
        net_b = NeatNetwork.from_genome(genome_b, self.config)

        # Run self-play loop using this isolated match_api
        max_turns = 30
        for counter in range(max_turns):
            for team_id, net in [(1, net_a), (2, net_b)]:
                self.agent.execute_next_actions(self.match_api, net, team_id)

                if self.match_api.is_game_over():
                    game_state_snapshot = self.match_api.get_board_snapshot()
                    return self.compute_fitness(counter, game_state_snapshot)

        game_state_snapshot = self.match_api.get_board_snapshot()

        return self.compute_fitness(counter, game_state_snapshot)

    def compute_fitness(
        self,
        turn_number: int,
        game_state_snapshot: dict[str, Any],
    ) -> tuple[float, float]:
        """Return fitness for both teams based on remaining HP."""
        units = game_state_snapshot["units"]

        team1_hp = sum(u["health"] for u in units if u["team_id"] == 1)
        team2_hp = sum(u["health"] for u in units if u["team_id"] == 2)

        total_hp = team1_hp + team2_hp + 1e-6
        return team1_hp / total_hp, team2_hp / total_hp

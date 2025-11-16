from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from ai.agents.neat_agent import NeatAgent
from ai.draft_helper import get_ai_draft_units
from ai.neat.neat_network import NeatNetwork

if TYPE_CHECKING:
    from api.headless_api import HeadlessGameAPI

from backend.board import GameState, create_random_map
from utils.constants import TeamType


class SelfPlaySimulator:
    """
    Simulates a match between two NEAT agents (genome A vs genome B)
    using the existing game logic and a headless API.

    The simulator:
      - Creates a fresh random map for each match.
      - Drafts AI units for both teams.
      - Runs turn-based self-play using a DFS+NN agent.
      - Returns winner, number of turns played, and summary stats
        for both teams (HP, unit counts).
    """

    def __init__(
        self,
        config,
        base_api: "HeadlessGameAPI",
        max_turns: int = 40,
    ) -> None:
        self.config = config
        # we always work on a fresh clone to avoid cross-match contamination
        self.base_api = base_api
        self.max_turns = max_turns

        # For training, use some exploration
        self.agent = NeatAgent(
            max_depth=3,
            max_sets=10,
            max_branching=8,
            exploration_rate=0.2,
        )

        self.match_api: HeadlessGameAPI = self.base_api.clone()

    # ------------------------------------------------------------------
    # Match setup
    # ------------------------------------------------------------------
    def _setup_match(self) -> None:
        """
        Create a new random map and draft units for both teams.
        """
        # Clone the headless API so we have fresh GameLogic + GameState wrapper
        self.match_api = self.base_api.clone()

        # Create new game board
        game_board = GameState(
            width=8,
            height=8,
            cell_size=64,
            tile_map=create_random_map(8, 8),
        )
        self.match_api.reset(game_board=game_board)

        # Add AI units for both teams (keep your current draft logic)
        team1_draft_names = get_ai_draft_units(funds=100)
        team2_draft_names = get_ai_draft_units(funds=100)

        self.match_api.add_units(team1_draft_names, team_id=1, team=TeamType.AI)
        self.match_api.add_units(team2_draft_names, team_id=2, team=TeamType.AI)

    # ------------------------------------------------------------------
    # Helper: compute summary stats for fitness
    # ------------------------------------------------------------------
    def _compute_stats(self) -> Dict[str, Any]:
        """
        Compute simple summary statistics for both teams:
          - total HP per team
          - alive unit counts per team
        """
        snapshot = self.match_api.get_board_snapshot()
        units = snapshot["units"]

        team1 = [u for u in units if u["team_id"] == 1]
        team2 = [u for u in units if u["team_id"] == 2]

        hp1 = sum(u["health"] for u in team1)
        hp2 = sum(u["health"] for u in team2)

        alive1 = len(team1)
        alive2 = len(team2)

        return {
            "hp1": hp1,
            "hp2": hp2,
            "alive1": alive1,
            "alive2": alive2,
        }

    # ------------------------------------------------------------------
    # Main match loop
    # ------------------------------------------------------------------
    def play_match(self, genome_a, genome_b):
        self._setup_match()

        net_a = NeatNetwork.from_genome(genome_a, self.config)
        net_b = NeatNetwork.from_genome(genome_b, self.config)

        turns_played = 0

        for t in range(self.max_turns):
            # --- Team 1 turn ---
            self.match_api.turn_begin_reset(1)
            self.agent.execute_next_actions(self.match_api, net_a, team_id=1)
            if self.match_api.is_game_over():
                turns_played = t + 1
                stats = self._compute_stats()
                return self.match_api.get_winner(), turns_played, stats

            # --- Team 2 turn ---
            self.match_api.turn_begin_reset(2)
            self.agent.execute_next_actions(self.match_api, net_b, team_id=2)
            if self.match_api.is_game_over():
                turns_played = t + 1
                stats = self._compute_stats()
                return self.match_api.get_winner(), turns_played, stats

            turns_played = t + 1

        stats = self._compute_stats()
        winner = self.match_api.get_winner()
        return winner, turns_played, stats

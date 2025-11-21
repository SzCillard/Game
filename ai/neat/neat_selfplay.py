from __future__ import annotations

from typing import TYPE_CHECKING

from ai.agents.neat_agent import NeatAgent
from ai.neat.neat_network import NeatNetwork
from ai.utils.draft_helper import get_ai_draft_units

if TYPE_CHECKING:
    from api.headless_api import HeadlessGameAPI

from backend.board import GameState, create_random_map
from utils.constants import UNIT_STATS, TeamType


class SelfPlaySimulator:
    """
    Simulates a match between two NEAT agents (genome A vs genome B)
    using the existing game logic and a headless API.
    """

    def __init__(
        self,
        config,
        base_api: "HeadlessGameAPI",
        max_turns: int,
    ) -> None:
        self.config = config
        self.base_api = base_api
        self.max_turns = max_turns

        self.agent = NeatAgent(
            max_sets=100,
            max_branching=20,
            exploration_rate=0.2,
        )

        self.match_api: HeadlessGameAPI = self.base_api.clone()

    # ------------------------------------------------------------------
    # Match setup
    # ------------------------------------------------------------------
    def _setup_match(self) -> tuple[list[str], list[str]]:
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

        return team1_draft_names, team2_draft_names

    # ------------------------------------------------------------------
    # Helper: compute summary stats for fitness
    # ------------------------------------------------------------------
    def _compute_stats(
        self, drafted_unit_names: tuple[list[str], list[str]]
    ) -> dict[str, float]:
        """
        Compute simple summary statistics for both teams
        """

        initial_unit_count_team1 = len(drafted_unit_names[0])
        initial_unit_count_team2 = len(drafted_unit_names[1])

        max_hp_team1 = sum(UNIT_STATS[name]["health"] for name in drafted_unit_names[0])
        max_hp_team2 = sum(UNIT_STATS[name]["health"] for name in drafted_unit_names[1])

        snapshot = self.match_api.get_board_snapshot()
        units = snapshot["units"]

        team1 = [u for u in units if u["team_id"] == 1]
        team2 = [u for u in units if u["team_id"] == 2]

        hp1 = sum(u["health"] for u in team1)
        if hp1 == 0:
            hp1 = 1
        hp2 = sum(u["health"] for u in team2)
        if hp2 == 0:
            hp2 = 1

        # gets a small value due to division by 0
        alive1 = len(team1) if len(team1) > 0 else 0.1
        alive2 = len(team2) if len(team2) > 0 else 0.1

        return {
            "initial_unit_count_team1": initial_unit_count_team1,
            "initial_unit_count_team2": initial_unit_count_team2,
            "alive1": alive1,
            "alive2": alive2,
            "max_hp_team1": max_hp_team1,
            "max_hp_team2": max_hp_team2,
            "hp1": hp1,
            "hp2": hp2,
        }

    # ------------------------------------------------------------------
    # Main match loop
    # ------------------------------------------------------------------
    def play_match(self, genome_a, genome_b):
        drafted_unit_names = self._setup_match()

        net_a = NeatNetwork.from_genome(genome_a, self.config)
        net_b = NeatNetwork.from_genome(genome_b, self.config)

        turns_played = 0

        for t in range(self.max_turns):
            # --- Team 1 turn ---
            self.match_api.turn_begin_reset(1)
            self.agent.execute_next_actions(self.match_api, net_a, team_id=1)
            if self.match_api.is_game_over():
                turns_played = t + 1
                stats = self._compute_stats(drafted_unit_names)
                return self.match_api.get_winner(), turns_played, stats

            # --- Team 2 turn ---
            self.match_api.turn_begin_reset(2)
            self.agent.execute_next_actions(self.match_api, net_b, team_id=2)
            if self.match_api.is_game_over():
                turns_played = t + 1
                stats = self._compute_stats(drafted_unit_names)
                return self.match_api.get_winner(), turns_played, stats

            turns_played = t + 1

        stats = self._compute_stats(drafted_unit_names)
        winner = self.match_api.get_winner()
        return winner, turns_played, stats

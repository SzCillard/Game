# ai/neat/neat_selfplay.py
import numpy as np

from ai.draft_helper import get_ai_draft_units
from ai.neat.neat_network import NEATNetwork
from api.api import GameAPI
from backend.board import GameState, create_random_map
from backend.logic import GameLogic
from utils.constants import TeamType


class SelfPlaySimulator:
    """
    Simulates a match between two NEAT agents using your existing game logic.
    """

    def __init__(self, config, game_api: "GameAPI"):
        self.config = config
        self.game_api = game_api

    def play_match(self, genome_a, genome_b):
        """
        Run a single match between two genomes.
        Returns (fitness_a, fitness_b).
        """

        net_a = NEATNetwork.from_genome(genome_a, self.config)
        net_b = NEATNetwork.from_genome(genome_b, self.config)

        # Minimal board
        gs = GameState(
            width=8,
            height=8,
            cell_size=64,
            tile_map=create_random_map(8, 8),
        )
        logic = GameLogic(gs)

        # Add a few test units per team (currently only for one team)
        ai_draft_names: list[str] = get_ai_draft_units(funds=100)

        self.game_api.add_units(ai_draft_names, team=TeamType.AI)

        # Game loop (simplified)
        max_turns = 30
        for _ in range(max_turns):
            for team, net in [(TeamType.PLAYER, net_a), (TeamType.AI, net_b)]:
                state = gs.get_snapshot()  # or logic.get_snapshot()
                inputs = self.extract_features(state, team)
                outputs = net.predict(inputs)
                self.apply_action(outputs, logic, team)

                if logic.is_game_over():
                    return self.compute_fitness(gs)

        return self.compute_fitness(gs)

    def extract_features(self, game_state, team):
        # Same feature encoding as in NEATAgent.encode_state()
        ally_units = [u for u in game_state["units"] if u["team"] == team]
        enemy_units = [u for u in game_state["units"] if u["team"] != team]
        ally_hp = sum(u.health for u in ally_units)
        enemy_hp = sum(u.health for u in enemy_units)
        return np.array([ally_hp / 1000, enemy_hp / 1000])

    def apply_action(self, outputs, logic, team):
        # Simplified — map outputs to high-level action
        action_idx = int(np.argmax(outputs))
        if action_idx == 0:
            logic.move_random(team)
        elif action_idx == 1:
            logic.attack_random(team)

    def compute_fitness(self, gs):
        """Return (player_fitness, ai_fitness)."""
        player_hp = sum(u.health for u in gs.units if u.team == TeamType.PLAYER)
        ai_hp = sum(u.health for u in gs.units if u.team == TeamType.AI)
        total_hp = player_hp + ai_hp + 1e-6
        return player_hp / total_hp, ai_hp / total_hp

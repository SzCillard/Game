# ai/neat/neat_selfplay.py

from ai.agents.neat_agent import NeatAgent
from ai.draft_helper import get_ai_draft_units
from ai.neat.neat_network import NeatNetwork
from api.api import GameAPI
from backend.board import GameState, create_random_map
from utils.constants import TeamType


class SelfPlaySimulator:
    """
    Simulates a match between two NEAT agents using your existing game logic.
    """

    def __init__(self, config, game_api: "GameAPI"):
        self.config = config
        self.game_api = game_api
        self.agent = NeatAgent()

    def play_match(self, genome_a, genome_b):
        """
        Run a single match between two genomes.
        Returns (fitness_a, fitness_b).
        """

        net_a = NeatNetwork.from_genome(genome_a, self.config)
        net_b = NeatNetwork.from_genome(genome_b, self.config)
        # Minimal board
        game_board = GameState(
            width=8,
            height=8,
            cell_size=64,
            tile_map=create_random_map(8, 8),
        )

        # TODO: refactor game to enable two AI agents playing against each other
        # Add a few test units per team (currently only for one team)
        ai_draft_names: list[str] = get_ai_draft_units(funds=100)

        self.game_api.add_units(ai_draft_names, team=TeamType.AI)

        # Game loop
        max_turns = 30
        for _ in range(max_turns):
            for team, net in [(TeamType.PLAYER, net_a), (TeamType.AI, net_b)]:
                # game_state = self.game_api.get_board_snapshot()

                # legal_moves = self.game_api.get_legal_actions(game_state, team)

                self.agent.execute_next_actions(self.game_api, net, team)

                if self.game_api.is_game_over():
                    return self.compute_fitness(game_board)

        return self.compute_fitness(game_board)

    def compute_fitness(self, game_board):
        """Return (player_fitness, ai_fitness)."""
        player_hp = sum(u.health for u in game_board.units if u.team == TeamType.PLAYER)
        ai_hp = sum(u.health for u in game_board.units if u.team == TeamType.AI)
        total_hp = player_hp + ai_hp + 1e-6
        return player_hp / total_hp, ai_hp / total_hp

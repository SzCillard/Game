# ai/neat/neat_agent.py
from typing import Any

import numpy as np

from ai.neat.neat_network import NeatNetwork
from utils.constants import TeamType


class NeatAgent:
    def __init__(self):
        self.brain = None

    def setup_brain(self, brain: NeatNetwork):
        self.brain = brain

    def encode_state(self, game_state: dict[str, Any], team) -> np.ndarray:
        """Extract numerical features for the neural network."""

        ally_units = [u for u in game_state["units"] if u["team"] == TeamType.PLAYER]
        enemy_units = [u for u in game_state["units"] if u["team"] == TeamType.AI]

        ally_count = len(ally_units)
        enemy_count = len(enemy_units)

        # Example features (normalize where possible)
        ally_hp = sum(u.health for u in ally_units)
        enemy_hp = sum(u.health for u in enemy_units)

        # Average position (for positioning heuristics)
        avg_x_ally = np.mean([u.x for u in ally_units]) if ally_units else 0
        avg_y_ally = np.mean([u.y for u in ally_units]) if ally_units else 0
        avg_x_enemy = np.mean([u.x for u in enemy_units]) if enemy_units else 0
        avg_y_enemy = np.mean([u.y for u in enemy_units]) if enemy_units else 0

        # Simple derived feature: distance between army centers
        dist = np.hypot(avg_x_ally - avg_x_enemy, avg_y_ally - avg_y_enemy)

        return np.array(
            [
                team.Value,
                ally_hp / 1000.0,
                enemy_hp / 1000.0,
                ally_count / 10.0,
                enemy_count / 10.0,
                dist / 20.0,
            ]
        )

    def eval_state(self, net: NeatNetwork, game_state: dict[str, Any], team) -> float:
        """Evaluate the game state"""

        encoded_state = self.encode_state(game_state, team)
        prediction = net.predict(encoded_state)
        return prediction[0]

    """
    def select_greedy_action(self, state, brain, team):
        legal_actions = self.game_api.get_legal_actions(state, team)
        best_move = None
        best_score = -1e9

        for move in legal_actions:
            new_state = self.game_api.simulate_action(state, move)
            score = brain.predict(self.encode_state(new_state, team))[0]

            if score > best_score:
                best_score = score
                best_move = move

        return best_move
    """

    def get_next_actions(
        self, game_api, net: NeatNetwork, legal_actions, game_state, team
    ):
        # If no legal moves, do nothing
        if not legal_actions:
            return None

        best_move = None
        best_score = -1e9

        for actions in legal_actions:
            new_state = game_api.simulate_action(game_state, actions)
            score = self.eval_state(net, new_state, team)

            if score > best_score:
                best_score = score
                best_move = actions

        return best_move

    def decode_actions(self, action_idx):
        """Convert output index back into a valid action."""
        actions = ["move_up", "move_down", "attack", "wait"]
        return {"type": actions[action_idx]}

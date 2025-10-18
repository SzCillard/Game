# ai/neat/neat_agent.py
from typing import Any

import numpy as np

from ai.base_agent import BaseAgent
from ai.neat.neat_network import NEATNetwork
from utils.constants import TeamType


class NEATAgent(BaseAgent):
    def __init__(self, genome_path: str, config_path: str):
        super().__init__()
        self.brain = NEATNetwork(genome_path, config_path)

    def choose_action(self, game_state: dict[str, Any]):
        """
        Convert the current game state into neural net inputs,
        then interpret the outputs as an action (move/attack/etc.).
        """
        inputs = self.encode_state(game_state)
        outputs = self.brain.predict(inputs)

        # Example: interpret outputs
        # outputs = [move_up, move_down, attack, wait]
        action_idx = outputs.index(max(outputs))
        return self.decode_action(action_idx, game_state)

    def encode_state(self, game_state: dict[str, Any]) -> np.ndarray:
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
                ally_hp / 1000.0,
                enemy_hp / 1000.0,
                ally_count / 10.0,
                enemy_count / 10.0,
                dist / 20.0,
            ]
        )

    def decode_action(self, action_idx, game_state):
        """Convert output index back into a valid action."""
        actions = ["move_up", "move_down", "attack", "wait"]
        return {"type": actions[action_idx]}

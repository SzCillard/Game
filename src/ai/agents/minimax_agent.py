# ai/neat/neat_agent.py
from typing import Any

import numpy as np

from ai.neat.neat_network import NeatNetwork
from ai.planning.minimax import minimax
from utils.constants import TeamType


class MinimaxAgent:
    def __init__(self):
        self.brain = None

    def setup_brain(self, brain: NeatNetwork):
        self.brain = brain

    def choose_action(self, game_state: dict[str, Any]):
        """
        Convert the current game state into neural net inputs,
        then interpret the outputs as an action (move/attack/etc.).
        """
        """
        inputs = self.encode_state(game_state, team)
        outputs = self.brain.predict(inputs)

        # Example: interpret outputs
        # outputs = [move_up, move_down, attack, wait]
        action_idx = outputs.index(max(outputs))
        return self.decode_action(action_idx, game_state)
        """

    def encode_state(self, game_state: dict[str, Any], team) -> np.ndarray:
        """Extract numerical features for the neural network."""

        ally_units = [u for u in game_state["units"] if u["team"] == TeamType.HUMAN]
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

    def eval_state(self, game_state: dict[str, Any], team) -> float:
        """Evaluate the game state"""
        if self.brain is None:
            raise RuntimeError("Brain has not been set. Call setup_brain() before.")

        encoded_state = self.encode_state(game_state, team)
        prediction = self.brain.predict(encoded_state)
        return prediction[0]

    def get_next_actions(self, game_state, team) -> float:
        actions = minimax(
            game_state,
            depth=2,
            alpha=-1e9,
            beta=1e9,
            evaluator=self,
            is_maximizing=True,
        )
        decoded_actions = decode_actions(actions)  # type: ignore  # noqa: F821
        return decoded_actions

    def decode_actions(self, action_idx):
        """Convert output index back into a valid action."""
        actions = ["move_up", "move_down", "attack", "wait"]
        return {"type": actions[action_idx]}

    def minimax(node, depth, alpha, beta, evaluator, is_maximizing):
        """
        if depth == 0 or node.is_terminal():
            # TODO: game_state_list to store the game states,
            # somehow the nodes need to be stored
            return eval_state(game.get_state_snapshot())

        moves = game.get_legal_moves()
        if is_maximizing:
            value = -1e9
            for move in moves:
                # TODO: legal moves api call, building the legal move tree
                next_state = game.simulate_move(move)
                value = max(
                    value, minimax(next_state, depth - 1, alpha, beta, evaluator, False)
                )
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = 1e9
            for move in moves:
                next_state = game.simulate_move(move)
                value = min(
                    value, minimax(next_state, depth - 1, alpha, beta, evaluator, True)
                )
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value
        """

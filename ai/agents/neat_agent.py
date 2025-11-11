# ai/agents/neat_agent.py

from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from api.headless_api import HeadlessGameAPI

from ai.neat.neat_network import NeatNetwork


class NeatAgent:
    def __init__(self):
        self.brain = None

    def setup_brain(self, brain: NeatNetwork):
        self.brain = brain

    def _encode_state(self, game_state: dict[str, Any], team_id: int) -> np.ndarray:
        """Extract numerical features for the neural network."""

        units = game_state["units"]
        ally_units = []
        enemy_units = []
        for u in units:
            if u["team_id"] == team_id:
                ally_units.append(u)
            else:
                enemy_units.append(u)

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
                team_id,
                ally_hp / 1000.0,
                enemy_hp / 1000.0,
                ally_count / 10.0,
                enemy_count / 10.0,
                dist / 20.0,
            ]
        )

    def _eval_state(
        self, net: NeatNetwork, game_state: dict[str, Any], team_id: int
    ) -> float:
        """Evaluate the game state"""

        encoded_state = self._encode_state(game_state, team_id)
        prediction = net.predict(encoded_state)
        return prediction[0]

    def _decode_actions(self, action_idx):
        """Convert output index back into a valid action."""
        actions = ["move_up", "move_down", "attack", "wait"]
        return {"type": actions[action_idx]}

    def _get_set_of_actions(
        self, game_api: "HeadlessGameAPI", team_id: int, max_sets: int = 10
    ) -> list[list[dict[str, Any]]]:
        """
        Generate up to `max_sets` complete action sequences (sets of actions)
        for the specified team by recursively exploring all legal actions
        from the current game state using depth-first search.

        Each resulting sequence represents a full turn of valid actions
        that can be executed by the given team until no further legal actions
        are available (i.e., an end-of-turn state is reached).

        The search terminates early once `max_sets` sequences have been found.

        Args:
            game_api (Any):
                The game API interface providing methods such as
                `get_board_snapshot()`, `get_legal_actions(state, team)`,
                `clone()`, and `apply_action(action)`.
            team (Any):
                The team identifier (e.g., `TeamType.HUMAN` or `TeamType.AI`)
                for which to generate possible action sequences.
            max_sets (int, optional):
                The maximum number of complete action sequences to generate.
                Defaults to 10.

        Returns:
            list[list[dict[str, Any]]]:
                A list of action sets, where each action set is a list of
                action dictionaries representing one full sequence of
                valid actions for the given team.
        """
        result_sets = []

        def dfs(
            current_actions: list[dict[str, Any]], api_clone: "HeadlessGameAPI"
        ) -> None:
            """
            Recursive depth-first search helper for exploring all possible
            sequences of legal actions from a given game state.

            This function builds action sequences by repeatedly:
            1. Querying legal actions from the current cloned game state.
            2. Applying each possible action on a deep clone of the state.
            3. Recursing until no further legal actions remain (i.e., end of turn).

            Once a leaf node (no legal actions) is reached, the full sequence
            of actions leading to that state is added to the global result set.

            Args:
                current_actions (list[dict[str, Any]]):
                    The list of actions taken so far in the current sequence.
                api_clone (Any):
                    A cloned instance of the game API representing the current
                    simulated game state.
            """
            # Stop if we've collected enough sets
            if len(result_sets) >= max_sets:
                return

            # Get all legal actions for this team
            # TODO: refactor to use team_id
            legal_actions = api_clone.get_legal_actions(team_id)

            # If there are no actions left (leaf)
            if not legal_actions or api_clone.check_turn_end(team_id):
                result_sets.append(current_actions)
                return

            # For each action, simulate and recurse
            for action in legal_actions:
                if len(result_sets) >= max_sets:
                    break  # width limit reached

                # Clone the state
                next_clone = api_clone.clone()

                # Try to apply the action
                success = next_clone.apply_action(action)
                if not success:
                    continue

                # Continue DFS deeper
                dfs(current_actions + [action], next_clone)

        # Start exploration from the initial game state
        dfs([], game_api)

        return result_sets

    def _simulate_actions(
        self, game_api: "HeadlessGameAPI", actions: list[dict[str, Any]]
    ):
        api_clone = game_api.clone()
        for action in actions:
            api_clone.apply_action(action)
        return api_clone.get_board_snapshot()

    def _get_next_actions(
        self, game_api: "HeadlessGameAPI", net: NeatNetwork, team_id
    ) -> list[dict]:
        all_action_sets = self._get_set_of_actions(game_api, team_id)
        best_score = -1e9
        best_set = []

        for actions in all_action_sets:
            new_state = self._simulate_actions(game_api, actions)
            score = self._eval_state(net, new_state, team_id)
            if score > best_score:
                best_score = score
                best_set = actions

        return best_set

    def execute_next_actions(
        self, game_api: "HeadlessGameAPI", net: NeatNetwork, team_id: int
    ):
        actions = self._get_next_actions(game_api, net, team_id)
        for action in actions:
            game_api.apply_action(action)

    """
    def choose_actions_greedily(self, game_api, net, team):
        state = game_api.get_board_snapshot()
        legal_actions = game_api.get_legal_actions(state, team)
        best_action = None
        best_score = -float("inf")

        for action in legal_actions:
            clone = game_api.clone()
            clone.apply_action(action)

            new_state = clone.get_board_snapshot()
            score = self.eval_state(net, new_state, team)

            if score > best_score:
                best_score = score
                best_action = action

        return [best_action] if best_action else []
    """

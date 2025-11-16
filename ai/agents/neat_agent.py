# ai/agents/neat_agent.py

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Dict, List

import numpy as np

if TYPE_CHECKING:
    from ai.neat.neat_network import NeatNetwork
    from api.api import GameAPI  # for type hints
    from api.headless_api import HeadlessGameAPI


class NeatAgent:
    """
    NEAT-powered agent that uses a depth-limited DFS over action sequences.

    Flow:
      1. From the current game state, generate up to `max_sets` different
         action sequences for `team_id` using DFS, limited by:
           - max_depth: maximum number of actions in a sequence
           - max_branching: max actions expanded per node
      2. For each sequence, simulate it on a cloned game state.
      3. Encode the resulting state into a feature vector.
      4. Ask the NEAT network to score that state.
      5. Execute the best-scoring sequence on the real game_api.
    """

    def __init__(
        self,
        max_depth: int = 3,
        max_sets: int = 10,
        max_branching: int = 8,
    ) -> None:
        self.brain: NeatNetwork | None = None
        self.max_depth = max_depth
        self.max_sets = max_sets
        self.max_branching = max_branching

    # ------------------------------------------------------------------
    # Brain
    # ------------------------------------------------------------------
    def setup_brain(self, brain: NeatNetwork) -> None:
        """Attach a NEAT network instance."""
        self.brain = brain

    # ------------------------------------------------------------------
    # State Encoding & Evaluation
    # ------------------------------------------------------------------
    def _encode_state(self, game_state: Dict[str, Any], team_id: int) -> np.ndarray:
        """
        Extract numerical features for the neural network.

        Current simple feature set (can be extended later):
          - team_id (1 or 2)
          - total ally HP (normalized)
          - total enemy HP (normalized)
          - ally unit count (normalized)
          - enemy unit count (normalized)
          - distance between average ally position and average enemy position
        """
        units = game_state["units"]
        ally_units: List[Dict[str, Any]] = []
        enemy_units: List[Dict[str, Any]] = []

        for u in units:
            if u["team_id"] == team_id:
                ally_units.append(u)
            else:
                enemy_units.append(u)

        ally_count = len(ally_units)
        enemy_count = len(enemy_units)

        ally_hp = sum(u["health"] for u in ally_units)
        enemy_hp = sum(u["health"] for u in enemy_units)

        avg_x_ally = np.mean([u["x"] for u in ally_units]) if ally_units else 0.0
        avg_y_ally = np.mean([u["y"] for u in ally_units]) if ally_units else 0.0
        avg_x_enemy = np.mean([u["x"] for u in enemy_units]) if enemy_units else 0.0
        avg_y_enemy = np.mean([u["y"] for u in enemy_units]) if enemy_units else 0.0

        dist = float(np.hypot(avg_x_ally - avg_x_enemy, avg_y_ally - avg_y_enemy))

        # Simple normalization constants (tunable)
        return np.array(
            [
                float(team_id),
                ally_hp / 1000.0,
                enemy_hp / 1000.0,
                ally_count / 10.0,
                enemy_count / 10.0,
                dist / 20.0,
            ],
            dtype=np.float32,
        )

    def _eval_state(
        self, net: NeatNetwork, game_state: Dict[str, Any], team_id: int
    ) -> float:
        """Ask the NEAT network to score a board snapshot."""
        encoded_state = self._encode_state(game_state, team_id)
        prediction = net.predict(encoded_state)
        # Assuming predict returns a 1D array-like; take the first output.
        return float(prediction[0])

    # ------------------------------------------------------------------
    # DFS Action Sequence Generation
    # ------------------------------------------------------------------
    def _generate_action_sequences(
        self,
        game_api: "GameAPI | HeadlessGameAPI",
        team_id: int,
    ) -> List[List[Dict[str, Any]]]:
        """
        Generate up to `self.max_sets` action sequences for team_id using
        depth-limited DFS.

        Constraints:
          - Depth limited by self.max_depth (max number of actions).
          - At each node, only explore up to self.max_branching actions.
          - A sequence ends when:
              * depth == max_depth, or
              * check_turn_end(team_id) is True, or
              * there are no legal actions.
        """
        result_sets: List[List[Dict[str, Any]]] = []

        def dfs(
            api_state: "GameAPI | HeadlessGameAPI",
            depth: int,
            current_actions: List[Dict[str, Any]],
        ) -> None:
            # Stop if we already collected enough sequences
            if len(result_sets) >= self.max_sets:
                return

            # If turn is over or depth limit reached, record this sequence
            if depth >= self.max_depth or api_state.check_turn_end(team_id):
                result_sets.append(list(current_actions))
                return

            legal_actions = api_state.get_legal_actions(team_id)

            # No actions: treat this as a leaf sequence
            if not legal_actions:
                result_sets.append(list(current_actions))
                return

            # Randomize & prune branching factor
            random.shuffle(legal_actions)
            if len(legal_actions) > self.max_branching:
                legal_actions = legal_actions[: self.max_branching]

            for action in legal_actions:
                if len(result_sets) >= self.max_sets:
                    break

                next_state = api_state.clone()
                success = next_state.apply_action(action)
                if not success:
                    continue

                dfs(
                    next_state,
                    depth + 1,
                    current_actions + [action],
                )

        # Start DFS from a clone of the current state so we never mutate the real game
        dfs(game_api.clone(), 0, [])

        # Guarantee at least one (possibly empty) sequence
        if not result_sets:
            result_sets.append([])

        return result_sets

    # ------------------------------------------------------------------
    # Utilities: simulate & choose best sequence
    # ------------------------------------------------------------------
    def _simulate_actions(
        self,
        game_api: "GameAPI | HeadlessGameAPI",
        actions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Simulate the given action sequence on a cloned game_api and return
        the resulting board snapshot.
        """
        api_clone = game_api.clone()
        for action in actions:
            api_clone.apply_action(action)
        return api_clone.get_board_snapshot()

    def _get_next_actions(
        self,
        game_api: "GameAPI | HeadlessGameAPI",
        net: NeatNetwork,
        team_id: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate candidate action sequences with DFS, score each resulting
        state with the NEAT network, and return the best action sequence.
        """
        all_action_sets = self._generate_action_sequences(game_api, team_id)

        best_score = -1e9
        best_set: List[Dict[str, Any]] = []

        for actions in all_action_sets:
            new_state = self._simulate_actions(game_api, actions)
            score = self._eval_state(net, new_state, team_id)
            if score > best_score:
                best_score = score
                best_set = actions

        return best_set

    # ------------------------------------------------------------------
    # Public: execute chosen actions on the real game_api
    # ------------------------------------------------------------------
    def execute_next_actions(
        self,
        game_api: "GameAPI | HeadlessGameAPI",
        net: NeatNetwork,
        team_id: int,
    ) -> None:
        """
        Entry point used by SelfPlaySimulator & runtime agents:
          - Picks the best sequence of actions using DFS+NN.
          - Applies them to the real game_api.
        """
        if net is None and self.brain is None:
            # No brain attached; do nothing
            return

        brain = net if net is not None else self.brain
        actions = self._get_next_actions(game_api, brain, team_id)
        for action in actions:
            game_api.apply_action(action)

    # ------------------------------------------------------------------
    # (Optional) Greedy single-step chooser kept as reference:
    # ------------------------------------------------------------------
    """
    def choose_actions_greedily(self, game_api, net, team_id):
        snapshot = game_api.get_board_snapshot()
        legal_actions = game_api.get_legal_actions(team_id)
        best_action = None
        best_score = -float("inf")

        for action in legal_actions:
            clone = game_api.clone()
            clone.apply_action(action)
            new_state = clone.get_board_snapshot()
            score = self._eval_state(net, new_state, team_id)
            if score > best_score:
                best_score = score
                best_action = action

        return [best_action] if best_action else []
    """

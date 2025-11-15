# ai/agents/runtime_neat_agent.py

from __future__ import annotations

import copy
from typing import Any, Dict, List

import numpy as np

from ai.neat.neat_network import NeatNetwork
from backend.board import GameState
from backend.logic import GameLogic
from utils.logging import logger


class _SimulationAPI:
    """
    Minimal headless game API used only for NEAT planning in runtime.

    It wraps a GameState + GameLogic, exposes just the methods
    needed by the DFS planner:

    - clone()
    - get_legal_actions(team_id)
    - check_turn_end(team_id)
    - apply_action(action)
    - get_board_snapshot()
    """

    def __init__(self, game_board: GameState):
        self.game_board: GameState = game_board
        self.game_logic: GameLogic = GameLogic(game_board)

    def clone(self) -> "_SimulationAPI":
        board_copy = copy.deepcopy(self.game_board)
        return _SimulationAPI(board_copy)

    def get_legal_actions(self, team_id: int) -> List[Dict[str, Any]]:
        return self.game_logic.get_legal_actions(team_id)

    def check_turn_end(self, team_id: int) -> bool:
        return self.game_logic.check_turn_end(team_id)

    def apply_action(self, action: Dict[str, Any]) -> bool:
        return self.game_logic.apply_action(action)

    def get_board_snapshot(self) -> Dict[str, Any]:
        return self.game_board.get_snapshot()


class RuntimeNeatAgent:
    """
    Runtime NEAT agent used when playing Human vs AI.

    ⚙ Uses:
    - DFS over action sequences for a full turn
    - NEAT network (best genome) as state evaluator
    - Very similar logic to the training NEAT agent,
      but isolated for runtime, so training code stays untouched.
    """

    def __init__(self, brain: NeatNetwork) -> None:
        self.brain = brain

    # ------------------------------
    # State encoding / evaluation
    # ------------------------------

    def _encode_state(self, game_state: Dict[str, Any], team_id: int) -> np.ndarray:
        """
        Extract numerical features for the neural network from a board snapshot.

        game_state: dict returned by GameState.get_snapshot()
        team_id: 1 or 2 (player side)
        """
        units = game_state["units"]
        ally_units = [u for u in units if int(u["team_id"]) == int(team_id)]
        enemy_units = [u for u in units if int(u["team_id"]) != int(team_id)]

        ally_count = len(ally_units)
        enemy_count = len(enemy_units)

        # Total HP
        ally_hp = sum(u["health"] for u in ally_units) if ally_units else 0
        enemy_hp = sum(u["health"] for u in enemy_units) if enemy_units else 0

        # Average positions
        def _avg_xy(unit_list: List[Dict[str, Any]]) -> tuple[float, float]:
            if not unit_list:
                return 0.0, 0.0
            xs = [u["x"] for u in unit_list]
            ys = [u["y"] for u in unit_list]
            return float(np.mean(xs)), float(np.mean(ys))

        avg_x_ally, avg_y_ally = _avg_xy(ally_units)
        avg_x_enemy, avg_y_enemy = _avg_xy(enemy_units)

        # Distance between "centers of mass"
        dist = np.hypot(avg_x_ally - avg_x_enemy, avg_y_ally - avg_y_enemy)

        # Very simple normalization; you can tune later
        return np.array(
            [
                float(team_id),
                ally_hp / 1000.0,
                enemy_hp / 1000.0,
                ally_count / 10.0,
                enemy_count / 10.0,
                dist / 20.0,
            ],
            dtype=float,
        )

    def _eval_state(self, snapshot: Dict[str, Any], team_id: int) -> float:
        encoded = self._encode_state(snapshot, team_id)
        prediction = self.brain.predict(encoded)
        return float(prediction[0])

    # ------------------------------
    # DFS over action sequences
    # ------------------------------

    def _generate_action_sets(
        self,
        base_api: _SimulationAPI,
        team_id: int,
        max_sets: int = 10,
    ) -> List[List[Dict[str, Any]]]:
        """
        Depth-first enumeration of action sequences (full turn for team_id).
        Stops after collecting max_sets sequences.
        """
        result_sets: List[List[Dict[str, Any]]] = []

        def dfs(
            current_actions: List[Dict[str, Any]], api_clone: _SimulationAPI
        ) -> None:
            if len(result_sets) >= max_sets:
                return

            legal_actions = api_clone.get_legal_actions(team_id)

            # Leaf: no actions or turn ended
            if not legal_actions or api_clone.check_turn_end(team_id):
                result_sets.append(current_actions)
                return

            for action in legal_actions:
                if len(result_sets) >= max_sets:
                    break

                next_clone = api_clone.clone()
                success = next_clone.apply_action(action)
                if not success:
                    continue

                dfs(current_actions + [action], next_clone)

        dfs([], base_api)
        return result_sets

    def _simulate_action_set(
        self,
        base_api: _SimulationAPI,
        actions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Apply a sequence of actions to a fresh clone and return the resulting snapshot.
        """
        api_clone = base_api.clone()
        for action in actions:
            api_clone.apply_action(action)
        return api_clone.get_board_snapshot()

    def _plan_turn_actions(
        self,
        game_api: Any,  # GameAPI-like object (has .game_board and .apply_action)
        team_id: int,
        max_sets: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        From the REAL game_api, build a simulated headless copy and run DFS
        to choose the best full-turn action sequence.
        """
        # Build the simulation base from a deep copy of the current board
        real_board: GameState = game_api.game_board  # using internal attribute
        sim_board = copy.deepcopy(real_board)
        sim_api = _SimulationAPI(sim_board)
        logger("Neat agent generate action sets")
        all_sets = self._generate_action_sets(sim_api, team_id, max_sets=max_sets)
        if not all_sets:
            return []

        best_score = -1e9
        best_set: List[Dict[str, Any]] = []

        for actions in all_sets:
            snapshot = self._simulate_action_set(sim_api, actions)
            score = self._eval_state(snapshot, team_id)
            if score > best_score:
                best_score = score
                best_set = actions

        return best_set

    # ------------------------------
    # Public API used by GameAPI
    # ------------------------------

    def play_turn(self, game_api: Any, team_id: int) -> None:
        """
        Decide and apply a full turn of actions for team_id onto the REAL game_api.
        """
        logger("Neat agent plays turn")
        actions = self._plan_turn_actions(game_api, team_id)
        logger("Neat agent found the best actions")

        for action in actions:
            game_api.apply_action(action)

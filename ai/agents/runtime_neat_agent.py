from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from ai.agents.dfs_planner import DfsTurnPlanner
from ai.neat.neat_network import NeatNetwork
from backend.board import GameState
from utils.logging import logger


class RuntimeNeatAgent:
    """
    Runtime NEAT agent used when playing Human vs AI.

    Uses:
      - Shared DfsTurnPlanner for full-turn search
      - NEAT network (best genome) as a state evaluator
    """

    def __init__(self, brain: NeatNetwork) -> None:
        self.brain = brain
        # No exploration at runtime – make behaviour deterministic
        self.planner = DfsTurnPlanner(
            max_depth=3,
            max_sets=10,
            max_branching=8,
            exploration_rate=0.0,
        )

    # ------------------------------
    # State encoding / evaluation
    # ------------------------------
    def _encode_state(self, game_state: Dict[str, Any], team_id: int) -> np.ndarray:
        units = game_state["units"]
        ally_units = [u for u in units if int(u["team_id"]) == int(team_id)]
        enemy_units = [u for u in units if int(u["team_id"]) != int(team_id)]

        ally_count = len(ally_units)
        enemy_count = len(enemy_units)

        ally_hp = sum(u["health"] for u in ally_units) if ally_units else 0
        enemy_hp = sum(u["health"] for u in enemy_units) if enemy_units else 0

        def _avg_xy(unit_list: List[Dict[str, Any]]) -> tuple[float, float]:
            if not unit_list:
                return 0.0, 0.0
            xs = [u["x"] for u in unit_list]
            ys = [u["y"] for u in unit_list]
            return float(np.mean(xs)), float(np.mean(ys))

        avg_x_ally, avg_y_ally = _avg_xy(ally_units)
        avg_x_enemy, avg_y_enemy = _avg_xy(enemy_units)

        dist = float(np.hypot(avg_x_ally - avg_x_enemy, avg_y_ally - avg_y_enemy))

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
    # Public API used by GameAPI
    # ------------------------------
    def play_turn(self, game_api: Any, team_id: int) -> None:
        """
        Decide and apply a full turn of actions for team_id onto the REAL game_api.
        """
        logger("Neat agent planning turn...")
        real_board: GameState = game_api.game_board

        actions = self.planner.plan_turn(
            real_board,
            team_id,
            eval_fn=lambda snapshot: self._eval_state(snapshot, team_id),
        )
        logger(f"Neat agent chose {len(actions)} actions for this turn")

        for action in actions:
            game_api.apply_action(action)

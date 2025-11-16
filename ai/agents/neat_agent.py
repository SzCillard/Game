from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

import numpy as np

if TYPE_CHECKING:
    pass


from ai.planning.full_turn_dfs import FullTurnDFS


class NeatAgent:
    def __init__(self, max_sets=12, max_branching=7, exploration_rate=0.2):
        self.brain = None
        self.planner = FullTurnDFS(
            max_sets=max_sets,
            max_branching=max_branching,
            exploration_rate=exploration_rate,
        )

    def setup_brain(self, brain):
        self.brain = brain

    # ------------------------------------------------------------------
    # State Encoding & Evaluation
    # ------------------------------------------------------------------
    def _encode_state(self, game_state: Dict[str, Any], team_id: int) -> np.ndarray:
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

    def _eval(self, net, snapshot, team_id):
        state = self._encode_state(snapshot, team_id)
        return float(net.predict(state)[0])

    def execute_next_actions(self, game_api, net, team_id):
        board = game_api.game_board

        actions = self.planner.plan(
            board,
            team_id,
            eval_fn=lambda snap: self._eval(net, snap, team_id),
        )

        for act in actions:
            game_api.apply_action(act)

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from ai.neat.neat_network import NeatNetwork
from ai.planning.full_turn_dfs import FullTurnDFS


class RuntimeNeatAgent:
    def __init__(self, brain: NeatNetwork):
        self.brain = brain
        self.planner = FullTurnDFS(
            max_sets=12,
            max_branching=7,
            exploration_rate=0.0,  # no randomness during gameplay
        )

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

    def _eval(self, snapshot, team_id):
        return float(self.brain.predict(self._encode_state(snapshot, team_id))[0])

    def play_turn(self, game_api, team_id: int):
        board = game_api.game_board
        actions = self.planner.plan(
            board,
            team_id,
            eval_fn=lambda snap: self._eval(snap, team_id),
        )

        if not actions:
            # fallback: turn ends or wait-all
            legal = game_api.get_legal_actions(team_id)
            if legal:
                actions = []
                seen = set()
                for a in legal:
                    uid = a["unit_id"]
                    if uid not in seen:
                        seen.add(uid)
                        actions.append({"unit_id": uid, "type": "wait", "target": None})

        for act in actions:
            game_api.apply_action(act)

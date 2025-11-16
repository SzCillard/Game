from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

import numpy as np

from ai.agents.dfs_planner import DfsTurnPlanner
from ai.neat.neat_network import NeatNetwork

if TYPE_CHECKING:
    from api.api import GameAPI
    from api.headless_api import HeadlessGameAPI


class NeatAgent:
    """
    NEAT-powered agent used during training self-play.

    Uses the shared DfsTurnPlanner so its behaviour matches RuntimeNeatAgent.
    """

    def __init__(
        self,
        max_depth: int = 3,
        max_sets: int = 10,
        max_branching: int = 8,
        exploration_rate: float = 0.2,
    ) -> None:
        self.brain: NeatNetwork | None = None
        self.planner = DfsTurnPlanner(
            max_depth=max_depth,
            max_sets=max_sets,
            max_branching=max_branching,
            exploration_rate=exploration_rate,
        )

    def setup_brain(self, brain: NeatNetwork) -> None:
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

    def _eval_state(
        self, net: NeatNetwork, game_state: Dict[str, Any], team_id: int
    ) -> float:
        encoded_state = self._encode_state(game_state, team_id)
        prediction = net.predict(encoded_state)
        return float(prediction[0])

    # ------------------------------------------------------------------
    # Public: used by SelfPlaySimulator
    # ------------------------------------------------------------------
    def execute_next_actions(
        self,
        game_api: "GameAPI | HeadlessGameAPI",
        net: NeatNetwork,
        team_id: int,
    ) -> None:
        """
        Entry point used by SelfPlaySimulator:
          - plans one full turn for team_id,
          - applies actions to the provided game_api.
        """
        brain = net if net is not None else self.brain
        if brain is None:
            return

        real_board = game_api.game_board

        actions = self.planner.plan_turn(
            real_board,
            team_id,
            eval_fn=lambda snapshot: self._eval_state(brain, snapshot, team_id),
        )

        for action in actions:
            game_api.apply_action(action)

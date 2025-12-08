from __future__ import annotations

from typing import TYPE_CHECKING

from ai.neat.neat_network import NeatNetwork
from ai.utils.nn_utils import encode_state

if TYPE_CHECKING:
    pass


from ai.planning.action_planning import ActionPlannerReversible


class NeatAgent:
    def __init__(
        self, brain: NeatNetwork, max_sets=500, max_branching=14, exploration_rate=0.05
    ):
        self.brain = brain
        self.planner = ActionPlannerReversible(
            max_sets=max_sets,
            max_branching=max_branching,
            exploration_rate=exploration_rate,
        )

    def setup_brain(self, brain):
        self.brain = brain

    # ------------------------------------------------------------------
    # State Encoding & Evaluation
    # ------------------------------------------------------------------

    def _eval(self, snapshot, team_id):
        state = encode_state(snapshot, team_id)
        return float(self.brain.predict(state)[0])

    def execute_next_actions(self, game_api, team_id):
        board = game_api.game_board

        actions = self.planner.plan(
            board,
            team_id,
            eval_fn=lambda snap: self._eval(snap, team_id),
        )

        for act in actions:
            game_api.apply_action(act)

    def play_turn(self, game_api, team_id: int):
        self.execute_next_actions(game_api=game_api, team_id=team_id)

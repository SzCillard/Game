from __future__ import annotations

from ai.neat.neat_network import NeatNetwork
from ai.planning.full_turn_dfs import FullTurnDFS
from ai.utils.nn_utils import encode_state


class RuntimeNeatAgent:
    def __init__(self, brain: NeatNetwork):
        self.brain = brain
        self.planner = FullTurnDFS(
            max_sets=30,
            max_branching=10,
            exploration_rate=0.0,
        )

    # ------------------------------
    # State encoding / evaluation
    # ------------------------------

    def _eval(self, snapshot, team_id):
        return float(self.brain.predict(encode_state(snapshot, team_id))[0])

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

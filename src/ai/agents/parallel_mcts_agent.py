from __future__ import annotations

import math
import random
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

from ai.neat.neat_network import NeatNetwork
from ai.planning.action_planning import ActionPlannerReversible
from ai.utils.nn_utils import encode_state
from api.simulation_api import SimulationAPI
from utils.logging import logger


@dataclass
class _MCTSChildStats:
    sequence: list[dict]
    visits: int = 0
    value_sum: float = 0.0

    @property
    def q_value(self) -> float:
        return self.value_sum / self.visits if self.visits > 0 else 0.0


class MCTSAgent:
    def __init__(
        self,
        brain: NeatNetwork,
        dfs_action_sets_limit=200,
        dfs_branching_limit=20,
        max_root_children=8,
        iterations=80,
        rollout_turns=2,
        c_puct=1.4,
        max_workers=4,  # 🔥 NEW: number of parallel processes
    ):
        self.brain = brain
        self.max_root_children = max_root_children
        self.iterations = iterations
        self.rollout_turns = rollout_turns
        self.c_puct = c_puct
        self.max_workers = max_workers  # 🔥 store worker count

        self.planner = ActionPlannerReversible(
            dfs_action_sets_limit=dfs_action_sets_limit,
            dfs_branching_limit=dfs_branching_limit,
            exploration_rate=0.0,
        )

    # ----------------------------------------------------------------------
    # STATIC WORKER FUNCTION  🔥 PARALLEL
    # ----------------------------------------------------------------------
    @staticmethod
    def _rollout_worker(
        snapshot: dict,
        sequence: list[dict],
        team_id: int,
        rollout_turns: int,
        brain_weights: bytes,
    ) -> float:
        """
        Worker process:
        - rebuild SimulationAPI from snapshot
        - rebuild NEAT brain from bytes
        - apply the selected root sequence
        - simulate rollout_turns random full turns
        - return final NEAT evaluation
        """

        # --- rebuild SimulationAPI ---
        sim = SimulationAPI.from_snapshot(snapshot)

        opponent = 1 if team_id == 2 else 2

        sim.start_turn(team_id)
        for act in sequence:
            sim.apply_action(act)
            if sim.is_game_over():
                return 0.0

        if not sim.is_game_over():
            sim.start_turn(opponent)

        # --- rebuild brain ---
        brain = NeatNetwork.restore(brain_weights)

        # --- rollout ---
        for _ in range(rollout_turns):
            if sim.is_game_over():
                break

            sim.start_turn(opponent)
            while not sim.check_turn_end(opponent):
                legal = sim.get_legal_actions(opponent)
                if not legal:
                    break
                sim.apply_action(random.choice(legal))

            if sim.is_game_over():
                break

            sim.start_turn(team_id)
            while not sim.check_turn_end(team_id):
                legal = sim.get_legal_actions(team_id)
                if not legal:
                    break
                sim.apply_action(random.choice(legal))

        # --- evaluate final state ---
        state = encode_state(sim.get_board_snapshot(), team_id)
        return float(brain.predict(state)[0])

    # ----------------------------------------------------------------------
    # NEAT evaluation helper
    # ----------------------------------------------------------------------
    def _eval_snapshot(self, snapshot, team_id):
        state = encode_state(snapshot, team_id)
        return float(self.brain.predict(state)[0])

    # ----------------------------------------------------------------------
    # Generate/prune root sequences
    # ----------------------------------------------------------------------
    def _generate_root_moves(self, game_board, team_id):
        sequences = self.planner.plan_sequences(game_board, team_id)
        if not sequences:
            return []

        sim_root = SimulationAPI(game_board.fast_clone())
        sim_root.start_turn(team_id)

        scored = []
        for seq in sequences:
            replay = sim_root.clone()
            replay.start_turn(team_id)
            for act in seq:
                replay.apply_action(act)
            val = self._eval_snapshot(replay.get_board_snapshot(), team_id)
            scored.append((seq, val))

        scored.sort(key=lambda x: x[1], reverse=True)
        scored = scored[: self.max_root_children]

        return [_MCTSChildStats(sequence=seq) for (seq, _) in scored]

    # ----------------------------------------------------------------------
    # UCB1 selection
    # ----------------------------------------------------------------------
    def _select_child_ucb(self, children, total_visits):
        log_n = math.log(total_visits + 1.0)
        best_idx = 0
        best_score = -1e9

        for i, ch in enumerate(children):
            if ch.visits == 0:
                ucb = float("inf")
            else:
                ucb = ch.q_value + self.c_puct * math.sqrt(log_n / ch.visits)

            if ucb > best_score:
                best_score = ucb
                best_idx = i

        return best_idx

    # ----------------------------------------------------------------------
    # Main entry: play turn WITH PARALLEL ROLLOUTS
    # ----------------------------------------------------------------------
    def execute_next_actions(self, game_api, team_id):
        # generate root sequences
        root_children = self._generate_root_moves(game_api.game_board, team_id)
        if not root_children:
            return

        # snapshot for workers
        initial_snapshot = game_api.game_board.get_snapshot()

        # serialize NEAT brain once
        brain_bytes = self.brain.serialize()

        total_visits = 0
        pending = []

        logger.info(f"[MCTS] Running {self.iterations} parallel iterations...")

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            for _ in range(self.iterations):
                # SELECT
                idx = self._select_child_ucb(root_children, total_visits)
                child = root_children[idx]

                # DISPATCH WORK TO PROCESS  🔥 PARALLEL
                future = executor.submit(
                    MCTSAgent._rollout_worker,
                    initial_snapshot,
                    child.sequence,
                    team_id,
                    self.rollout_turns,
                    brain_bytes,
                )
                pending.append((idx, future))

            # COLLECT RESULTS
            for idx, future in pending:
                value = future.result()

                ch = root_children[idx]
                ch.visits += 1
                ch.value_sum += value
                total_visits += 1

        # choose best root child
        best_child = max(root_children, key=lambda c: (c.visits, c.q_value))

        # execute
        for act in best_child.sequence:
            game_api.apply_action(act)

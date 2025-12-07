from __future__ import annotations

import time
from math import inf
from typing import Any

from ai.neat.neat_network import NeatNetwork
from ai.planning.action_planning import ActionPlannerReversible
from ai.utils.nn_utils import encode_state
from api.simulation_api import SimulationAPI
from utils.logging import logger


class MinimaxAgent:
    """
    Minimax-based agent that searches over *full-turn* action sequences.
    Uses SimulationAPI for simulation so we never clone UI / renderer / pygame objects.
    """

    def __init__(
        self,
        brain: NeatNetwork,
        depth: int = 2,
        max_sets: int = 200,
        max_branching: int = 12,
        child_limit: int = 6,
    ) -> None:
        self.depth = depth
        self.child_limit = child_limit

        self.planner = ActionPlannerReversible(
            max_sets=max_sets,
            max_branching=max_branching,
            exploration_rate=0.0,
        )

        self.brain = brain

        logger.info(
            f"[MinimaxAgent] Initialized (depth={depth}, "
            f"max_sets={max_sets}, max_branching={max_branching}, "
            f"child_limit={child_limit})"
        )

    # ----------------------------------------------------------------------
    # Evaluation
    # ----------------------------------------------------------------------
    def _eval_snapshot(self, snapshot: dict, team_id: int) -> float:
        state = encode_state(snapshot, team_id)
        return float(self.brain.predict(state)[0])

    # ----------------------------------------------------------------------
    # Sequence scoring (for pruning)
    # ----------------------------------------------------------------------
    def _score_sequences(
        self,
        sim,
        acting_team: int,
        sequences: list[list[dict]],
        eval_team: int,
    ) -> list[tuple[list[dict], float]]:
        logger.debug(
            f"[MinimaxAgent] Scoring {len(sequences)} sequences for team {acting_team}"
        )

        scored = []
        start = time.time()

        for idx, seq in enumerate(sequences):
            replay = sim.clone()
            replay.start_turn(acting_team)

            for act in seq:
                replay.apply_action(act)

            score = self._eval_snapshot(replay.get_board_snapshot(), eval_team)
            scored.append((seq, score))

            logger.debug(
                f"[MinimaxAgent] Seq #{idx} | len={len(seq)} | score={score:.4f}"
            )

        scored.sort(key=lambda x: x[1], reverse=True)

        if self.child_limit:
            scored = scored[: self.child_limit]

        logger.info(
            f"[MinimaxAgent] Sequence scoring done "
            f"({len(scored)} kept, {time.time() - start:.3f}s)"
        )
        return scored

    # ----------------------------------------------------------------------
    # Child expansion
    # ----------------------------------------------------------------------
    def _get_children(
        self,
        sim,
        acting_team: int,
        eval_team: int,
    ) -> list[tuple[list[dict], Any]]:
        logger.debug(f"[MinimaxAgent] Expanding children (team={acting_team})")

        start = time.time()
        sequences = self.planner.plan_all_sequences(sim.game_board, acting_team)

        logger.info(
            f"[MinimaxAgent] Generated {len(sequences)} full-turn sequences "
            f"for team {acting_team}"
        )

        if not sequences:
            return []

        if len(sequences) > 100:
            logger.warning(
                f"[MinimaxAgent] ⚠ HIGH SEQUENCE COUNT ({len(sequences)}) → slow search"
            )

        scored = self._score_sequences(sim, acting_team, sequences, eval_team)

        opponent = 1 if acting_team == 2 else 2
        children = []

        for seq, _ in scored:
            replay = sim.clone()
            replay.start_turn(acting_team)

            for act in seq:
                replay.apply_action(act)

            if not replay.is_game_over():
                replay.start_turn(opponent)

            children.append((seq, replay))

        logger.info(
            f"[MinimaxAgent] Built {len(children)} children "
            f"in {time.time() - start:.3f}s"
        )

        return children

    # ----------------------------------------------------------------------
    # Main public method
    # ----------------------------------------------------------------------
    def execute_next_actions(self, game_api, team_id: int) -> None:
        logger.info(f"[MinimaxAgent] === AI TURN START (team={team_id}) ===")

        # Child generator wrapper
        def child_gen(sim, acting_team):
            return self._get_children(sim, acting_team, team_id)

        # ----------------------------------------------------
        # 🔥 DO NOT USE game_api.clone()
        #    Use SimulationAPI to avoid pygame deepcopy crash
        # ----------------------------------------------------
        sim_root = SimulationAPI(game_api.game_board.fast_clone())

        start_total = time.time()
        root_children = child_gen(sim_root, team_id)

        logger.info(
            f"[MinimaxAgent] Root expansion produced {len(root_children)} children "
            f"(depth={self.depth})"
        )

        if not root_children:
            logger.warning("[MinimaxAgent] No legal root sequences")
            return

        best_score = -inf
        best_seq = None

        # -------------------------------------------------------------
        # Evaluate each top-level child with minimax
        # -------------------------------------------------------------
        for idx, (seq, child_sim) in enumerate(root_children):
            logger.debug(
                f"[MinimaxAgent] Running minimax on child #{idx} (len={len(seq)})"
            )

            t_child = time.time()
            score = self.minimax(
                sim=child_sim,
                team_id=team_id,
                depth=self.depth,
                alpha=-inf,
                beta=inf,
                is_max=False,  # opponent acts next
            )

            logger.info(
                f"[MinimaxAgent] Child #{idx} → minimax={score:.4f} "
                f"({time.time() - t_child:.3f}s)"
            )

            if score > best_score:
                best_score = score
                best_seq = seq

        logger.info(
            f"[MinimaxAgent] Best score={best_score:.4f} "
            f"(thinking time={time.time() - start_total:.3f}s)"
        )

        if not best_seq:
            logger.warning("[MinimaxAgent] No best sequence found")
            return

        # Apply chosen sequence to real game
        logger.info(f"[MinimaxAgent] Executing sequence (len={len(best_seq)})")
        for act in best_seq:
            logger.debug(f"[MinimaxAgent] → {act}")
            game_api.apply_action(act)

    def play_turn(self, game_api, team_id: int):
        logger.info(f"[MinimaxAgent] play_turn(team={team_id})")
        self.execute_next_actions(game_api, team_id)

    # ----------------------------------------------------------------------
    # Minimax with alpha-beta pruning
    # ----------------------------------------------------------------------
    def minimax(
        self,
        sim,
        team_id: int,
        depth: int,
        alpha: float,
        beta: float,
        is_max: bool,
    ):
        """Minimax with alpha-beta pruning as an agent method."""

        # Terminal node
        if depth == 0 or sim.is_game_over():
            return self._eval_snapshot(sim.get_board_snapshot(), team_id)

        acting_team = team_id if is_max else (1 if team_id == 2 else 2)

        # Generate children
        children = self._get_children(sim, acting_team, team_id)
        if not children:
            return self._eval_snapshot(sim.get_board_snapshot(), team_id)

        # -------------------------------------------------------
        # MAX node
        # -------------------------------------------------------
        if is_max:
            best = -inf
            for _, child_sim in children:
                value = self.minimax(
                    sim=child_sim,
                    team_id=team_id,
                    depth=depth - 1,
                    alpha=alpha,
                    beta=beta,
                    is_max=False,
                )
                best = max(best, value)
                alpha = max(alpha, best)
                if alpha >= beta:
                    break
            return best

        # -------------------------------------------------------
        # MIN node
        # -------------------------------------------------------
        else:
            best = inf
            for _, child_sim in children:
                value = self.minimax(
                    sim=child_sim,
                    team_id=team_id,
                    depth=depth - 1,
                    alpha=alpha,
                    beta=beta,
                    is_max=True,
                )
                best = min(best, value)
                beta = min(beta, best)
                if alpha >= beta:
                    break
            return best

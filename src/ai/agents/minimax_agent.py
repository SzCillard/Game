from __future__ import annotations

import time
from math import inf
from typing import Any

from ai.neat.neat_network import NeatNetwork
from ai.planning.action_planning import ActionPlannerReversible
from ai.utils.nn_utils import encode_state, encode_state_old
from api.simulation_api import SimulationAPI
from utils.logging import logger


class MinimaxAgent:
    """
    Minimax-based agent that searches over *full-turn* action sequences.

    Key points:
    - Uses SimulationAPI so we never clone UI / renderer / pygame objects.
    - Uses ActionPlannerReversible to generate full-turn sequences.
    - Uses a per-team sequence cache so DFS is done ONCE per team per turn.
      All deeper minimax nodes reuse those sequences, only re-simulating them.
    """

    def __init__(
        self,
        brain: NeatNetwork,
        depth: int = 2,
        dfs_action_sets_limit: int = 200,
        dfs_branching_limit: int = 12,
        child_limit: int = 6,
    ) -> None:
        self.depth = depth
        self.child_limit = child_limit

        # Planner generates full-turn sequences with reversible DFS
        self.planner = ActionPlannerReversible(
            dfs_action_sets_limit=dfs_action_sets_limit,
            dfs_branching_limit=dfs_branching_limit,
            exploration_rate=0.0,
        )

        self.brain = brain

        # ✅ Cache of sequences per team_id for the current move
        #    { team_id: list[list[action_dict]] }
        self._sequence_cache: dict[int, list[list[dict]]] = {}

        logger.info(
            f"[MinimaxAgent] Initialized (depth={depth}, "
            f"""dfs_action_sets_limit={dfs_action_sets_limit},
            dfs_branching_limit={dfs_branching_limit}, """
            f"child_limit={child_limit})"
        )

    # ----------------------------------------------------------------------
    # Evaluation
    # ----------------------------------------------------------------------
    def _eval_snapshot(self, snapshot: dict, team_id: int) -> float:
        """Evaluate board snapshot with NEAT brain for given team_id."""
        state = encode_state_old(snapshot, team_id)
        return float(self.brain.predict(state)[0])

    # ----------------------------------------------------------------------
    # Cached sequence retrieval
    # ----------------------------------------------------------------------
    def _get_sequences_cached(self, team_id: int, sim) -> list[list[dict]]:
        """
        Return full-turn sequences for `team_id`, using a cache.

        The first time this is called in a move for a given team:
          - We run DFS (plan_sequences) from the provided sim.
          - We cache the resulting list of sequences.

        All further calls for that team_id reuse the cached sequences, which
        we then re-simulate from whatever sim is passed in.
        """
        if team_id in self._sequence_cache:
            return self._sequence_cache[team_id]

        # Generate sequences ONCE (expensive DFS)
        start = time.time()
        # sequences = self.planner.plan_sequences(sim.game_board, team_id)
        sequences = self.planner.plan_sequences(
            game_board=sim.game_board,
            team_id=team_id,
            # eval_fn=lambda snap: self._eval_snapshot(snap, team_id),
        )

        self._sequence_cache[team_id] = sequences

        logger.info(
            f"[MinimaxAgent] Cached {len(sequences)} sequences for team {team_id} "
            f"(DFS took {time.time() - start:.3f}s)"
        )
        return sequences

    # ----------------------------------------------------------------------
    # Child expansion (uses cached sequences)
    # ----------------------------------------------------------------------
    def _get_children(
        self,
        sim,
        acting_team: int,
        eval_team: int,
    ) -> list[tuple[list[dict], Any]]:
        """
        For this node:
          1. Get full-turn sequences for acting_team (from cache or DFS once).
          2. For each sequence:
               - simulate it once from the current sim
               - evaluate the resulting state with NN
               - keep the resulting SimulationAPI
          3. Sort by score and keep top `child_limit`.

        This is the main performance hotspot: re-simulation is relatively
        cheap, DFS is very expensive—so we cache DFS results per team.
        """
        logger.debug(f"[MinimaxAgent] Expanding children (team={acting_team})")

        start = time.time()
        sequences = self._get_sequences_cached(acting_team, sim)

        logger.info(
            f"[MinimaxAgent] Using {len(sequences)} cached sequences "
            f"for team {acting_team}"
        )

        if not sequences:
            return []

        if len(sequences) > 100:
            logger.warning(
                f"[MinimaxAgent] ⚠ HIGH SEQUENCE COUNT ({len(sequences)}) → slow search"
            )

        opponent = 1 if acting_team == 2 else 2
        scored_children: list[tuple[list[dict], float, Any]] = []

        for idx, seq in enumerate(sequences):
            # Simulate this sequence from the CURRENT sim state
            replay = sim.clone()
            replay.start_turn(acting_team)

            for act in seq:
                replay.apply_action(act)

            # If game continues, advance to opponent's turn
            if not replay.is_game_over():
                replay.start_turn(opponent)

            score = self._eval_snapshot(replay.get_board_snapshot(), eval_team)
            scored_children.append((seq, score, replay))

            logger.debug(
                f"[MinimaxAgent] Seq #{idx} | len={len(seq)} | score={score:.4f}"
            )

        # Sort by score descending (best first)
        scored_children.sort(key=lambda x: x[1], reverse=True)

        if self.child_limit:
            scored_children = scored_children[: self.child_limit]

        children = [(seq, replay) for (seq, _score, replay) in scored_children]

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

        # 🔄 Reset sequence cache for this full AI move
        self._sequence_cache.clear()

        # Child generator wrapper: minimax calls this
        def child_gen(sim, acting_team):
            return self._get_children(sim, acting_team, team_id)

        # ----------------------------------------------------
        # Use SimulationAPI to avoid pygame deepcopy crash
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
            score = self._minimax(
                sim=child_sim,
                team_id=team_id,
                depth=self.depth,
                alpha=-inf,
                beta=inf,
                is_max=False,  # opponent acts next
                child_gen=child_gen,
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
    # Minimax with alpha-beta pruning (as an instance method)
    # ----------------------------------------------------------------------
    def _minimax(
        self,
        sim,
        team_id: int,
        depth: int,
        alpha: float,
        beta: float,
        is_max: bool,
        child_gen,
    ) -> float:
        """
        Minimax with alpha-beta pruning.

        - `team_id` is the MAX player.
        - `is_max` tells whether this node is MAX or MIN.
        - `child_gen(sim, acting_team)` returns [(sequence, new_sim), ...]
          and internally reuses cached sequences per team.
        """

        # Terminal node
        if depth == 0 or sim.is_game_over():
            return self._eval_snapshot(sim.get_board_snapshot(), team_id)

        acting_team = team_id if is_max else (1 if team_id == 2 else 2)

        # Generate children using cached sequences
        children = child_gen(sim, acting_team)
        if not children:
            return self._eval_snapshot(sim.get_board_snapshot(), team_id)

        # -------------------------------------------------------
        # MAX node
        # -------------------------------------------------------
        if is_max:
            best = -inf
            for _, child_sim in children:
                value = self._minimax(
                    sim=child_sim,
                    team_id=team_id,
                    depth=depth - 1,
                    alpha=alpha,
                    beta=beta,
                    is_max=False,
                    child_gen=child_gen,
                )
                if value > best:
                    best = value
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            return best

        # -------------------------------------------------------
        # MIN node
        # -------------------------------------------------------
        best = inf
        for _, child_sim in children:
            value = self._minimax(
                sim=child_sim,
                team_id=team_id,
                depth=depth - 1,
                alpha=alpha,
                beta=beta,
                is_max=True,
                child_gen=child_gen,
            )
            if value < best:
                best = value
            if best < beta:
                beta = best
            if alpha >= beta:
                break
        return best

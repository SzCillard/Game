from __future__ import annotations

import math
import random
import time
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
    """
    Monte Carlo Tree Search agent operating on *full-turn action sequences*.

    - Uses ActionPlannerReversible to generate candidate full-turn sequences
      for the AI side (like your minimax agent).
    - Uses SimulationAPI to simulate future turns (no UI / pygame cloning).
    - At the root:
        * Generates N candidate sequences
        * Keeps top K by quick NN evaluation
        * Runs MCTS iterations over these root moves
    - Each playout:
        * Applies the chosen root sequence
        * Then simulates a few random full turns for both players
        * Evaluates the final state with the NEAT network
    """

    def __init__(
        self,
        brain: NeatNetwork,
        dfs_action_sets_limit: int = 200,  # DFS limit for sequence generation
        dfs_branching_limit: int = 20,  # max actions per DFS node
        max_root_children: int = 8,  # how many root moves to keep
        iterations: int = 80,  # MCTS iterations per AI move
        rollout_turns: int = 2,  # how many full turns in a rollout
        c_puct: float = 1.4,  # exploration constant
    ) -> None:
        self.brain = brain

        self.planner = ActionPlannerReversible(
            dfs_action_sets_limit=dfs_action_sets_limit,
            dfs_branching_limit=dfs_branching_limit,
            exploration_rate=0.0,
        )

        self.max_root_children = max_root_children
        self.iterations = iterations
        self.rollout_turns = rollout_turns
        self.c_puct = c_puct

        logger.info(
            "[MCTSAgent] Initialized "
            f"""(dfs_action_sets_limit={dfs_action_sets_limit},
            dfs_branching_limit={dfs_branching_limit}, """
            f"max_root_children={max_root_children}, iterations={iterations}, "
            f"rollout_turns={rollout_turns}, c_puct={c_puct})"
        )

    # ----------------------------------------------------------------------
    # NEAT evaluation
    # ----------------------------------------------------------------------
    def _eval_snapshot(self, snapshot: dict, team_id: int) -> float:
        state = encode_state(snapshot, team_id)
        return float(self.brain.predict(state)[0])

    # ----------------------------------------------------------------------
    # Root move generation & pruning
    # ----------------------------------------------------------------------
    def _generate_root_moves(
        self,
        game_board,
        team_id: int,
    ) -> list[_MCTSChildStats]:
        """
        Generate candidate full-turn sequences for `team_id` and prune them
        down to at most `max_root_children`, preferring high NN scores.
        """
        logger.info("[MCTSAgent] Generating root sequences for MCTS...")

        t0 = time.time()
        all_sequences = self.planner.plan_sequences(game_board, team_id)
        dt = time.time() - t0

        logger.info(
            f"[MCTSAgent] DFS generated {len(all_sequences)} sequences "
            f"for team {team_id} in {dt:.3f}s"
        )

        if not all_sequences:
            return []

        # Quick score for pruning: simulate once per sequence from the ROOT board
        # and evaluate with NN.
        scored: list[tuple[list[dict], float]] = []

        sim_root = SimulationAPI(game_board.fast_clone())
        sim_root.start_turn(team_id)

        for idx, seq in enumerate(all_sequences):
            replay = sim_root.clone()
            # It's our turn
            # (start_turn already called on sim_root; clone should preserve state)
            # but to be safe, ensure turn:
            replay.start_turn(team_id)

            for act in seq:
                replay.apply_action(act)

            val = self._eval_snapshot(replay.get_board_snapshot(), team_id)
            scored.append((seq, val))

            logger.debug(
                f"[MCTSAgent] Root seq #{idx} len={len(seq)} quick_eval={val:.4f}"
            )

        scored.sort(key=lambda x: x[1], reverse=True)

        if self.max_root_children is not None and self.max_root_children > 0:
            scored = scored[: self.max_root_children]

        root_children = [
            _MCTSChildStats(sequence=seq, visits=0, value_sum=0.0)
            for (seq, _val) in scored
        ]

        logger.info(f"[MCTSAgent] Kept {len(root_children)} root moves after pruning")
        return root_children

    # ----------------------------------------------------------------------
    # Rollout policy (random turns)
    # ----------------------------------------------------------------------
    def _rollout(
        self,
        root_sim: SimulationAPI,
        team_id: int,
    ) -> float:
        """
        Starting from `root_sim`, simulate a few random full turns for both sides.
        Returns NEAT evaluation from `team_id`'s perspective.
        """

        sim = root_sim

        # Determine opponent ID (assuming only teams 1 and 2)
        opponent = 1 if team_id == 2 else 2

        # We'll alternate turns: opponent, us, opponent, us, ...
        # Starting from whoever is next to act. Here we just alternate a fixed pattern:
        # opp -> us -> opp -> ...
        current = opponent

        for _ in range(self.rollout_turns):
            if sim.is_game_over():
                break

            sim.start_turn(current)

            # Play entire turn randomly
            while not sim.check_turn_end(current):
                legal = sim.get_legal_actions(current)
                if not legal:
                    break
                action = random.choice(legal)
                sim.apply_action(action)

                if sim.is_game_over():
                    break

            # Switch side
            current = team_id if current == opponent else opponent

        # Evaluate final state
        return self._eval_snapshot(sim.get_board_snapshot(), team_id)

    # ----------------------------------------------------------------------
    # MCTS Selection: choose a root child index via UCB1
    # ----------------------------------------------------------------------
    def _select_child_ucb(
        self,
        children: list[_MCTSChildStats],
        total_visits: int,
    ) -> int:
        """
        Return index of selected child using UCB1 on the root children.
        """
        log_n = math.log(total_visits + 1.0)
        best_idx = 0
        best_score = -float("inf")

        for i, ch in enumerate(children):
            if ch.visits == 0:
                ucb = float("inf")
            else:
                exploit = ch.q_value
                explore = self.c_puct * math.sqrt(log_n / ch.visits)
                ucb = exploit + explore

            if ucb > best_score:
                best_score = ucb
                best_idx = i

        return best_idx

    # ----------------------------------------------------------------------
    # Main entry: decide and play a turn
    # ----------------------------------------------------------------------
    def execute_next_actions(self, game_api, team_id: int) -> None:
        logger.info(f"[MCTSAgent] === AI TURN START (team={team_id}) ===")

        # 1) Generate and prune root moves
        root_children = self._generate_root_moves(game_api.game_board, team_id)

        if not root_children:
            logger.warning("[MCTSAgent] No sequences available; skipping turn")
            return

        # 2) Run MCTS iterations
        total_visits = 0
        t_start = time.time()

        for it in range(self.iterations):
            # Selection
            idx = self._select_child_ucb(root_children, total_visits)
            child = root_children[idx]

            # Simulation: apply the chosen root move from the REAL board
            sim = SimulationAPI(game_api.game_board.fast_clone())
            sim.start_turn(team_id)

            for act in child.sequence:
                sim.apply_action(act)
                if sim.is_game_over():
                    break

            if not sim.is_game_over():
                # After our full-turn, opponent would act next
                sim.start_turn(1 if team_id == 2 else 2)

            # Rollout
            value = self._rollout(sim, team_id)

            # Backpropagation (root only)
            child.visits += 1
            child.value_sum += value
            total_visits += 1

            logger.debug(
                f"[MCTSAgent] Iter {it + 1}/{self.iterations} → child#{idx} "
                f"rollout_value={value:.4f}, visits={child.visits}, "
                f"Q={child.q_value:.4f}"
            )

        logger.info(
            f"[MCTSAgent] MCTS finished {total_visits} simulations in "
            f"{time.time() - t_start:.3f}s"
        )

        # 3) Choose best root child to play
        best_child = max(root_children, key=lambda ch: (ch.visits, ch.q_value))

        logger.info(
            f"[MCTSAgent] Selected sequence: visits={best_child.visits}, "
            f"Q={best_child.q_value:.4f}, len={len(best_child.sequence)}"
        )

        # 4) Execute chosen sequence in the real game
        for act in best_child.sequence:
            logger.debug(f"[MCTSAgent] → {act}")
            game_api.apply_action(act)

    def play_turn(self, game_api, team_id: int):
        """
        Entry point used by GameAPI.run_ai_turn.
        """
        logger.info(f"[MCTSAgent] play_turn(team={team_id})")
        self.execute_next_actions(game_api, team_id)

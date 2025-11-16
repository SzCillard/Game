# ai/agents/dfs_planner.py
from __future__ import annotations

import copy
import random
from typing import Any, Callable, Dict, List

from backend.board import GameState
from backend.logic import GameLogic


class _SimulationAPI:
    """
    Minimal simulation wrapper around GameState + GameLogic.

    Used internally by the DFS planner to:
      - reset turns,
      - generate legal actions,
      - apply actions,
      - detect end of turn,
      - query board snapshots.
    """

    def __init__(self, game_board: GameState):
        self.game_board: GameState = game_board
        self.game_logic: GameLogic = GameLogic(self.game_board)

    def clone(self) -> "_SimulationAPI":
        board_copy = self.game_board.fast_clone()
        return _SimulationAPI(board_copy)

    # Turn lifecycle
    def start_team_turn(self, team_id: int) -> None:
        self.game_logic.update_damage_timers()

    # Action interface
    def get_legal_actions(self, team_id: int) -> List[Dict[str, Any]]:
        return self.game_logic.get_legal_actions(team_id)

    def check_turn_end(self, team_id: int) -> bool:
        return self.game_logic.check_turn_end(team_id)

    def apply_action(self, action: Dict[str, Any]) -> bool:
        success = self.game_logic.apply_action(action)
        if success:
            self.game_logic.update_damage_timers()
        return success

    def get_board_snapshot(self) -> Dict[str, Any]:
        return self.game_board.get_snapshot()


class DfsTurnPlanner:
    """
    Shared DFS-based full-turn planner.

    Usage:
      - You pass a GameState and a team_id.
      - You pass an eval_fn(snapshot) -> float, which scores terminal states.
      - It returns a list of action dicts to execute for that team's turn.
    """

    def __init__(
        self,
        max_depth: int = 3,
        max_sets: int = 10,
        max_branching: int = 8,
        exploration_rate: float = 0.0,
    ) -> None:
        self.max_depth = max_depth
        self.max_sets = max_sets
        self.max_branching = max_branching
        self.exploration_rate = exploration_rate

    # ----------------------------------------------------------
    # Internal: DFS over action sequences
    # ----------------------------------------------------------
    def _generate_action_sequences(
        self,
        base_sim: _SimulationAPI,
        team_id: int,
    ) -> List[List[Dict[str, Any]]]:
        sequences: List[List[Dict[str, Any]]] = []

        def dfs(depth: int, actions: List[Dict[str, Any]], sim: _SimulationAPI):
            if len(sequences) >= self.max_sets:
                return

            # Depth limit or end-of-turn => record this sequence
            if depth >= self.max_depth or sim.check_turn_end(team_id):
                sequences.append(actions)
                return

            legal = sim.get_legal_actions(team_id)
            if not legal:
                sequences.append(actions)
                return

            random.shuffle(legal)
            legal = legal[: self.max_branching]

            for action in legal:
                if len(sequences) >= self.max_sets:
                    break
                nxt = sim.clone()
                if nxt.apply_action(action):
                    dfs(depth + 1, actions + [action], nxt)

        dfs(0, [], base_sim)
        if not sequences:
            sequences.append([])
        return sequences

    # ----------------------------------------------------------
    # Public: plan a full turn
    # ----------------------------------------------------------
    def plan_turn(
        self,
        game_board: GameState,
        team_id: int,
        eval_fn: Callable[[Dict[str, Any]], float],
    ) -> List[Dict[str, Any]]:
        """
        Plan a full turn for `team_id` from `game_board` using DFS + eval_fn.

        eval_fn receives a board snapshot (dict) and must return a scalar score.
        """
        # Build simulation base from a deep copy of the board
        base_sim = _SimulationAPI(copy.deepcopy(game_board))
        base_sim.start_team_turn(team_id)

        sequences = self._generate_action_sequences(base_sim, team_id)
        if not sequences:
            return []

        # Exploration: sometimes pick a random sequence (mainly used in training)
        if self.exploration_rate > 0.0 and random.random() < self.exploration_rate:
            return random.choice(sequences)

        # Otherwise score each sequence and pick best
        best_score = float("-inf")
        best_seq: List[Dict[str, Any]] = []

        for seq in sequences:
            eval_sim = _SimulationAPI(copy.deepcopy(game_board))
            eval_sim.start_team_turn(team_id)
            for action in seq:
                eval_sim.apply_action(action)

            snapshot = eval_sim.get_board_snapshot()
            score = eval_fn(snapshot)
            if score > best_score:
                best_score = score
                best_seq = seq

        return best_seq

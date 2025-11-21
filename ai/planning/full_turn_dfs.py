# ai/planning/full_turn_dfs.py
from __future__ import annotations

import random
from typing import Any, Callable

from backend.board import GameState
from backend.logic import GameLogic


class _SimulationAPI:
    """
    Minimal simulation wrapper for DFS.
    """

    def __init__(self, board: GameState):
        self.game_board = board
        self.game_logic = GameLogic(self.game_board)

    def clone(self) -> "_SimulationAPI":
        new_board = self.game_board.fast_clone()
        return _SimulationAPI(new_board)

    def start_turn(self, team_id: int):
        self.game_logic.turn_begin_reset(team_id)

    def get_legal_actions(self, team_id: int) -> list[dict[str, Any]]:
        return self.game_logic.get_legal_actions(team_id)

    def apply_action(self, action: dict[str, Any]) -> bool:
        ok = self.game_logic.apply_action(action)
        return ok

    def check_turn_end(self, team_id: int) -> bool:
        return self.game_logic.check_turn_end(team_id)

    def snapshot(self) -> dict[str, Any]:
        return self.game_board.get_snapshot()


class FullTurnDFS:
    """
    Pure DFS-based full-turn planner.
    No depth limit.
    Limits via:
        - max_branching
        - max_sets
    """

    def __init__(
        self,
        max_sets: int = 200,
        max_branching: int = 20,
        exploration_rate: float = 0.0,
    ):
        self.max_sets = max_sets
        self.max_branching = max_branching
        self.exploration_rate = exploration_rate

    # ------------------------------------------
    # Internal DFS
    # ------------------------------------------
    def _dfs(
        self,
        team_id: int,
        sim: _SimulationAPI,
        actions: list[dict[str, Any]],
        out_sequences: list[list[dict[str, Any]]],
    ):
        if len(out_sequences) >= self.max_sets:
            return

        if sim.check_turn_end(team_id):
            out_sequences.append(actions)
            return

        legal = sim.get_legal_actions(team_id)
        if not legal:
            out_sequences.append(actions)
            return

        random.shuffle(legal)
        legal = legal[: self.max_branching]

        for act in legal:
            if len(out_sequences) >= self.max_sets:
                break

            nxt = sim.clone()
            if nxt.apply_action(act):
                self._dfs(team_id, nxt, actions + [act], out_sequences)

    # ------------------------------------------
    # Public API
    # ------------------------------------------
    def plan(
        self,
        game_board: GameState,
        team_id: int,
        eval_fn: Callable[[dict[str, Any]], float],
    ) -> list[dict[str, Any]]:
        base = _SimulationAPI(game_board.fast_clone())
        base.start_turn(team_id)

        sequences: list[list[dict[str, Any]]] = []
        self._dfs(team_id, base, [], sequences)

        if not sequences:
            return []

        # Exploration (training only)
        if self.exploration_rate > 0 and random.random() < self.exploration_rate:
            return random.choice(sequences)

        # Evaluate
        best_score = float("-inf")
        best_seq: list[dict[str, Any]] = []

        for seq in sequences:
            sim = _SimulationAPI(game_board.fast_clone())
            sim.start_turn(team_id)

            for act in seq:
                sim.apply_action(act)

            score = eval_fn(sim.snapshot())
            if score > best_score:
                best_score = score
                best_seq = seq

        return best_seq

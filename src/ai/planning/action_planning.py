# ai/planning/full_turn_dfs.py
from __future__ import annotations

import random
from typing import Any, Callable

from api.simulation_api import SimulationAPI
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
        self.game_logic.start_turn(team_id)

    def get_legal_actions(self, team_id: int) -> list[dict[str, Any]]:
        return self.game_logic.get_legal_actions(team_id)

    def apply_action(self, action: dict[str, Any]) -> bool:
        ok = self.game_logic.apply_action(action)
        return ok

    def check_turn_end(self, team_id: int) -> bool:
        return self.game_logic.check_turn_end(team_id)

    def snapshot(self) -> dict[str, Any]:
        return self.game_board.get_snapshot()


class ActionPlannerReversible:
    def __init__(
        self,
        dfs_action_sets_limit: int,
        dfs_branching_limit: int,
        exploration_rate: float,
    ):
        self.dfs_action_sets_limit = dfs_action_sets_limit
        self.dfs_branching_limit = dfs_branching_limit
        self.exploration_rate = exploration_rate

    # ------------------------------------------------------------
    # Apply action with reversible state token
    # ------------------------------------------------------------
    def _apply_action_reversible(self, sim: SimulationAPI, action: dict):
        board = sim.game_board
        logic = sim.game_logic

        restore = {
            "unit_states": [],
            "units_list": None,
        }

        # --------- MOVE ACTION ---------
        if action["type"] == "move":
            uid = action["unit_id"]
            u = board.get_unit_by_id(uid)
            if u is None:
                return False, None

            restore["unit_states"].append((u, (u.x, u.y, u.move_points, u.has_acted)))

        # --------- ATTACK ACTION ---------
        elif action["type"] == "attack":
            aid = action["unit_id"]
            did = action["target"]

            attacker = board.get_unit_by_id(aid)
            defender = board.get_unit_by_id(did)

            if attacker is None or defender is None:
                return False, None

            restore["unit_states"].append(
                (
                    attacker,
                    (
                        attacker.x,
                        attacker.y,
                        attacker.health,
                        attacker.has_attacked,
                        attacker.has_acted,
                    ),
                )
            )
            restore["unit_states"].append(
                (
                    defender,
                    (
                        defender.x,
                        defender.y,
                        defender.health,
                        defender.has_attacked,
                        defender.has_acted,
                    ),
                )
            )

        # Save whole unit list (for restores after death)
        restore["units_list"] = list(board.units)

        ok = logic.apply_action(action)
        return ok, restore

    # ------------------------------------------------------------
    # Undo reversible change
    # ------------------------------------------------------------
    def _undo(self, sim: SimulationAPI, restore):
        board = sim.game_board

        # Restore units' attributes
        for unit, state in restore["unit_states"]:
            if len(state) == 4:  # move
                unit.x, unit.y, unit.move_points, unit.has_acted = state
            else:  # attack
                (unit.x, unit.y, unit.health, unit.has_attacked, unit.has_acted) = state

        # Restore full unit list (dead units revived)
        board.units = restore["units_list"]

    # ------------------------------------------------------------
    # DFS recursion
    # ------------------------------------------------------------
    def _dfs(self, team_id, sim, actions, out):
        if len(out) >= self.dfs_action_sets_limit:
            return

        if sim.check_turn_end(team_id):
            out.append(actions[:])
            return

        legal = sim.get_legal_actions(team_id)
        if not legal:
            out.append(actions[:])
            return

        random.shuffle(legal)
        legal = legal[: self.dfs_branching_limit]

        for act in legal:
            ok, token = self._apply_action_reversible(sim, act)
            if not ok:
                continue

            actions.append(act)
            self._dfs(team_id, sim, actions, out)
            actions.pop()

            self._undo(sim, token)

            if len(out) >= self.dfs_action_sets_limit:
                break

    # ------------------------------------------------------------
    # Public planning entry
    # ------------------------------------------------------------
    def plan(self, game_board, team_id, eval_fn):
        sim = SimulationAPI(game_board.fast_clone())
        sim.start_turn(team_id)

        sequences = []
        self._dfs(team_id, sim, [], sequences)

        if not sequences:
            return []

        if self.exploration_rate > 0 and random.random() < self.exploration_rate:
            return random.choice(sequences)

        best = None
        best_score = float("-inf")

        for seq in sequences:
            replay_api = SimulationAPI(game_board.fast_clone())
            replay_api.start_turn(team_id)

            for act in seq:
                replay_api.apply_action(act)

            score = eval_fn(replay_api.get_board_snapshot())
            if score > best_score:
                best_score = score
                best = seq

        return best or []

    def plan_sequences(self, game_board, team_id):
        sim = SimulationAPI(game_board.fast_clone())
        sim.start_turn(team_id)

        sequences = []
        self._dfs(team_id, sim, [], sequences)
        return sequences


class ActionPlanner:
    """
    Pure DFS-based full-turn planner.
    No depth limit.
    Limits via:
        - dfs_branching_limit
        - dfs_action_sets_limit
    """

    def __init__(
        self,
        dfs_action_sets_limit: int,
        dfs_branching_limit: int,
        exploration_rate: float,
    ):
        self.dfs_action_sets_limit = dfs_action_sets_limit
        self.dfs_branching_limit = dfs_branching_limit
        self.exploration_rate = exploration_rate

    # ------------------------------------------
    # Internal DFS
    # ------------------------------------------
    def _dfs(
        self,
        team_id: int,
        sim: SimulationAPI,
        actions: list[dict[str, Any]],
        out_sequences: list[list[dict[str, Any]]],
    ):
        if len(out_sequences) >= self.dfs_action_sets_limit:
            return

        if sim.check_turn_end(team_id):
            out_sequences.append(actions)
            return

        legal = sim.get_legal_actions(team_id)
        if not legal:
            out_sequences.append(actions)
            return

        random.shuffle(legal)
        legal = legal[: self.dfs_branching_limit]

        for act in legal:
            if len(out_sequences) >= self.dfs_action_sets_limit:
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
        base = SimulationAPI(game_board.fast_clone())
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
            sim = SimulationAPI(game_board.fast_clone())
            sim.start_turn(team_id)

            for act in seq:
                sim.apply_action(act)

            score = eval_fn(sim.get_board_snapshot())
            if score > best_score:
                best_score = score
                best_seq = seq

        return best_seq


# ------------------------------------------------------------
# Beam Search Full-Turn Planner  (FAST + NN-Guided)
# ------------------------------------------------------------
class BeamSearchPlannerFullTurn:
    """
    Beam-search-based full-turn planner.

    - Generates *full* action sequences for a single turn of `team_id`.
    - Uses beam search to limit branching:
        - At each step, keep only `beam_width` best partial sequences.
        - For each node, branch on at most `dfs_branching_limit` legal actions.
    - A sequence is considered "finished" when:
        - sim.check_turn_end(team_id) is True, or
        - there are no legal actions left.
    """

    def __init__(self, beam_width: int, dfs_branching_limit: int):
        self.beam_width = beam_width
        self.dfs_branching_limit = dfs_branching_limit

    def plan_sequences(
        self,
        game_board: GameState,
        team_id: int,
        eval_fn: Callable[[dict[str, Any]], float],
    ) -> list[list[dict[str, Any]]]:
        """
        Returns a list of full-turn action sequences (best-first).

        Each sequence is a list[dict] of actions that, when applied from
        the given game_board, completes the turn for `team_id`.
        """

        # Initial simulation at start of this team's turn
        root_sim = SimulationAPI(game_board.fast_clone())
        root_sim.start_turn(team_id)

        # frontier: list of (sim, seq, score)
        # score is evaluation of the *current* state after seq
        initial_score = eval_fn(root_sim.get_board_snapshot())
        frontier: list[tuple[SimulationAPI, list[dict[str, Any]], float]] = [
            (root_sim, [], initial_score)
        ]

        finished: list[tuple[list[dict[str, Any]], float]] = []

        while frontier:
            candidates: list[tuple[SimulationAPI, list[dict[str, Any]], float]] = []

            # Expand all nodes in current frontier
            for sim, seq, _ in frontier:
                # Check if this sequence already ended the turn
                if sim.check_turn_end(team_id):
                    finished.append((seq, eval_fn(sim.get_board_snapshot())))
                    continue

                legal = sim.get_legal_actions(team_id)
                if not legal:
                    # No moves → treat as finished sequence
                    finished.append((seq, eval_fn(sim.get_board_snapshot())))
                    continue

                random.shuffle(legal)
                legal = legal[: self.dfs_branching_limit]

                for act in legal:
                    child_sim = sim.clone()
                    if not child_sim.apply_action(act):
                        continue

                    child_seq = seq + [act]
                    score = eval_fn(child_sim.get_board_snapshot())
                    candidates.append((child_sim, child_seq, score))

            # No more candidates → all current frontier nodes were finished
            if not candidates:
                break

            # Sort candidates (best first) and keep only top beam_width
            candidates.sort(key=lambda item: item[2], reverse=True)
            frontier = candidates[: self.beam_width]

        # If we never produced a finished sequence, fall back to current frontier
        if not finished:
            finished = [(seq, score) for (_sim, seq, score) in frontier]

        # Sort finished by score, best first, and return only action sequences
        finished.sort(key=lambda item: item[1], reverse=True)
        return [seq for (seq, _score) in finished]

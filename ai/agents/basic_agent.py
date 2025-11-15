# ai/agents/basic_agent.py
from typing import Any, Dict, Optional

from utils.helpers import manhattan, next_step_toward_snapshot

from .base_agent import BaseAgent


class BasicAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__()

    def decide_next_action(
        self, board_snapshot: Dict[str, Any], team: int
    ) -> Optional[Dict[str, Any]]:
        """
        board_snapshot: dict returned by GameState.get_snapshot()
        team: team_id (1 or 2)
        """
        units = board_snapshot["units"]

        # Use team_id, not TeamType, to distinguish sides
        my_units = [
            u
            for u in units
            if int(u["team_id"]) == int(team)
            and not u["has_acted"]
            and u["move_points"] > 0
        ]

        enemy_units = [
            u for u in units if int(u["team_id"]) != int(team) and u["health"] > 0
        ]

        if not my_units or not enemy_units:
            return None

        unit = my_units[0]
        # pick nearest by manhattan for attack check, but movement uses path
        target = min(
            enemy_units, key=lambda e: manhattan(unit["x"], unit["y"], e["x"], e["y"])
        )

        # if in attack range (tile distance) -> attack
        if (
            manhattan(unit["x"], unit["y"], target["x"], target["y"])
            <= unit["attack_range"]
        ):
            return {"unit_id": unit["id"], "type": "attack", "target": target["id"]}

        # otherwise compute next step along shortest-cost path and move there
        nxt = next_step_toward_snapshot(
            board_snapshot, (unit["x"], unit["y"]), (target["x"], target["y"])
        )
        if nxt is None:
            return None
        nx, ny = nxt
        return {"unit_id": unit["id"], "type": "move", "target": (nx, ny)}

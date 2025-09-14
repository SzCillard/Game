# ai/basic_agent.py
from utils.helpers import distance

from .base_agent import BaseAgent


class BasicAgent(BaseAgent):
    def __init__(self):
        pass

    def decide_next_action(self, board_snapshot, team):
        """
        Decide the next action for one unit.

        Args:
            board_snapshot: a read-only representation of the current board
            team: the team number (1 or 2)

        Returns:
            action: dict containing
                {
                    "unit_id": int,
                    "type": "move" or "attack",
                    "target": (x, y) for move or target_unit_id for attack
                }
            or None if no action possible
        """
        my_units = [
            u for u in board_snapshot if u["team"] == team and not u["has_acted"]
        ]
        enemy_units = [u for u in board_snapshot if u["team"] != team]

        if not my_units or not enemy_units:
            return None

        unit = my_units[0]
        target = min(
            enemy_units, key=lambda e: distance(unit["x"], unit["y"], e["x"], e["y"])
        )

        dist = distance(unit["x"], unit["y"], target["x"], target["y"])

        if dist <= unit["attack_range"]:
            return {"unit_id": unit["id"], "type": "attack", "target": target["id"]}
        else:
            # Move one step toward target
            dx = target["x"] - unit["x"]
            dy = target["y"] - unit["y"]
            # Clamp to one tile
            dx = 0 if dx == 0 else (1 if dx > 0 else -1)
            dy = 0 if dy == 0 else (1 if dy > 0 else -1)

            new_x = unit["x"] + dx
            new_y = unit["y"] + dy

            return {"unit_id": unit["id"], "type": "move", "target": (new_x, new_y)}

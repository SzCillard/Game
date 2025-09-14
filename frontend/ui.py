# frontend/ui.py
from typing import Any, Dict, List, Optional

import pygame

from utils.constants import TeamType
from utils.helpers import pixel_to_grid


class UI:
    def __init__(self, cell_size: int):
        self.cell_size = cell_size

    def handle_event(
        self,
        event: pygame.event.Event,
        units_snapshot: List[Dict[str, Any]],
        selected_id: Optional[int],
    ) -> Optional[Dict[str, Any]]:
        """
        Process a Pygame event and return an action dict if applicable.
        Handles selecting, moving, and attacking units.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            px, py = event.pos
            x, y = pixel_to_grid(px, py, self.cell_size)

            # Find unit at clicked position
            target = next(
                (u for u in units_snapshot if u["x"] == x and u["y"] == y), None
            )
            selected = next((u for u in units_snapshot if u["id"] == selected_id), None)

            # No unit currently selected: try to select own unit
            if selected is None:
                if (
                    target
                    and target["team"] == TeamType.PLAYER
                    and not target["has_acted"]
                ):
                    return {"type": "select", "selected_id": target["id"]}
            else:
                # Unit already selected
                if target:
                    if target["team"] != selected["team"]:
                        # Attack enemy
                        return {
                            "type": "attack",
                            "attacker_id": selected["id"],
                            "defender_id": target["id"],
                        }
                    else:
                        # Switch selection to another friendly unit
                        if not target["has_acted"]:
                            return {"type": "select", "selected_id": target["id"]}
                        return None
                else:
                    # Move to empty cell
                    return {"type": "move", "unit_id": selected["id"], "to": (x, y)}

        return None

    def apply_action(self, action: Dict[str, Any], api) -> Dict[str, Optional[int]]:
        """
        Apply the given action through the API and return updated selection.
        """
        kind = action.get("type")

        if kind == "select":
            return {"selected_id": action["selected_id"]}

        elif kind == "move":
            unit = next(u for u in api.get_units() if u.id == action["unit_id"])
            x, y = action["to"]
            api.request_move(unit, x, y)
            return {"selected_id": unit.id}  # Keep selection on moved unit

        elif kind == "attack":
            attacker = next(u for u in api.get_units() if u.id == action["attacker_id"])
            defender = next(u for u in api.get_units() if u.id == action["defender_id"])
            api.request_attack(attacker, defender)
            return {"selected_id": None}  # Clear selection after attack

        return {"selected_id": None}

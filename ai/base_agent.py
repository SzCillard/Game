from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseAgent(ABC):
    @abstractmethod
    def decide_next_action(
        self, board_snapshot: List[Dict[str, Any]], team: int
    ) -> Dict[str, Any] | None:
        """
        Decide the next action for one of the agent's units.

        Args:
            board_snapshot: a list of unit dictionaries
            (read-only snapshot of the board)
            team: the team number (1 or 2)

        Returns:
            action: dict containing
                {
                    "unit_id": int,
                    "type": "move" or "attack",
                    "target": (x, y) for move OR unit_id for attack
                }
            or None if no action is possible
        """
        pass

    def evaluate_state(self, board_snapshot: List[Dict[str, Any]]) -> float:
        """Optional: returns a heuristic value of the board state."""
        return 0.0

    def reset(self) -> None:
        """Optional: reset internal state for a new game."""
        pass

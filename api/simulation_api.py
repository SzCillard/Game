# api/headless_api.py
from __future__ import annotations

from api.api import GameAPI
from backend.logic import GameLogic


class SimulationAPI(GameAPI):
    def __init__(self, game_board):
        super().__init__(
            game_ui=None,
            renderer=None,
            game_board=game_board,
            game_logic=GameLogic(game_board),
            agent=None,
        )

    def clone(self):
        new_board = self.game_board.fast_clone()
        return SimulationAPI(new_board)

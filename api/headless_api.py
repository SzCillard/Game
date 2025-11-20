# api/headless_api.py
from __future__ import annotations

from api.api import GameAPI
from backend.logic import GameLogic


class HeadlessGameAPI(GameAPI):
    def __init__(self, game_board, game_logic):
        super().__init__(
            game_ui=None,
            renderer=None,
            game_board=game_board,
            game_logic=game_logic,
            agent=None,
        )

    def clone(self):
        new_board = self.game_board.fast_clone()
        new_logic = GameLogic(new_board)
        return HeadlessGameAPI(new_board, new_logic)

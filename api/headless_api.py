# api/api.py
from __future__ import annotations

from api.api import GameAPI


class HeadlessGameAPI(GameAPI):
    def __init__(self, game_board, game_logic):
        super().__init__(
            game_ui=None,
            renderer=None,
            game_board=game_board,
            game_logic=game_logic,
            agent=None,
        )

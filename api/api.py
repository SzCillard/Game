# api/api.py
from __future__ import annotations

import copy
from typing import Any, Optional

from ai.agents.runtime_neat_agent import RuntimeNeatAgent
from backend.board import GameState
from backend.logic import GameLogic
from backend.units import Unit
from frontend.renderer import Renderer
from frontend.ui import UI
from utils.constants import TeamType
from utils.messages import draw_messages


class GameAPI:
    def __init__(
        self,
        game_ui: Optional[UI],
        renderer: Optional[Renderer],
        game_board: GameState,
        game_logic: GameLogic,
        agent: Any,
        team1_id: int = 1,
        team2_id: int = 2,
        team1_type: TeamType = TeamType.HUMAN,
        team2_type: TeamType = TeamType.AI,
    ):
        self.game_ui = game_ui
        self.renderer = renderer
        self.game_board = game_board
        self.game_logic = game_logic
        self.agent = agent

        # We keep ids in case you want to extend later
        self.team1_id = team1_id
        self.team2_id = team2_id

        # Store TeamType enums directly; int equality still works (IntEnum)
        self.team1_type = team1_type
        self.team2_type = team2_type

    def clone(self) -> "GameAPI":
        return copy.deepcopy(self)

    def reset(self, game_board: GameState):
        self.game_board = game_board
        self.game_logic.game_board = self.game_board

    def turn_begin_reset(self, team_id: int):
        self.game_logic.turn_begin_reset(team_id)

    def check_turn_end(self, team_id: int):
        return self.game_logic.check_turn_end(team_id)

    # ------------------------------
    # AI Turn Dispatch
    # ------------------------------

    def run_ai_turn(self, team_id: int):
        """
        Route AI turn to the proper implementation.
        Currently we assume a NEAT-based agent (RuntimeNeatAgent or similar)
        that exposes a `play_turn(api, team_id)` method.
        """
        if isinstance(self.agent, RuntimeNeatAgent):
            # NEAT runtime agent plans a whole turn internally (and uses NeatAgent)
            self.agent.play_turn(self, team_id)
        elif hasattr(self.agent, "play_turn"):
            # Generic NEAT-like agent with a play_turn method
            self.agent.play_turn(self, team_id)
        else:
            # No compatible agent configured; do nothing
            return None

    def update_damage_timers(self):
        self.game_logic.update_damage_timers()

    # --- Queries (frontend can use these) ---

    def get_units(self):
        """Return all units (read-only)"""
        return self.game_board.units.copy()

    def get_unit_at(self, x, y) -> Optional[Unit]:
        """Return the unit at (x,y) or None if empty"""
        return self.game_board.get_unit_at(x, y)

    def get_unit_by_id(self, id: int) -> Optional[Unit]:
        return self.game_board.get_unit_by_id(id)

    def add_units(
        self, unit_name_list: list[str], team_id: int, team: TeamType
    ) -> None:
        self.game_board.add_units(
            unit_name_list=unit_name_list, team_id=team_id, team=team
        )

    def is_game_over(self):
        return self.game_logic.is_game_over()

    def get_winner(self):
        return self.game_logic.get_winner()

    # --- Action requests (frontend calls these) ---

    def get_legal_actions(self, team_id):
        return self.game_logic.get_legal_actions(team_id)

    def request_move(self, unit, x, y):
        """Frontend requests a unit move. Returns success boolean."""
        return self.game_logic.move_unit(unit, x, y)

    def request_attack(self, attacker, target):
        """Frontend requests an attack. Returns True if successful."""
        return self.game_logic.apply_attack(attacker, target)

    def get_movable_tiles(self, unit):
        return self.game_logic.get_movable_tiles(unit)

    def get_attackable_tiles(self, unit):
        return self.game_logic.get_attackable_tiles(unit)

    def apply_action(self, action):
        return self.game_logic.apply_action(action)

    # --- Agent interaction ---

    def get_board_snapshot(self) -> dict[str, Any]:
        """Provide a read-only view of the board for AI agents"""
        return self.game_board.get_snapshot()

    def get_ai_action(self):
        """(kept for compatibility with simple agents)"""
        snapshot = self.get_board_snapshot()
        if hasattr(self.agent, "decide_next_action"):
            return self.agent.decide_next_action(snapshot, self.team2_id)
        return None

    # --- UI/Renderer interactions (backend calls these) ---

    def start_menu(self, screen, font):
        if not self.game_ui:
            return None
        return self.game_ui.start_menu(screen, font)

    def handle_ui_event(self, event, units_snapshot, selected_id):
        if not self.game_ui:
            return None
        return self.game_ui.handle_event(event, units_snapshot, selected_id)

    def apply_ui_action(self, action):
        if not self.game_ui:
            return None
        return self.game_ui.apply_action(action, self)

    def draw(self, screen, board_snapshot, selected_id=None, is_player_turn=False):
        if not self.renderer:
            return
        self.renderer.draw_sidebar(screen, board_snapshot, selected_id, is_player_turn)
        self.renderer.draw_grid(screen, board_snapshot)
        self.renderer.draw_units(screen, board_snapshot, selected_id)

    def draw_center_text(self, screen, text):
        if self.renderer:
            self.renderer.draw_center_text(screen, text)

    def draw_messages(self, screen, font, screen_height):
        draw_messages(screen, font, screen_height)

    def draw_highlights(self, screen, move_tiles, attack_tiles):
        if self.renderer:
            self.renderer.draw_highlights(screen, move_tiles, attack_tiles)

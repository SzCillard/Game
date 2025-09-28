# api/api.py
from typing import Optional

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
        game_ui: UI,
        renderer: Renderer,
        game_board: GameState,
        game_logic: GameLogic,
        agent,
        player_team: TeamType = TeamType.PLAYER,
        ai_team: TeamType = TeamType.AI,
    ):
        self.game_ui = game_ui
        self.renderer = renderer
        self.game_board = game_board
        self.game_logic = game_logic
        self.agent = agent
        # Store integer values internally for comparisons
        self.player_team = (
            player_team.value if isinstance(player_team, TeamType) else player_team
        )
        self.ai_team = ai_team.value if isinstance(ai_team, TeamType) else ai_team

    def turn_begin_reset(self, team):
        self.game_logic.turn_begin_reset(team)

    def turn_check_end(self, team):
        return self.game_logic.turn_check_end(team)

    def run_ai_turn(self, team):
        return self.game_logic.run_ai_turn(self.agent, team)

    # --- Queries (frontend can use these) ---
    def get_units(self):
        """Return all units (read-only)"""
        return self.game_board.units.copy()

    def get_unit_at(self, x, y) -> Optional[Unit]:
        """Return the unit at (x,y) or None if empty"""
        return self.game_board.get_unit_at(x, y)

    def is_game_over(self):
        return self.game_logic.is_game_over()

    def get_winner(self):
        return self.game_logic.get_winner()

    # --- Action requests (frontend calls these) ---
    def request_move(self, unit, x, y):
        """Frontend requests a unit move. Returns success boolean."""

        return self.game_logic.move_unit(unit, x, y)

    def request_attack(self, attacker, target):
        """Frontend requests an attack. Returns True if successful."""

        return self.game_logic.apply_attack(attacker, target)

    # --- Agent interaction ---
    def get_board_snapshot(self):
        """Provide a read-only view of the board for AI agents"""
        return self.game_board.get_snapshot()

    def get_ai_action(self):
        """Ask the agent to decide its next action"""
        snapshot = self.get_board_snapshot()
        return self.agent.decide_next_action(snapshot, self.ai_team)

    # --- UI/Renderer interactions (backend calls these) ---
    def start_menu(self, screen, font):
        return self.game_ui.start_menu(screen, font)

    def handle_ui_event(self, event, units_snapshot, selected_id):
        """
        Handle a pygame event and return an action dictionary if applicable.
        Action dict format:
        {
            "type": "select" | "move" | "attack",
            ... other fields depending on type ...
        }
        """
        return self.game_ui.handle_event(event, units_snapshot, selected_id)

    def apply_ui_action(self, action):
        return self.game_ui.apply_action(action, self)

    def draw(self, screen, board_snapshot, selected_id=None):
        self.renderer.draw_grid(screen, board_snapshot)
        self.renderer.draw_units(screen, board_snapshot, selected_id)

    def draw_center_text(self, screen, text):
        self.renderer.draw_center_text(screen, text)

    def draw_messages(self, screen, font, screen_height):
        draw_messages(screen, font, screen_height)


"""
def apply_action(self, action):
    if action["type"] == "move":
        unit = self.game_board.get_unit_by_id(action["unit_id"])
        x, y = action["target"]
        return self.request_move(unit, x, y)

    if action["type"] == "attack":
        attacker = self.game_board.get_unit_by_id(action["attacker_id"])
        defender = self.game_board.get_unit_by_id(action["target_id"])
        return self.request_attack(attacker, defender)
"""

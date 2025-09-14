# api/api.py
from utils.constants import TeamType


class GameAPI:
    def __init__(self, board, agent, player_team=TeamType.PLAYER, ai_team=TeamType.AI):
        self.board = board
        self.agent = agent
        # Store integer values internally for comparisons
        self.player_team = (
            player_team.value if isinstance(player_team, TeamType) else player_team
        )
        self.ai_team = ai_team.value if isinstance(ai_team, TeamType) else ai_team

    # --- Queries (frontend can use these) ---
    def get_units(self):
        """Return all units (read-only)"""
        return self.board.units.copy()

    def get_unit_at(self, x, y):
        return self.board.get_unit_at(x, y)

    def is_game_over(self):
        return self.board.is_game_over()

    def get_winner(self):
        return self.board.get_winner()

    # --- Action requests (frontend calls these) ---
    def request_move(self, unit, x, y):
        """Frontend requests a unit move. Returns success boolean."""
        from backend.logic import move_unit

        return move_unit(unit, self.board, x, y)

    def request_attack(self, attacker, target):
        """Frontend requests an attack. Returns True if successful."""
        from backend.logic import apply_attack

        return apply_attack(attacker, target, self.board)

    # --- Agent interaction ---
    def get_board_snapshot(self):
        """Provide a read-only view of the board for AI agents"""
        return self.board.get_snapshot()

    def get_ai_action(self):
        """Ask the agent to decide its next action"""
        snapshot = self.get_board_snapshot()
        return self.agent.decide_next_action(snapshot, self.ai_team)

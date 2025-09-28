# api/api.py
from utils.constants import TeamType


class GameAPI:
    def __init__(
        self, board, logic, agent, player_team=TeamType.PLAYER, ai_team=TeamType.AI
    ):
        self.board = board
        self.game_logic = logic
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
        return self.game_logic.is_game_over()

    def get_winner(self):
        return self.game_logic.get_winner()

    # --- Action requests (frontend calls these) ---
    def request_move(self, unit, x, y):
        """Frontend requests a unit move. Returns success boolean."""

        return self.game_logic.move_unit(unit, self.board, x, y)

    def request_attack(self, attacker, target):
        """Frontend requests an attack. Returns True if successful."""

        return self.game_logic.apply_attack(attacker, target, self.board)

    # --- Agent interaction ---
    def get_board_snapshot(self):
        """Provide a read-only view of the board for AI agents"""
        return self.board.get_snapshot()

    def get_ai_action(self):
        """Ask the agent to decide its next action"""
        snapshot = self.get_board_snapshot()
        return self.agent.decide_next_action(snapshot, self.ai_team)


"""
def apply_action(self, action):
    if action["type"] == "move":
        unit = self.board.get_unit_by_id(action["unit_id"])
        x, y = action["target"]
        return self.request_move(unit, x, y)

    if action["type"] == "attack":
        attacker = self.board.get_unit_by_id(action["attacker_id"])
        defender = self.board.get_unit_by_id(action["target_id"])
        return self.request_attack(attacker, defender)
"""

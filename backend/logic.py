from __future__ import annotations

import copy
from typing import Optional

from backend.board import GameState, TileType
from backend.units import Unit
from utils.constants import DAMAGE_DISPLAY_TIME, DIRS, EPSILON
from utils.helpers import calculate_damage, compute_min_cost_gs, manhattan
from utils.messages import logger


class GameLogic:
    """
    Core backend logic for game mechanics.

    Responsible for:
    - Movement validation and execution
    - Combat and damage application
    - Turn-based state management
    - Win condition checks
    - Running the AI’s decision loop
    """

    def __init__(self, game_state: GameState) -> None:
        """
        Initialize the game logic controller.

        Args:
            game_state (GameState): The shared game state containing tiles and units.
        """
        self.game_board = game_state
        self.dirs = DIRS

    def clone(self):
        return copy.deepcopy(self)

    # ------------------------------
    # Movement & Combat
    # ------------------------------

    def get_movable_tiles(self, unit: Unit) -> list[tuple[int, int]]:
        """
        Get all possible (x, y) tiles that a given unit can move to.

        Args:
            unit (Unit): The unit whose movement range to compute.

        Returns:
            list[tuple[int, int]]: A list of valid coordinates.
        """
        tiles: list[tuple[int, int]] = []

        for dx, dy in self.dirs:
            nx = unit.x + dx
            ny = unit.y + dy
            if self.can_move(unit, nx, ny):
                tiles.append((nx, ny))

        return tiles

    def can_move(self, unit: Unit, to_x: int, to_y: int) -> bool:
        # --- Boundary and occupancy checks ---
        if not self.game_board.in_bounds(to_x, to_y):
            return False
        if self.game_board.get_unit_at(to_x, to_y) is not None:
            return False
        if self.game_board.tile(to_x, to_y) == TileType.MOUNTAIN:
            return False
        if unit.has_attacked:  # cannot move after attacking
            return False

        # --- Cost check ---
        # Fast path: single-tile move (what AI / DFS uses)
        if manhattan(unit.x, unit.y, to_x, to_y) == 1:
            step_cost = self.game_board.move_cost(to_x, to_y)
        else:
            # Fallback for human long-click pathing
            step_cost = compute_min_cost_gs(
                self.game_board, (unit.x, unit.y), (to_x, to_y)
            )

        return step_cost <= unit.move_points

    def move_unit(self, unit: Unit, to_x: int, to_y: int) -> bool:
        if not self.can_move(unit, to_x, to_y):
            logger(
                f"""{unit.name} (ID:{unit.id}) unit of
                team:{unit.team} cannot move there [{to_x};{to_y}]."""
            )
            return False

        # Same cost logic as in can_move
        if manhattan(unit.x, unit.y, to_x, to_y) == 1:
            cost = self.game_board.move_cost(to_x, to_y)
        else:
            cost = compute_min_cost_gs(self.game_board, (unit.x, unit.y), (to_x, to_y))

        # --- Execute move ---
        unit.x = to_x
        unit.y = to_y
        unit.move_points = max(0.0, round(unit.move_points - cost, 3))

        if unit.move_points <= EPSILON:
            unit.has_acted = True

        logger(
            f"""{unit.name} (ID:{unit.id}) unit of team:{unit.team}
            moved to ({to_x},{to_y}), points left: {unit.move_points}."""
        )
        return True

    def get_attackable_tiles(self, unit: Unit) -> list[tuple[int, int]]:
        """
        Get all tiles containing enemy units that the given unit can attack.

        Args:
            unit (Unit): The attacking unit.

        Returns:
            list[tuple[int, int]]: Positions of enemy units in range.
        """
        tiles: list[tuple[int, int]] = []
        for target in self.game_board.units:
            if self.can_attack(unit, target):
                tiles.append((target.x, target.y))
        return tiles

    def can_attack(self, attacker: Unit, defender: Unit) -> bool:
        """
        Check whether an attack is possible between two units.

        Args:
            attacker (Unit): The attacking unit.
            defender (Unit): The defending unit.

        Returns:
            bool: True if attack is possible, False otherwise.
        """
        if attacker.team_id == defender.team_id:
            return False
        return manhattan(attacker.x, attacker.y, defender.x, defender.y) <= max(
            1, attacker.attack_range
        )

    def apply_attack(self, attacker: Unit, defender: Unit) -> bool:
        """
        Execute an attack between two units, including retaliation logic.

        Args:
            attacker (Unit): The attacking unit.
            defender (Unit): The defending unit.

        Returns:
            bool: True if attack executed successfully, False otherwise.
        """
        # --- Validate conditions ---
        if attacker.has_attacked or not self.can_attack(attacker, defender):
            return False

        # --- Compute and apply damage ---
        dmg = calculate_damage(attacker, defender, self.game_board)

        # Store damage data for UI animation
        defender.last_damage = dmg
        defender.damage_timer = DAMAGE_DISPLAY_TIME

        if attacker.attack_range > 1:
            # Ranged attack — no retaliation
            defender.health -= dmg
            logger(
                f"""{attacker.name} (ID:{attacker.id}) unit of team:{attacker.team}
                shot {defender.name} (ID:{defender.id}) unit of team:{defender.team}
                for {dmg}."""
            )
        else:
            # Melee — defender can retaliate if still alive
            defender.health -= dmg
            logger(
                f"""{attacker.name} (ID:{attacker.id}) unit of team:{attacker.team}
                hit {defender.name} (ID:{defender.id}) unit of team:{defender.team}
                for {dmg}."""
            )
            if defender.health > 0:
                retaliation = calculate_damage(defender, attacker)
                attacker.health -= retaliation
                if retaliation > 0:
                    logger(
                        f"""{defender.name} (ID:{defender.id}) unit of
                           team:{defender.team} retaliated for {retaliation}."""
                    )

        # --- Finalize attack ---
        attacker.has_attacked = True
        attacker.move_points = 0
        self.game_board.remove_dead()
        return True

    def get_legal_actions(self, team_id) -> list[dict]:
        actions = []
        units = [
            u
            for u in self.game_board.units
            if u.team_id == team_id and not u.has_acted and u.move_points > EPSILON
        ]

        for unit in units:
            # Moves
            movable_tiles = self.get_movable_tiles(unit)
            for x, y in movable_tiles:
                actions.append({"unit_id": unit.id, "type": "move", "target": (x, y)})

            # Attacks
            attackable_tiles = self.get_attackable_tiles(unit)
            for x, y in attackable_tiles:
                defender = self.game_board.get_unit_at(x, y)
                if defender:
                    actions.append(
                        {"unit_id": unit.id, "type": "attack", "target": defender.id}
                    )

            # Always allow wait/pass (finish action)
            actions.append({"unit_id": unit.id, "type": "wait", "target": None})

        return actions

    def apply_action(self, action: dict):
        unit = next(
            (u for u in self.game_board.units if u.id == action["unit_id"]), None
        )
        if not unit:
            return False

        if action["type"] == "move":
            x, y = action["target"]
            return self.move_unit(unit, x, y)

        elif action["type"] == "attack":
            target_id = action["target"]
            target_unit = next(
                (u for u in self.game_board.units if u.id == target_id), None
            )
            if target_unit:
                return self.apply_attack(unit, target_unit)
            return False

        elif action["type"] == "wait":
            unit.has_acted = True
            return True

        return False

    def update_damage_timers(self) -> None:
        """
        Update and decrease the damage text timers for all units.

        Used by renderer to fade out damage numbers over time.
        """
        for u in self.game_board.units:
            if hasattr(u, "damage_timer") and u.damage_timer > 0:
                u.damage_timer = max(0, u.damage_timer - 1)
                if u.damage_timer == 0:
                    u.last_damage = 0

    def start_turn(self, team_id: int) -> None:
        for u in self.game_board.units:
            if u.team_id == team_id:
                u.move_points = u.move_range
                u.has_attacked = False
                u.has_acted = False

    def check_turn_end(self, team_id: int) -> bool:
        units = [u for u in self.game_board.units if u.team_id == team_id]
        for u in units:
            if u.move_points <= EPSILON:
                u.has_acted = True
        return all(u.has_acted for u in units)

    def get_winner(self) -> Optional[int]:
        """
        Winner based on remaining team_ids.
        Returns: 1, 2, 0 (draw) or None.
        """
        team_ids = {u.team_id for u in self.game_board.units}
        if 1 in team_ids and 2 in team_ids:
            return None
        if 1 not in team_ids and 2 not in team_ids:
            return 0  # Draw
        return 1 if 1 in team_ids else 2

    def is_game_over(self) -> bool:
        team_ids = {u.team_id for u in self.game_board.units}
        return not (1 in team_ids and 2 in team_ids)

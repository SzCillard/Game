from __future__ import annotations

import copy
from typing import Optional, Tuple

from backend.board import GameState, TileType
from backend.units import Unit
from utils.constants import DAMAGE_DISPLAY_TIME, EPSILON
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
        self.gs = game_state

    def clone(self):
        return copy.deepcopy(self)

    # ------------------------------
    # Movement & Combat
    # ------------------------------

    def get_movable_tiles(self, unit: Unit) -> list[Tuple[int, int]]:
        """
        Get all possible (x, y) tiles that a given unit can move to.

        Args:
            unit (Unit): The unit whose movement range to compute.

        Returns:
            list[tuple[int, int]]: A list of valid coordinates.
        """
        tiles: list[Tuple[int, int]] = []
        for x in range(self.gs.width):
            for y in range(self.gs.height):
                if self.can_move(unit, x, y):
                    tiles.append((x, y))
        return tiles

    def get_attackable_tiles(self, unit: Unit) -> list[Tuple[int, int]]:
        """
        Get all tiles containing enemy units that the given unit can attack.

        Args:
            unit (Unit): The attacking unit.

        Returns:
            list[tuple[int, int]]: Positions of enemy units in range.
        """
        tiles: list[Tuple[int, int]] = []
        for target in self.gs.units:
            if self.can_attack(unit, target):
                tiles.append((target.x, target.y))
        return tiles

    def get_legal_actions(self, game_state, team) -> list[dict]:
        actions = []
        units = [
            u
            for u in self.gs.units
            if u.team == team and not u.has_acted and u.move_points > EPSILON
        ]

        for unit in units:
            # Moves
            movable_tiles = self.get_movable_tiles(unit)
            for x, y in movable_tiles:
                actions.append({"unit_id": unit.id, "type": "move", "target": (x, y)})

            # Attacks
            attackable_tiles = self.get_attackable_tiles(unit)
            for x, y in attackable_tiles:
                defender = self.gs.get_unit_at(x, y)
                if defender:
                    actions.append(
                        {"unit_id": unit.id, "type": "attack", "target": defender.id}
                    )

            # Always allow wait/pass (finish action)
            actions.append({"unit_id": unit.id, "type": "wait", "target": None})

        return actions

    """
    def get_legal_actions_from_snapshot(self, game_state_snapshot, team) -> list[dict]:
        actions = []

        # units structured like snapshot["units"]
        units = [
            u for u in game_state_snapshot["units"]
            if int(u["team"]) == int(team)
            and not u["has_acted"]
            and u["move_points"] > 0
        ]

        for unit in units:
            ux, uy = unit["x"], unit["y"]

            # MOVES
            for x in range(game_state_snapshot["width"]):
                for y in range(game_state_snapshot["height"]):
                    if self._can_move_snapshot(game_state_snapshot, unit, x, y):
                        actions.append({
                            "unit_id": unit["id"],
                            "type": "move",
                            "target": (x, y)
                        })

            # ATTACKS
            for enemy in game_state_snapshot["units"]:
                if enemy["team"] != team and enemy["health"] > 0:
                    if abs(enemy["x"] - ux) + abs(enemy["y"] - uy)
                    <= max(1, unit["attack_range"]):
                        actions.append({
                            "unit_id": unit["id"],
                            "type": "attack",
                            "target": enemy["id"]
                        })

            # WAIT action
            actions.append({
                "unit_id": unit["id"],
                "type": "wait",
                "target": None
            })

        return actions
    """

    def can_move(self, unit: Unit, to_x: int, to_y: int) -> bool:
        """
        Determine if a unit can move to a target tile.

        Args:
            unit (Unit): The unit attempting to move.
            to_x (int): Target x-coordinate.
            to_y (int): Target y-coordinate.

        Returns:
            bool: True if the move is valid, False otherwise.
        """
        # --- Boundary and occupancy checks ---
        if not self.gs.in_bounds(to_x, to_y):
            return False
        if self.gs.get_unit_at(to_x, to_y) is not None:
            return False
        if self.gs.tile(to_x, to_y) == TileType.MOUNTAIN:
            return False
        if unit.has_attacked:  # cannot move after attacking
            return False

        # --- Pathfinding-based cost check ---
        cost = compute_min_cost_gs(self.gs, (unit.x, unit.y), (to_x, to_y))
        return cost <= unit.move_points

    def move_unit(self, unit: Unit, to_x: int, to_y: int) -> bool:
        """
        Move a unit to a target location if possible.

        Args:
            unit (Unit): The unit to move.
            to_x (int): Destination x-coordinate.
            to_y (int): Destination y-coordinate.

        Returns:
            bool: True if movement succeeded, False otherwise.
        """
        if not self.can_move(unit, to_x, to_y):
            logger(f"{unit.name} cannot move there [{to_x};{to_y}].")
            return False

        cost = compute_min_cost_gs(self.gs, (unit.x, unit.y), (to_x, to_y))
        if cost > unit.move_points:
            logger(f"{unit.name} does not have enough movement points.")
            return False

        # --- Execute move ---
        unit.x = to_x
        unit.y = to_y
        unit.move_points = max(0.0, round(unit.move_points - cost, 3))

        # Automatically mark unit as done if no movement points left
        if unit.move_points <= EPSILON:
            unit.has_acted = True

        logger(
            f"{unit.name} moved to ({to_x},{to_y}), points left: {unit.move_points}."
        )
        return True

    def can_attack(self, attacker: Unit, defender: Unit) -> bool:
        """
        Check whether an attack is possible between two units.

        Args:
            attacker (Unit): The attacking unit.
            defender (Unit): The defending unit.

        Returns:
            bool: True if attack is possible, False otherwise.
        """
        if attacker.team == defender.team:
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
        dmg = calculate_damage(attacker, defender, self.gs)

        # Store damage data for UI animation
        defender.last_damage = dmg
        defender.damage_timer = DAMAGE_DISPLAY_TIME

        if attacker.attack_range > 1:
            # Ranged attack — no retaliation
            defender.health -= dmg
            logger(f"{attacker.name} shot {defender.name} for {dmg}.")
        else:
            # Melee — defender can retaliate if still alive
            defender.health -= dmg
            logger(f"{attacker.name} hit {defender.name} for {dmg}.")
            if defender.health > 0:
                retaliation = calculate_damage(defender, attacker)
                attacker.health -= retaliation
                if retaliation > 0:
                    logger(f"{defender.name} retaliated for {retaliation}.")

        # --- Finalize attack ---
        attacker.has_attacked = True
        attacker.move_points = 0
        self.gs.remove_dead()
        return True

    def update_damage_timers(self) -> None:
        """
        Update and decrease the damage text timers for all units.

        Used by renderer to fade out damage numbers over time.
        """
        for u in self.gs.units:
            if hasattr(u, "damage_timer") and u.damage_timer > 0:
                u.damage_timer = max(0, u.damage_timer - 1)
                if u.damage_timer == 0:
                    u.last_damage = 0

    # ------------------------------
    # Turn Flow Helpers
    # ------------------------------

    def turn_begin_reset(self, team: int) -> None:
        """
        Reset movement and action flags for all units at the start of their team's turn.

        Args:
            team (int): The team whose turn begins.
        """
        for u in self.gs.units:
            if u.team == team:
                u.move_points = u.move_range
                u.has_attacked = False
                u.has_acted = False

    def turn_check_end(self, team: int) -> bool:
        """
        Check if all units on a team have completed their actions.

        Args:
            team (int): Team ID to check.

        Returns:
            bool: True if all units have acted, False otherwise.
        """
        units = [u for u in self.gs.units if u.team == team]
        for u in units:
            if u.move_points <= EPSILON:
                u.has_acted = True
        return all(u.has_acted for u in units)

    def get_winner(self) -> Optional[int]:
        """
        Determine the winner based on remaining units.

        Returns:
            Optional[int]:
                - 1 → Player (Team 1) wins
                - 2 → AI (Team 2) wins
                - 0 → Draw
                - None → Game still ongoing
        """
        teams = {u.team for u in self.gs.units}
        if 1 in teams and 2 in teams:
            return None
        if 1 not in teams and 2 not in teams:
            return 0  # Draw
        return 1 if 1 in teams else 2

    def is_game_over(self) -> bool:
        """
        Check whether the game has reached an end state.

        Returns:
            bool: True if one or both teams have no units left.
        """
        teams = {u.team for u in self.gs.units}
        return not (1 in teams and 2 in teams)

    # ------------------------------
    # AI Turn Runner
    # ------------------------------

    def run_ai_turn(self, agent, ai_team: int) -> None:
        """
        Execute a full AI turn, allowing each AI-controlled unit to act once.

        Args:
            agent: The AI agent object with a `decide_next_action` method.
            ai_team (int): The numeric team ID for the AI.
        """
        ai_units = [
            u
            for u in self.gs.units
            if u.team == ai_team and not u.has_acted and u.move_points > EPSILON
        ]

        for unit in ai_units:
            while unit.move_points > EPSILON and not unit.has_acted:
                # Snapshot used for AI decision-making
                snapshot = self.gs.get_snapshot()
                action = agent.decide_next_action(snapshot, ai_team)

                # No available action
                if not action:
                    unit.has_acted = True
                    break

                # --- Handle AI decisions ---
                if action["type"] == "move":
                    nx, ny = action["target"]
                    if not self.move_unit(unit, nx, ny):
                        unit.has_acted = True
                        break

                elif action["type"] == "attack":
                    defender = next(
                        (u for u in self.gs.units if u.id == action["target"]), None
                    )
                    if defender:
                        self.apply_attack(unit, defender)
                    unit.has_acted = True
                    break

# backend/logic.py
from typing import Optional, Tuple

from backend.board import GameState, TileType
from backend.units import Unit
from utils.constants import EPSILON
from utils.helpers import compute_min_cost_gs, manhattan
from utils.messages import add_message


class GameLogic:
    def __init__(self, game_state: GameState):
        self.gs = game_state

    # ------------------------------
    # Movement & Combat
    # ------------------------------

    def get_movable_tiles(self, unit) -> list[Tuple[int, int]]:
        """Return all (x,y) positions unit can move to."""
        tiles = []
        for x in range(self.gs.width):
            for y in range(self.gs.height):
                if self.can_move(unit, x, y):
                    tiles.append((x, y))
        return tiles

    def get_attackable_tiles(self, unit) -> list[Tuple[int, int]]:
        """Return all (x,y) positions unit can attack."""
        tiles = []
        for target in self.gs.units:
            if self.can_attack(unit, target):
                tiles.append((target.x, target.y))
        return tiles

    def can_move(self, unit: Unit, to_x: int, to_y: int) -> bool:
        if not self.gs.in_bounds(to_x, to_y):
            return False
        if self.gs.get_unit_at(to_x, to_y) is not None:
            return False
        if self.gs.tile(to_x, to_y) == TileType.MOUNTAIN:
            return False
        if unit.has_attacked:  # cannot move after attacking
            return False

        cost = compute_min_cost_gs(self.gs, (unit.x, unit.y), (to_x, to_y))
        return cost <= unit.move_points

    def move_unit(self, unit: Unit, to_x: int, to_y: int) -> bool:
        if not self.can_move(unit, to_x, to_y):
            add_message(f"{unit.name} cannot move there [{to_x};{to_y}].")
            return False

        cost = compute_min_cost_gs(self.gs, (unit.x, unit.y), (to_x, to_y))
        if cost > unit.move_points:
            add_message(f"{unit.name} does not have enough movement points.")
            return False

        unit.x = to_x
        unit.y = to_y
        unit.move_points = max(0.0, round(unit.move_points - cost, 3))
        if unit.move_points <= EPSILON:
            unit.has_acted = True

        add_message(
            f"{unit.name} moved to ({to_x},{to_y}), points left: {unit.move_points}."
        )
        return True

    def can_attack(self, attacker: Unit, defender: Unit) -> bool:
        if attacker.team == defender.team:
            return False
        return manhattan(attacker.x, attacker.y, defender.x, defender.y) <= max(
            1, attacker.attack_range
        )

    def apply_attack(self, attacker: Unit, defender: Unit) -> bool:
        if attacker.has_attacked or not self.can_attack(attacker, defender):
            return False

        if attacker.attack_range > 1:  # ranged (no retaliation)
            dmg = max(0, attacker.attack_power - getattr(defender, "armor", 0))
            defender.health -= dmg
            add_message(f"{attacker.name} shot {defender.name} for {dmg}.")
        else:  # melee with retaliation
            att = max(0, attacker.attack_power - getattr(defender, "armor", 0))
            defender.health -= att
            add_message(f"{attacker.name} hit {defender.name} for {att}.")
            if defender.health > 0:  # only retaliate if alive
                deff = max(0, defender.attack_power - getattr(attacker, "armor", 0))
                attacker.health -= deff
                if deff > 0:
                    add_message(f"{defender.name} retaliated for {deff}.")

        attacker.has_attacked = True
        attacker.move_points = 0
        self.gs.remove_dead()
        return True

    # ------------------------------
    # Turn Flow Helpers
    # ------------------------------

    def turn_begin_reset(self, team: int) -> None:
        for u in self.gs.units:
            if u.team == team:
                u.move_points = u.move_range
                u.has_attacked = False
                u.has_acted = False

    def turn_check_end(self, team: int) -> bool:
        units = [u for u in self.gs.units if u.team == team]
        for u in units:
            if u.move_points <= EPSILON:
                u.has_acted = True
        return all(u.has_acted for u in units)

    def get_winner(self) -> Optional[int]:
        teams = {u.team for u in self.gs.units}
        if 1 in teams and 2 in teams:
            return None
        if 1 not in teams and 2 not in teams:
            return 0  # draw
        return 1 if 1 in teams else 2

    def is_game_over(self) -> bool:
        teams = {u.team for u in self.gs.units}
        return not (1 in teams and 2 in teams)

    # ------------------------------
    # AI Turn Runner
    # ------------------------------

    def run_ai_turn(self, agent, ai_team: int) -> None:
        ai_units = [
            u
            for u in self.gs.units
            if u.team == ai_team and not u.has_acted and u.move_points > EPSILON
        ]

        for unit in ai_units:
            while unit.move_points > EPSILON and not unit.has_acted:
                snapshot = self.gs.get_snapshot()
                action = agent.decide_next_action(snapshot, ai_team)

                if not action:
                    unit.has_acted = True
                    break

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

# backend/logic.py
from typing import Optional

from backend.board import GameState, TileType
from backend.units import Unit
from utils.helpers import compute_min_cost_gs, manhattan
from utils.messages import add_message


def can_move(unit: Unit, gs: GameState, to_x: int, to_y: int) -> bool:
    """
    Check if the unit can move to (to_x, to_y) within its remaining move_points,
    considering terrain costs and blocking units.
    """
    if not gs.in_bounds(to_x, to_y):
        return False
    if gs.get_unit_at(to_x, to_y) is not None:
        return False
    if gs.tile(to_x, to_y) == TileType.MOUNTAIN:
        return False

    # if unit has already attacked this turn, it cannot move
    if getattr(unit, "has_attacked"):
        return False

    remaining = getattr(unit, "move_points", unit.move_range)
    cost = compute_min_cost_gs(gs, (unit.x, unit.y), (to_x, to_y))
    return cost <= remaining


def move_unit(unit: Unit, gs: GameState, to_x: int, to_y: int) -> bool:
    if not can_move(unit, gs, to_x, to_y):
        add_message(f"{unit.name} cannot move there [{to_x};{to_y}].")
        return False

    cost = compute_min_cost_gs(gs, (unit.x, unit.y), (to_x, to_y))
    if cost > unit.move_points:
        add_message(f"{unit.name} does not have enough movement points.")
        return False

    unit.x = to_x
    unit.y = to_y
    unit.move_points = max(0.0, round(unit.move_points - cost, 3))
    if unit.move_points == 0.0:
        unit.has_acted = True

    add_message(
        f"{unit.name} moved to ({to_x},{to_y}), points left: {unit.move_points}."
    )
    return True


def can_attack(attacker: Unit, defender: Unit) -> bool:
    if attacker.team == defender.team:
        return False
    return manhattan(attacker.x, attacker.y, defender.x, defender.y) <= max(
        1, attacker.attack_range
    )


def apply_attack(attacker: Unit, defender: Unit, gs: GameState) -> bool:
    if getattr(attacker, "has_attacked", False):
        return False
    if not can_attack(attacker, defender):
        return False

    if attacker.attack_range > 1:  # ranged
        dmg = max(0, attacker.attack_power - getattr(defender, "armor", 0))
        defender.health -= dmg
        add_message(f"{attacker.name} shot {defender.name} for {dmg}.")
    else:  # melee
        att = max(0, attacker.attack_power - getattr(defender, "armor", 0))
        deff = max(0, defender.attack_power - getattr(attacker, "armor", 0))
        defender.health -= att
        attacker.health -= deff
        add_message(f"{attacker.name} hit {defender.name} for {att}.")
        if deff > 0:
            add_message(f"{defender.name} retaliated for {deff}.")

    # Attacking consumes any remaining movement this turn
    attacker.has_attacked = True
    attacker.move_points = 0
    gs.remove_dead()
    return True


def turn_begin_reset(gs: GameState, team: int) -> None:
    for u in gs.units:
        if u.team == team:
            u.move_points = u.move_range
            u.has_attacked = False
            u.has_acted = False


def check_victory(gs: GameState) -> Optional[int]:
    teams = {u.team for u in gs.units}
    if 1 in teams and 2 in teams:
        return None
    if 1 not in teams and 2 not in teams:
        return 0  # draw
    return 1 if 1 in teams else 2

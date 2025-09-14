# backend/logic.py
from typing import Optional

from backend.board import GameState, TileType
from backend.units import Unit
from utils.helpers import distance
from utils.messages import add_message


def can_move(unit: Unit, gs: GameState, to_x: int, to_y: int) -> bool:
    if unit.has_acted:
        return False
    if not gs.in_bounds(to_x, to_y):
        return False
    if gs.get_unit_at(to_x, to_y) is not None:
        return False
    if gs.tile(to_x, to_y) == TileType.MOUNTAIN:
        return False

    dist = distance(unit.x, unit.y, to_x, to_y)
    cost = dist + (1 if gs.tile(to_x, to_y) == TileType.WATER else 0)
    return cost <= unit.move_range


def move_unit(unit: Unit, gs: GameState, to_x: int, to_y: int) -> bool:
    if can_move(unit, gs, to_x, to_y):
        unit.x = to_x
        unit.y = to_y
        unit.has_acted = True
        add_message(f"{unit.name} moved to ({to_x},{to_y}).")
        return True
    add_message(f"{unit.name} cannot move there.")
    return False


def can_attack(attacker: Unit, defender: Unit) -> bool:
    if attacker.team == defender.team:
        return False
    return distance(attacker.x, attacker.y, defender.x, defender.y) <= max(
        1, attacker.attack_range
    )


def apply_attack(attacker: Unit, defender: Unit, gs: GameState) -> bool:
    if attacker.has_acted:
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

    attacker.has_acted = True
    gs.remove_dead()
    return True


def turn_begin_reset(gs: GameState, team: int):
    for u in gs.units:
        if u.team == team:
            u.has_acted = False


def check_victory(gs: GameState) -> Optional[int]:
    teams = {u.team for u in gs.units}
    if 1 in teams and 2 in teams:
        return None
    if 1 not in teams and 2 not in teams:
        return 0  # draw
    return 1 if 1 in teams else 2

# backend/units.py
from abc import ABC

from utils.constants import UnitType


class Unit(ABC):
    _id_counter = 0  # unique ID generator

    def __init__(
        self,
        name: UnitType,
        x: int,
        y: int,
        team: int,
        health: int,
        attack_power: int,
        attack_range: int,
        move_range: int,
    ):
        Unit._id_counter += 1
        self.id = Unit._id_counter
        self.name = name
        self.x = x
        self.y = y
        self.team = team
        self.health = health
        self.attack_power = attack_power
        self.attack_range = attack_range
        self.move_range = move_range
        self.has_acted = False


class Swordsman(Unit):
    def __init__(self, x, y, team):
        super().__init__(
            name=UnitType.SWORDSMAN,
            x=x,
            y=y,
            team=team,
            health=12,
            attack_power=4,
            attack_range=1,
            move_range=2,
        )


class Archer(Unit):
    def __init__(self, x, y, team):
        super().__init__(
            name=UnitType.ARCHER,
            x=x,
            y=y,
            team=team,
            health=8,
            attack_power=5,
            attack_range=3,
            move_range=3,
        )

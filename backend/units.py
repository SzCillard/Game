# backend/units.py
from abc import ABC

from utils.constants import TeamType, UnitType


class Unit(ABC):
    _id_counter = 0  # unique ID generator

    def __init__(
        self,
        name: UnitType,
        x: int,
        y: int,
        team: TeamType,
        health: int,
        armor: int,
        attack_power: int,
        attack_range: int,
        move_range: float,
    ):
        Unit._id_counter += 1
        self.id: int = Unit._id_counter
        self.name: str = name.value
        self.x: int = x
        self.y: int = y
        self.team: TeamType = team
        self.health: int = health
        self.armor: int = armor
        self.attack_power: int = attack_power
        self.attack_range: int = attack_range
        self.move_range: float = move_range

        # Per-turn state
        self.move_points: float = move_range  # reset at start of turn
        self.has_attacked: bool = False  # has the unit attacked this turn?
        self.has_acted: bool = False  # generic flag if unit already acted


class Swordsman(Unit):
    def __init__(self, x: int, y: int, team: TeamType):
        super().__init__(
            name=UnitType.SWORDSMAN,
            x=x,
            y=y,
            team=team,
            health=20,
            armor=4,
            attack_power=6,
            attack_range=1,
            move_range=2.0,
        )


class Archer(Unit):
    def __init__(self, x: int, y: int, team: TeamType):
        super().__init__(
            name=UnitType.ARCHER,
            x=x,
            y=y,
            team=team,
            health=12,
            armor=2,
            attack_power=5,
            attack_range=3,
            move_range=3.0,
        )


class Horseman(Unit):
    def __init__(self, x: int, y: int, team: TeamType):
        super().__init__(
            name=UnitType.HORSEMAN,
            x=x,
            y=y,
            team=team,
            health=15,
            armor=6,
            attack_power=6,
            attack_range=1,
            move_range=4.0,
        )


class Spearman(Unit):
    def __init__(self, x: int, y: int, team: TeamType):
        super().__init__(
            name=UnitType.SPEARMAN,
            x=x,
            y=y,
            team=team,
            health=10,
            armor=7,
            attack_power=5,
            attack_range=1,
            move_range=2.0,
        )

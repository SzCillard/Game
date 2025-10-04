# backend/units.py
from abc import ABC

from utils.constants import UNIT_STATS, TeamType, UnitType


class Unit(ABC):
    _id_counter = 0  # unique ID generator

    def __init__(
        self,
        name: UnitType,
        x: int,
        y: int,
        team: TeamType,
        max_hp: int,
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
        self.max_hp: int = health  # set by subclass
        self.health: int = health
        self.armor: int = armor
        self.attack_power: int = attack_power
        self.attack_range: int = attack_range
        self.move_range: float = move_range

        # Per-turn state
        self.move_points: float = move_range  # reset at start of turn
        self.has_attacked: bool = False  # has the unit attacked this turn?
        self.has_acted: bool = False  # generic flag if unit already acted

        # Temporary info
        self.last_damage = 0
        self.damage_timer = 0


class Swordsman(Unit):
    def __init__(self, x: int, y: int, team: TeamType):
        stats = UNIT_STATS["Swordsman"]
        super().__init__(
            name=UnitType.SWORDSMAN,
            x=x,
            y=y,
            team=team,
            max_hp=stats["health"],
            health=stats["health"],
            armor=stats["armor"],
            attack_power=stats["attack_power"],
            attack_range=stats["attack_range"],
            move_range=stats["move_range"],
        )


class Archer(Unit):
    def __init__(self, x: int, y: int, team: TeamType):
        stats = UNIT_STATS["Archer"]
        super().__init__(
            name=UnitType.ARCHER,
            x=x,
            y=y,
            team=team,
            max_hp=stats["health"],
            health=stats["health"],
            armor=stats["armor"],
            attack_power=stats["attack_power"],
            attack_range=stats["attack_range"],
            move_range=stats["move_range"],
        )


class Horseman(Unit):
    def __init__(self, x: int, y: int, team: TeamType):
        stats = UNIT_STATS["Horseman"]
        super().__init__(
            name=UnitType.HORSEMAN,
            x=x,
            y=y,
            team=team,
            max_hp=stats["health"],
            health=stats["health"],
            armor=stats["armor"],
            attack_power=stats["attack_power"],
            attack_range=stats["attack_range"],
            move_range=stats["move_range"],
        )


class Spearman(Unit):
    def __init__(self, x: int, y: int, team: TeamType):
        stats = UNIT_STATS["Spearman"]
        super().__init__(
            name=UnitType.SPEARMAN,
            x=x,
            y=y,
            team=team,
            max_hp=stats["health"],
            health=stats["health"],
            armor=stats["armor"],
            attack_power=stats["attack_power"],
            attack_range=stats["attack_range"],
            move_range=stats["move_range"],
        )

# utils/constants.py
from enum import Enum, IntEnum


class Color(Enum):
    # Basic palette
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (150, 150, 150)
    LIGHT_GRAY = (230, 230, 230)
    DARK_GRAY = (60, 60, 60)

    RED = (200, 50, 50)
    GREEN = (0, 200, 0)
    YELLOW = (255, 230, 80)
    BLUE = (0, 150, 255)
    CYAN = (0, 153, 153)

    # Optional: highlights, terrain tints
    GRASS = (153, 204, 140)
    HILL = (195, 205, 170)
    MOUNTAIN = (140, 140, 140)
    WATER = (0, 153, 153)


class UnitType(Enum):
    SWORDSMAN = "Swordsman"
    ARCHER = "Archer"
    SPEARMAN = "Spearman"
    HORSEMAN = "Horseman"


class TeamType(IntEnum):
    PLAYER = 1
    AI = 2


class TileType(IntEnum):
    PLAIN = 0
    HILL = 1
    MOUNTAIN = 2
    WATER = 3


class TileHighlightType(IntEnum):
    MOVE = 1
    ATTACK = 2
    BOTH = 3


UNIT_STATS = {
    "Swordsman": {
        "health": 110,
        "armor": 40,
        "attack_power": 50,
        "attack_range": 1,
        "move_range": 2.0,
    },
    "Archer": {
        "health": 70,
        "armor": 15,
        "attack_power": 45,
        "attack_range": 3,
        "move_range": 3.0,
    },
    "Horseman": {
        "health": 100,
        "armor": 30,
        "attack_power": 50,
        "attack_range": 1,
        "move_range": 4.0,
    },
    "Spearman": {
        "health": 110,
        "armor": 35,
        "attack_power": 50,
        "attack_range": 1,
        "move_range": 2.0,
    },
}


# Effectiveness multipliers: attacker -> defender
EFFECTIVENESS = {
    "Archer": {"Swordsman": 1.0, "Horseman": 0.8, "Spearman": 1.0},
    "Swordsman": {"Archer": 1.0, "Horseman": 1.0, "Spearman": 1.0},
    "Horseman": {"Archer": 1.3, "Swordsman": 1.1, "Spearman": 0.8},
    "Spearman": {"Archer": 1.0, "Swordsman": 0.8, "Horseman": 1.3},
}

DAMAGE_DISPLAY_TIME = 30  # frames to show the number

TERRAIN_MOVE_COST = {
    TileType.PLAIN: 1,
    TileType.HILL: 2,  # slows
    TileType.MOUNTAIN: 9999,  # impassable
    TileType.WATER: 2,  # slows
}

GRID_W, GRID_H = 15, 15
CELL_SIZE = 50
SCREEN_W, SCREEN_H = GRID_W * CELL_SIZE, GRID_H * CELL_SIZE
SIDEBAR_WIDTH = 200
FPS = 60

TEAM_COLORS = {
    TeamType.PLAYER: Color.BLUE.value,
    TeamType.AI: Color.RED.value,
}

TILE_COLORS = {
    TileType.PLAIN: Color.GRASS.value,
    TileType.HILL: Color.HILL.value,
    TileType.MOUNTAIN: Color.MOUNTAIN.value,
    TileType.WATER: Color.WATER.value,
}
TILE_HIGHLIGHT_COLOR = {
    TileHighlightType.MOVE: (100, 150, 255),
    TileHighlightType.ATTACK: (255, 100, 100),
    TileHighlightType.BOTH: (255, 100, 255),
}

GRID_COLOR = (50, 90, 50)
HP_BG = (0, 0, 0)
HP_FG = (255, 255, 255)


DIRS = (
    (1, 0),
    (-1, 0),
    (0, 1),
    (0, -1),
    (1, 1),
    (-1, -1),
    (1, -1),
    (-1, 1),
)

EPSILON = 0.6  # tolerance for float movement points

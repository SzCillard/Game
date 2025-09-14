# utils/constants.py
from enum import Enum, IntEnum


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


TERRAIN_MOVE_COST = {
    TileType.PLAIN: 1,
    TileType.HILL: 1,
    TileType.MOUNTAIN: 9999,  # impassable
    TileType.WATER: 2,  # slows
}

GRID_W, GRID_H = 15, 15
CELL_SIZE = 48
SCREEN_W, SCREEN_H = GRID_W * CELL_SIZE, GRID_H * CELL_SIZE
FPS = 60

TEAM_COLORS = {
    TeamType.PLAYER: (0, 150, 255),
    TeamType.AI: (200, 50, 50),
}

TILE_COLORS = {
    TileType.PLAIN: (210, 220, 210),
    TileType.HILL: (195, 205, 170),
    TileType.MOUNTAIN: (140, 140, 140),
    TileType.WATER: (150, 180, 220),
}

GRID_COLOR = (50, 90, 50)
HP_BG = (0, 0, 0)
HP_FG = (255, 255, 255)

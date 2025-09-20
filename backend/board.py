# backend/board.py
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.units import Unit
from utils.constants import TERRAIN_MOVE_COST, TileType


@dataclass
class GameState:
    width: int
    height: int
    cell_size: int
    tile_map: List[List[TileType]] = field(default_factory=list)
    units: List[Unit] = field(default_factory=list)

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def tile(self, x: int, y: int) -> TileType:
        return self.tile_map[y][x]

    def is_passable(self, x: int, y: int) -> bool:
        return (
            self.in_bounds(x, y)
            and TERRAIN_MOVE_COST[self.tile(x, y)] < 9999
            and self.get_unit_at(x, y) is None
        )

    def move_cost(self, x: int, y: int) -> int:
        return TERRAIN_MOVE_COST[self.tile(x, y)]

    def add_unit(self, unit: Unit) -> None:
        # initialise per-turn movement/attack state on the unit
        setattr(unit, "move_points", getattr(unit, "move_range", 0))
        setattr(unit, "has_attacked", False)
        self.units.append(unit)

    def get_unit_at(self, x: int, y: int) -> Optional[Unit]:
        for u in self.units:
            if u.x == x and u.y == y:
                return u
        return None

    def get_snapshot(self) -> Dict[str, Any]:
        """
        UI/AI snapshot. Tiles are TileType entries, units is a list of dicts.
        The unit dict contains both 'has_attacked' and 'move_points'
        (so UI can show availability).
        """
        return {
            "tiles": self.tile_map,
            "units": [
                {
                    "id": u.id,
                    "x": u.x,
                    "y": u.y,
                    "team": u.team,
                    "health": u.health,
                    "attack_power": u.attack_power,
                    "attack_range": u.attack_range,
                    "move_range": u.move_range,
                    "move_points": u.move_points,
                    "name": u.name,
                    "has_attacked": u.has_attacked,
                    # compatibility field used by existing UI logic:
                    "has_acted": u.has_acted,
                }
                for u in self.units
            ],
        }

    def remove_dead(self) -> None:
        self.units = [u for u in self.units if u.health > 0]

    def is_game_over(self) -> bool:
        teams = {u.team for u in self.units}
        return not (1 in teams and 2 in teams)

    def get_winner(self) -> str:
        teams = {u.team for u in self.units}
        if 1 in teams and 2 not in teams:
            return "Player"
        elif 2 in teams and 1 not in teams:
            return "AI"
        return "Draw"


def create_default_map(w: int, h: int) -> List[List[TileType]]:
    m: List[List[TileType]] = [[TileType.PLAIN for _ in range(w)] for _ in range(h)]
    # border hills
    for x in range(w):
        m[0][x] = TileType.HILL
        m[h - 1][x] = TileType.HILL
    # mountains diagonal
    for i in range(3, min(w, h) - 3, 4):
        if 0 <= i < w and 0 <= i < h:
            m[i][i] = TileType.MOUNTAIN
    # water column
    water_x = w // 2
    for y in range(2, h - 2):
        m[y][water_x] = TileType.WATER
    return m

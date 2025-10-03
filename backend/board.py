# backend/board.py
import random
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
                    "armor": u.armor,
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


def create_hilly_map(w: int, h: int) -> List[List[TileType]]:
    """Creates a map with many hills in the middle horizontally and
    a few scattered elsewhere."""
    # Start with a plain map
    m = [[TileType.PLAIN for _ in range(w)] for _ in range(h)]

    # Middle horizontal band of hills
    mid_h = h // 2
    band_height = 3  # 3 rows of hills centered at mid_h
    for y in range(mid_h - band_height // 2, mid_h + band_height // 2 + 1):
        for x in range(w):
            if random.random() < 0.8:  # 80% chance to be a hill
                m[y][x] = TileType.HILL

    # Scatter a few hills in other parts
    for _ in range((w * h) // 15):  # number of random hills
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 1)
        if m[y][x] == TileType.PLAIN:
            m[y][x] = TileType.HILL

    return m


def create_watery_map(w: int, h: int) -> List[List[TileType]]:
    """Several lakes and rivers."""
    m = [[TileType.PLAIN for _ in range(w)] for _ in range(h)]
    # horizontal river
    for x in range(2, w - 2):
        m[h // 2][x] = TileType.WATER
    # vertical river
    for y in range(3, h - 3):
        m[y][w // 3] = TileType.WATER
    return m


def create_mountainous_map(w: int, h: int) -> List[List[TileType]]:
    """Impassable mountains blocking areas."""
    m = [[TileType.PLAIN for _ in range(w)] for _ in range(h)]
    for i in range(min(w, h)):
        if i % 2 == 0 or i > 7 or i < 9:
            m[i][i] = TileType.MOUNTAIN
    return m


def create_mixed_map(w: int, h: int) -> List[List[TileType]]:
    """Balanced map with plains, hills, water, and some mountains in simple clusters."""
    m = [[TileType.PLAIN for _ in range(w)] for _ in range(h)]

    # --- Horizontal hills band in the middle ---
    mid_h = h // 2
    for y in range(mid_h - 1, mid_h + 2):  # 3 rows thick
        for x in range(w):
            if random.random() < 0.7:  # 70% chance to be a hill
                m[y][x] = TileType.HILL

    # --- Water clusters ---
    num_lakes = max(1, w * h // 50)
    for _ in range(num_lakes):
        lake_x = random.randint(0, w - 3)
        lake_y = random.randint(0, h - 3)
        for dy in range(3):
            for dx in range(3):
                if random.random() < 0.8:
                    m[lake_y + dy][lake_x + dx] = TileType.WATER

    # --- Mountain clusters ---
    num_mountains = max(1, w * h // 80)
    for _ in range(num_mountains):
        mount_x = random.randint(0, w - 2)
        mount_y = random.randint(0, h - 2)
        for dy in range(2):
            for dx in range(2):
                if random.random() < 0.7:
                    m[mount_y + dy][mount_x + dx] = TileType.MOUNTAIN

    return m


MAP_GENERATORS = {
    "hilly": create_hilly_map,
    "mixed": create_mixed_map,
}


def create_random_map(w: int, h: int) -> List[List[TileType]]:
    """Pick a random map type and generate it."""
    map_type = random.choice(list(MAP_GENERATORS.keys()))
    print(f"🌍 Using map type: {map_type}")
    return MAP_GENERATORS[map_type](w, h)

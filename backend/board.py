"""
backend/board.py

Defines the GameState class (the central board representation) and
various terrain generation utilities for maps (plains, hills, water, etc.).

Each GameState contains:
- Tile map (2D grid of TileType)
- List of units
- Utilities for querying and mutating the map state
"""

import copy
import random
from dataclasses import dataclass, field
from typing import Any, List, Optional

from backend.units import Archer, Horseman, Spearman, Swordsman, Unit
from utils.constants import TERRAIN_MOVE_COST, TeamType, TileType

# ======================================================================
# 🎯 Core Game State
# ======================================================================


@dataclass
class GameState:
    """
    Represents the full game board and all active units.

    Attributes:
        width (int): Width of the board in tiles.
        height (int): Height of the board in tiles.
        cell_size (int): Size of each tile in pixels (for rendering alignment).
        tile_map (list[list[TileType]]): 2D terrain grid (rows × columns).
        units (list[Unit]): All currently active units.
    """

    width: int
    height: int
    cell_size: int
    tile_map: List[List[TileType]] = field(default_factory=list)
    units: List[Unit] = field(default_factory=list)
    unit_classes = {
        "Swordsman": Swordsman,
        "Archer": Archer,
        "Horseman": Horseman,
        "Spearman": Spearman,
    }

    def clone(self):
        return copy.deepcopy(self)

    # ------------------------------
    # Basic Grid Operations
    # ------------------------------

    def in_bounds(self, x: int, y: int) -> bool:
        """Return True if coordinates are within map bounds."""
        return 0 <= x < self.width and 0 <= y < self.height

    def tile(self, x: int, y: int) -> TileType:
        """Return the terrain type at the given coordinates."""
        return self.tile_map[y][x]

    def is_passable(self, x: int, y: int) -> bool:
        """
        Check if a tile is traversable (not a mountain or water, no unit on it).

        Returns:
            bool: True if unit can pass, False otherwise.
        """
        return (
            self.in_bounds(x, y)
            and TERRAIN_MOVE_COST[self.tile(x, y)] < 9999
            and self.get_unit_at(x, y) is None
        )

    def move_cost(self, x: int, y: int) -> int:
        """
        Get the terrain movement cost of a tile.

        Returns:
            int: Movement cost (e.g. 1 = plain, 2 = hill, 9999 = mountain).
        """
        return TERRAIN_MOVE_COST[self.tile(x, y)]

    # ------------------------------
    # Unit Management
    # ------------------------------

    def add_units(
        self, unit_name_list: list[str], team_id: int, team: TeamType
    ) -> None:
        """
        Add units to the board and initialize their starting positions.
        - Player units spawn on the bottom-left area.
        - Enemy units spawn on the top-right area.
        - Units avoid impassable tiles and existing units.
        """
        spacing_x = 2
        spacing_y = 1
        units_per_row = 3

        # Define spawn zones
        if team_id == 1:
            start_x = 1
            start_y = self.height - 4  # Bottom rows
            x_dir = 1
            y_dir = 1
        else:
            start_x = self.width - 6  # Top rows, right side
            start_y = 1
            x_dir = 1
            y_dir = 1

        x, y = start_x, start_y

        for i, name in enumerate(unit_name_list):
            unit_class = self.unit_classes[name]

            # --- Find a nearby valid tile ---
            found = False
            for dy in range(-1, 3):  # small search window
                for dx in range(-1, 3):
                    tx, ty = x + dx, y + dy
                    if self.is_passable(tx, ty):
                        x, y = tx, ty
                        found = True
                        break
                if found:
                    break

            # --- Spawn unit ---
            new_unit = unit_class(x, y, team_id=team_id, team=team)
            new_unit.move_points = getattr(new_unit, "move_range", 0)
            new_unit.has_attacked = False
            self.units.append(new_unit)

            # --- Increment placement position ---
            x += spacing_x * x_dir
            if (i + 1) % units_per_row == 0:
                x = start_x
                y += spacing_y * y_dir

    def get_unit_at(self, x: int, y: int) -> Optional[Unit]:
        """
        Get the unit at a given tile, if any.

        Args:
            x (int): Tile x position.
            y (int): Tile y position.

        Returns:
            Optional[Unit]: Unit instance if found, None otherwise.
        """
        for u in self.units:
            if u.x == x and u.y == y:
                return u
        return None

    def get_snapshot(self) -> dict[str, Any]:
        """
        Return a simplified snapshot of the current game state.

        Used by UI and AI for rendering or decision-making.

        Returns:
            dict: Contains 'tiles' (2D map) and 'units' (serialized list).
        """
        return {
            "tiles": self.tile_map,
            "units": [
                {
                    "id": u.id,
                    "x": u.x,
                    "y": u.y,
                    "team_id": u.team_id,
                    "team": u.team,
                    "health": u.health,
                    "max_hp": getattr(u, "max_hp", u.health),
                    "armor": u.armor,
                    "attack_power": u.attack_power,
                    "attack_range": u.attack_range,
                    "move_range": u.move_range,
                    "move_points": u.move_points,
                    "name": u.name,
                    "has_attacked": u.has_attacked,
                    "has_acted": u.has_acted,
                    # Damage feedback info (for floating numbers in UI)
                    "last_damage": getattr(u, "last_damage", 0),
                    "damage_timer": getattr(u, "damage_timer", 0),
                }
                for u in self.units
            ],
        }

    def remove_dead(self) -> None:
        """Remove all units with health <= 0 from the board."""
        self.units = [u for u in self.units if u.health > 0]


# ======================================================================
# 🗺️ Map Generation Utilities
# ======================================================================


def create_default_map(w: int, h: int) -> List[List[TileType]]:
    """
    Create a default mixed terrain map with a diagonal mountain range
    and a central water column.
    """
    m: List[List[TileType]] = [[TileType.PLAIN for _ in range(w)] for _ in range(h)]

    # Border hills (top/bottom)
    for x in range(w):
        m[0][x] = TileType.HILL
        m[h - 1][x] = TileType.HILL

    # Diagonal mountains for variety
    for i in range(3, min(w, h) - 3, 4):
        if 0 <= i < w and 0 <= i < h:
            m[i][i] = TileType.MOUNTAIN

    # Vertical water barrier in center
    water_x = w // 2
    for y in range(2, h - 2):
        m[y][water_x] = TileType.WATER
    return m


def create_hilly_map(w: int, h: int) -> List[List[TileType]]:
    """
    Generate a map with a thick horizontal band of hills across the center
    and some scattered hill tiles elsewhere.
    """
    m = [[TileType.PLAIN for _ in range(w)] for _ in range(h)]

    # Middle horizontal band of hills
    mid_h = h // 2
    band_height = 3  # rows thick
    for y in range(mid_h - band_height // 2, mid_h + band_height // 2 + 1):
        for x in range(w):
            if random.random() < 0.8:  # 80% chance hill
                m[y][x] = TileType.HILL

    # Scatter extra hills for variation
    for _ in range((w * h) // 15):
        x, y = random.randrange(w), random.randrange(h)
        if m[y][x] == TileType.PLAIN:
            m[y][x] = TileType.HILL

    return m


def create_watery_map(w: int, h: int) -> List[List[TileType]]:
    """
    Generate a map dominated by rivers and lakes.

    Features:
    - Horizontal river at mid-height
    - Vertical river roughly 1/3 into map width
    """
    m = [[TileType.PLAIN for _ in range(w)] for _ in range(h)]

    # Horizontal river
    for x in range(2, w - 2):
        m[h // 2][x] = TileType.WATER

    # Vertical river
    for y in range(3, h - 3):
        m[y][w // 3] = TileType.WATER
    return m


def create_mountainous_map(w: int, h: int) -> List[List[TileType]]:
    """
    Generate a map with mountains blocking movement in certain areas.
    """
    m = [[TileType.PLAIN for _ in range(w)] for _ in range(h)]
    for i in range(min(w, h)):
        if i % 2 == 0 or 7 < i < 9:
            m[i][i] = TileType.MOUNTAIN
    return m


def create_mixed_map(w: int, h: int) -> List[List[TileType]]:
    """
    Generate a balanced map with plains, hills, water, and mountains.

    - Hills form a horizontal band across the center.
    - Water and mountain clusters are scattered randomly.
    """
    m = [[TileType.PLAIN for _ in range(w)] for _ in range(h)]

    # --- Hills band ---
    mid_h = h // 2
    for y in range(mid_h - 1, mid_h + 2):
        for x in range(w):
            if random.random() < 0.7:
                m[y][x] = TileType.HILL

    # --- Water clusters (small lakes) ---
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


# ======================================================================
# 🧭 Map Type Dispatcher
# ======================================================================

MAP_GENERATORS = {
    "hilly": create_hilly_map,
    "mixed": create_mixed_map,
}


def create_random_map(w: int, h: int) -> List[List[TileType]]:
    """
    Randomly choose one of the available map generators.

    Args:
        w (int): Width in tiles.
        h (int): Height in tiles.

    Returns:
        list[list[TileType]]: Generated map grid.
    """
    map_type = random.choice(list(MAP_GENERATORS.keys()))
    print(f"🌍 Using map type: {map_type}")
    return MAP_GENERATORS[map_type](w, h)

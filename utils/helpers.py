# utils/helpers.py
import heapq
import math
import os
from typing import Any, Dict, List, Optional, Tuple

import pygame

from utils.constants import (
    DIRS,
    EFFECTIVENESS,
    HEALTH_INFLUENCE,
    TERRAIN_ATTACK_BONUS,
    TERRAIN_DEFENSE_BONUS,
    TERRAIN_MOVE_COST,
    TeamType,
    TileType,
    UnitType,
)


def pixel_to_grid(px: int, py: int, cell_size: int):
    return px // cell_size, py // cell_size


def manhattan(x1: int, y1: int, x2: int, y2: int) -> int:
    return abs(x1 - x2) + abs(y1 - y2)


def compute_min_cost_gs(gs, start: Tuple[int, int], goal: Tuple[int, int]) -> float:
    """
    Dijkstra / uniform-cost search on GameState 'gs' returning minimal movement cost
    from start -> goal (sum of tile move costs when entering a tile).
    Diagonal steps cost sqrt(2) * terrain cost.
    Returns a large number if unreachable.
    """
    sx, sy = start
    tx, ty = goal

    # If start and goal are the same tile → cost is zero
    if (sx, sy) == (tx, ty):
        return 0.0

    INF = 10**9  # effectively "infinity" for unreachable paths

    # Priority queue for Dijkstra: stores (cost_so_far, x, y)
    pq: List[Tuple[float, int, int]] = []
    heapq.heappush(pq, (0.0, sx, sy))

    # Dictionary to remember the best known cost to reach each tile
    best: Dict[Tuple[int, int], float] = {(sx, sy): 0.0}

    while pq:
        # Take the tile with the lowest cost seen so far
        cost, x, y = heapq.heappop(pq)

        # If we've reached the target → return the total cost
        if (x, y) == (tx, ty):
            return cost

        # Skip if this is not the best cost anymore (outdated entry in the PQ)
        if cost != best.get((x, y), INF):
            continue

        # Explore all 8 possible movement directions (DIRS must include diagonals)
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy

            # Ignore moves outside map boundaries
            if not gs.in_bounds(nx, ny):
                continue

            # Mountains are impassable
            if gs.tile(nx, ny) == TileType.MOUNTAIN:
                continue

            # Blocked if another unit is there, unless it's the target tile
            occupant = gs.get_unit_at(nx, ny)
            if occupant is not None and (nx, ny) != (tx, ty):
                continue

            # Base movement cost depends on the terrain type of the target tile
            step_cost = gs.move_cost(nx, ny)

            # TODO: refactor the if condition
            # If moving diagonally, apply sqrt(2) multiplier
            if dx != 0 and dy != 0:
                step_cost *= math.sqrt(2)

            # New total cost if we step onto this tile
            nc = cost + step_cost

            # Only update if this path is cheaper than any previously found
            if nc < best.get((nx, ny), INF):
                best[(nx, ny)] = nc
                heapq.heappush(pq, (nc, nx, ny))

    # If we exhaust the search without reaching the goal → unreachable
    return INF


def movement_cost_snapshot(
    snapshot: Dict[str, Any], start: Tuple[int, int], goal: Tuple[int, int]
) -> float:
    """
    Similar to compute_min_cost_gs but operates on the snapshot dict (tiles + units).
    Returns INF if unreachable. Diagonal steps cost sqrt(2) * terrain cost.
    """
    tiles: List[List[TileType]] = snapshot["tiles"]
    units: List[Dict[str, Any]] = snapshot["units"]
    W = len(tiles[0])
    H = len(tiles)

    sx, sy = start
    tx, ty = goal
    if (sx, sy) == (tx, ty):
        return 0.0

    def in_bounds(x: int, y: int) -> bool:
        return 0 <= x < W and 0 <= y < H

    def tile_at(x: int, y: int) -> TileType:
        return tiles[y][x]

    occupied = {(u["x"], u["y"]) for u in units if u["id"] is not None}

    INF = 10**9
    pq: List[Tuple[float, int, int]] = []
    heapq.heappush(pq, (0.0, sx, sy))
    best: Dict[Tuple[int, int], float] = {(sx, sy): 0.0}

    while pq:
        cost, x, y = heapq.heappop(pq)
        if (x, y) == (tx, ty):
            return cost
        if cost != best.get((x, y), INF):
            continue
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if not in_bounds(nx, ny):
                continue
            if tile_at(nx, ny) == TileType.MOUNTAIN:
                continue
            if (nx, ny) in occupied and (nx, ny) != (tx, ty):
                continue

            step_cost = TERRAIN_MOVE_COST[tile_at(nx, ny)]
            if dx != 0 and dy != 0:  # diagonal
                step_cost *= math.sqrt(2)

            nc = cost + step_cost
            if nc < best.get((nx, ny), INF):
                best[(nx, ny)] = nc
                heapq.heappush(pq, (nc, nx, ny))
    return INF


def next_step_toward_snapshot(
    snapshot: Dict[str, Any], start: Tuple[int, int], goal: Tuple[int, int]
) -> Optional[Tuple[int, int]]:
    """
    Compute the first step on a shortest-cost path from start to goal using snapshot.
    Returns (nx,ny) or None if unreachable or already at goal.
    Diagonal steps cost sqrt(2) * terrain cost.
    """
    tiles: List[List[TileType]] = snapshot["tiles"]
    units: List[Dict[str, Any]] = snapshot["units"]
    W = len(tiles[0])
    H = len(tiles)

    sx, sy = start
    tx, ty = goal
    if (sx, sy) == (tx, ty):
        return None

    def in_bounds(x: int, y: int) -> bool:
        return 0 <= x < W and 0 <= y < H

    def tile_at(x: int, y: int) -> TileType:
        return tiles[y][x]

    occupied = {(u["x"], u["y"]) for u in units}

    INF = 10**9
    pq: List[Tuple[float, int, int]] = []
    heapq.heappush(pq, (0.0, sx, sy))
    best: Dict[Tuple[int, int], float] = {(sx, sy): 0.0}
    parent: Dict[Tuple[int, int], Tuple[int, int]] = {}

    while pq:
        cost, x, y = heapq.heappop(pq)
        if (x, y) == (tx, ty):
            # reconstruct path
            cur = (tx, ty)
            path = []
            while cur != (sx, sy):
                path.append(cur)
                cur = parent[cur]
            path.reverse()
            return path[0] if path else None
        if cost != best.get((x, y), INF):
            continue
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if not in_bounds(nx, ny):
                continue
            if tile_at(nx, ny) == TileType.MOUNTAIN:
                continue
            if (nx, ny) in occupied and (nx, ny) != (tx, ty):
                continue

            step_cost = TERRAIN_MOVE_COST[tile_at(nx, ny)]
            if dx != 0 and dy != 0:  # diagonal
                step_cost *= math.sqrt(2)

            nc = cost + step_cost
            if nc < best.get((nx, ny), INF):
                best[(nx, ny)] = nc
                parent[(nx, ny)] = (x, y)
                heapq.heappush(pq, (nc, nx, ny))

    return None


def calculate_damage(attacker, defender, game_state=None):
    """Combined formula with armor %, type multipliers,
    health scaling, and terrain bonuses."""

    # --- 1) Base Power scaled by health ---

    ratio = attacker.health / attacker.max_hp
    health_factor = (1 - HEALTH_INFLUENCE) + HEALTH_INFLUENCE * ratio
    effective_power = attacker.attack_power * health_factor

    # --- 2) Armor as percentage reduction ---
    reduction = 100 / (100 + defender.armor * 10)  # e.g. armor 5 ≈ 33% reduction
    reduced = effective_power * reduction

    # --- 3) Type effectiveness (RPS multipliers) ---
    att_type = (
        attacker.name.name if hasattr(attacker.name, "name") else str(attacker.name)
    )
    def_type = (
        defender.name.name if hasattr(defender.name, "name") else str(defender.name)
    )

    type_mult = EFFECTIVENESS.get(att_type.capitalize(), {}).get(
        def_type.capitalize(), 1.0
    )

    # --- 4) Terrain modifiers ---
    atk_bonus = 0.0
    def_bonus = 0.0

    if game_state:
        try:
            atk_tile = game_state.tile_map[attacker.y][attacker.x]
            def_tile = game_state.tile_map[defender.y][defender.x]
            atk_bonus = TERRAIN_ATTACK_BONUS.get(atk_tile, 0.0)
            def_bonus = TERRAIN_DEFENSE_BONUS.get(def_tile, 0.0)
        except Exception:
            pass  # fallback if tiles missing (e.g. testing)

    terrain_mult = (1 + atk_bonus) * (1 - def_bonus)

    # --- 5) Final combined damage ---
    final_damage = reduced * type_mult * terrain_mult

    # Always at least 1 damage if it connects
    return max(1, int(final_damage))

    # ------------------------------
    # Image Loading
    # ------------------------------


def load_unit_images(cell_size: int):
    """
    Preload all unit images for both teams.

    Returns:
        dict: Nested dictionary of format:
              images[UnitType][TeamType] = pygame.Surface
    """
    images = {}
    base_path = os.path.join("assets/images")

    # Iterate over all defined unit types and team types
    for unit in UnitType:
        images[unit] = {}
        for team in TeamType:
            team_name = "purple" if team == TeamType.PLAYER else "red"
            path = os.path.join(
                base_path, unit.name.lower(), f"{unit.name.lower()}_{team_name}.png"
            )

            # Load and scale if exists, else use None
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (cell_size, cell_size))
                images[unit][team] = img
            else:
                print(f"⚠️ Missing image: {path}")
                images[unit][team] = None
    return images


def load_single_image(path: str, size: Tuple[int, int]) -> Optional[pygame.Surface]:
    """Load and scale a single image from the given path."""
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.scale(img, size)
        return img
    else:
        print(f"⚠️ Missing image: {path}")
        return None

import heapq
import math
from typing import Any, Dict, List, Optional, Tuple

from utils.constants import DIRS, TERRAIN_MOVE_COST, TileType


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

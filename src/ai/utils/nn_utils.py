# /ai/utils/nn_utils.py

from math import hypot
from typing import Any

import numpy as np

from utils.constants import TERRAIN_DEFENSE_BONUS, TERRAIN_MOVE_COST, TileType, UnitType


def _safe_mean(values):
    return float(np.mean(values)) if values else 0.0


def _safe_div(a, b):
    return a / b if b > 0 else 0.0


def _unit_dist(u1, u2):
    return float(hypot(u1["x"] - u2["x"], u1["y"] - u2["y"]))


def _count_type(units, unit_type_value: str):
    return sum(1 for u in units if unit_type_value.lower() in str(u["name"]).lower())


def encode_state(game_state: dict[str, Any], team_id: int) -> np.ndarray:
    units = game_state["units"]
    tiles = game_state["tiles"]

    ally = [u for u in units if u["team_id"] == team_id]
    enemy = [u for u in units if u["team_id"] != team_id]

    n_ally = len(ally)
    n_enemy = len(enemy)

    # ------------------------------------------------------------------
    # Board size & normalization helpers
    # ------------------------------------------------------------------
    board_h = len(tiles)
    board_w = len(tiles[0]) if board_h > 0 else 1
    max_dim = float(max(board_w, board_h, 1))

    def _dist(a, b) -> float:
        return float(hypot(a["x"] - b["x"], a["y"] - b["y"]))

    def _terrain_move_cost(x: int, y: int) -> float:
        if 0 <= y < board_h and 0 <= x < board_w:
            tile: TileType = tiles[y][x]
            return float(TERRAIN_MOVE_COST[tile])
        return 9999.0

    def _terrain_def_bonus(u: dict[str, Any]) -> float:
        tile: TileType = tiles[u["y"]][u["x"]]
        return float(TERRAIN_DEFENSE_BONUS[tile])

    # ------------------------------------------------------------------
    # 1. Global HP / mobility (similar to your original)
    # ------------------------------------------------------------------
    ally_hp = sum(u["health"] for u in ally)
    enemy_hp = sum(u["health"] for u in enemy)

    ally_max_hp = sum(u["max_hp"] for u in ally)
    enemy_max_hp = sum(u["max_hp"] for u in enemy)

    ally_hp_pct = _safe_div(ally_hp, ally_max_hp)
    enemy_hp_pct = _safe_div(enemy_hp, enemy_max_hp)
    hp_advantage = ally_hp_pct - enemy_hp_pct

    avg_move_pts_ally = _safe_mean([u["move_points"] for u in ally]) / 10.0
    avg_move_pts_enemy = _safe_mean([u["move_points"] for u in enemy]) / 10.0

    frac_ally_can_attack = _safe_mean([1 - int(u["has_attacked"]) for u in ally])
    frac_enemy_can_attack = _safe_mean([1 - int(u["has_attacked"]) for u in enemy])

    # ------------------------------------------------------------------
    # 2. Composition (keep your original idea)
    # ------------------------------------------------------------------
    ally_sword = _count_type(ally, UnitType.SWORDSMAN.value)
    ally_arch = _count_type(ally, UnitType.ARCHER.value)
    ally_horse = _count_type(ally, UnitType.HORSEMAN.value)
    ally_spear = _count_type(ally, UnitType.SPEARMAN.value)

    enemy_sword = _count_type(enemy, UnitType.SWORDSMAN.value)
    enemy_arch = _count_type(enemy, UnitType.ARCHER.value)
    enemy_horse = _count_type(enemy, UnitType.HORSEMAN.value)
    enemy_spear = _count_type(enemy, UnitType.SPEARMAN.value)

    comp = [
        _safe_div(ally_sword, n_ally),
        _safe_div(ally_arch, n_ally),
        _safe_div(ally_horse, n_ally),
        _safe_div(ally_spear, n_ally),
        _safe_div(enemy_sword, n_enemy),
        _safe_div(enemy_arch, n_enemy),
        _safe_div(enemy_horse, n_enemy),
        _safe_div(enemy_spear, n_enemy),
    ]

    # ------------------------------------------------------------------
    # 3. Per-unit tactical / local info
    # ------------------------------------------------------------------
    # closest enemy, can I hit, can they hit?
    def _closest_enemy_info_for_unit(u):
        if not enemy:
            return (1.0, 0.0, 0.0, 0.0, 0.0)

        dists = [(_dist(u, e), e) for e in enemy]
        d, e = min(dists, key=lambda x: x[0])

        d_norm = d / max_dim
        enemy_hp_pct = _safe_div(e["health"], e["max_hp"])
        enemy_armor_norm = e["armor"] / 100.0

        in_my_range = 1.0 if d <= u["attack_range"] else 0.0

        threatened = 0.0
        for en in enemy:
            if _dist(u, en) <= en["attack_range"]:
                threatened = 1.0
                break

        return (d_norm, enemy_hp_pct, enemy_armor_norm, in_my_range, threatened)

    if ally:
        arr = np.array(
            [_closest_enemy_info_for_unit(u) for u in ally], dtype=np.float32
        )
        closest_enemy_info = arr.mean(axis=0)
    else:
        closest_enemy_info = np.zeros(5, dtype=np.float32)

    # local ally / enemy density around allies (radius 3)
    def _nearby_count(u, group, radius: float) -> int:
        return sum(1 for o in group if o is not u and _dist(u, o) <= radius)

    if ally:
        ally_density = _safe_mean([_nearby_count(a, ally, 3.0) for a in ally])
        enemy_density = _safe_mean([_nearby_count(a, enemy, 3.0) for a in ally])
    else:
        ally_density = 0.0
        enemy_density = 0.0

    ally_density_norm = ally_density / 10.0
    enemy_density_norm = enemy_density / 10.0

    # ------------------------------------------------------------------
    # 4. Terrain influence (using your TILE / TERRAIN_* constants)
    # ------------------------------------------------------------------
    def _avg_local_move_cost(group):
        vals: list[float] = []
        for u in group:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    x = u["x"] + dx
                    y = u["y"] + dy
                    c = _terrain_move_cost(x, y)
                    if c < 9999:
                        vals.append(c)
        return _safe_mean(vals)

    ally_move_cost = _avg_local_move_cost(ally)
    enemy_move_cost = _avg_local_move_cost(enemy)

    max_move_cost = max(TERRAIN_MOVE_COST.values()) or 1
    ally_move_cost_norm = ally_move_cost / max_move_cost
    enemy_move_cost_norm = enemy_move_cost / max_move_cost

    ally_def_bonus = _safe_mean([_terrain_def_bonus(u) for u in ally])
    enemy_def_bonus = _safe_mean([_terrain_def_bonus(u) for u in enemy])

    # ------------------------------------------------------------------
    # 5. Formation / spacing
    # ------------------------------------------------------------------
    def _center(group):
        if not group:
            return (0.0, 0.0)
        return (
            _safe_mean([u["x"] for u in group]) / max_dim,
            _safe_mean([u["y"] for u in group]) / max_dim,
        )

    acx, acy = _center(ally)
    ecx, ecy = _center(enemy)

    center_distance = hypot(acx - ecx, acy - ecy)  # already normalized

    def _dispersion(group, cx, cy):
        if not group:
            return 0.0
        return _safe_mean(
            [hypot(u["x"] / max_dim - cx, u["y"] / max_dim - cy) for u in group]
        )

    ally_dispersion = _dispersion(ally, acx, acy)
    enemy_dispersion = _dispersion(enemy, ecx, ecy)

    # ------------------------------------------------------------------
    # 6. Best attack opportunity (focus fire / kill shots)
    # ------------------------------------------------------------------
    best_damage = 0.0
    best_target_hp = 0.0
    best_target_dist = max_dim
    can_kill = 0.0

    if ally and enemy:
        for a in ally:
            for e in enemy:
                d = _dist(a, e)
                # rough estimate; you might refine with EFFECTIVENESS
                estimated = a["attack_power"] - e["armor"] * 0.3
                if estimated <= 0:
                    continue
                if estimated > best_damage:
                    best_damage = estimated
                    best_target_hp = float(e["health"])
                    best_target_dist = d
                    can_kill = 1.0 if estimated >= e["health"] else 0.0

    best_damage_norm = best_damage / 100.0
    best_target_hp_norm = best_target_hp / 150.0
    best_target_dist_norm = best_target_dist / max_dim if max_dim > 0 else 0.0

    # ------------------------------------------------------------------
    # FINAL FEATURE VECTOR
    # ------------------------------------------------------------------
    # 30 features + comp(8)
    features = [
        float(team_id),
        # HP global
        ally_hp_pct,
        enemy_hp_pct,
        hp_advantage,
        # Composition
        *comp,
        # Mobility & action state
        avg_move_pts_ally,
        avg_move_pts_enemy,
        frac_ally_can_attack,
        frac_enemy_can_attack,
        # Closest enemy tactical info (averaged over allies)
        closest_enemy_info[0],  # avg distance to closest enemy (normalized)
        closest_enemy_info[1],  # avg closest enemy HP%
        closest_enemy_info[2],  # avg closest enemy armor
        closest_enemy_info[3],  # fraction of allies that have someone in range
        closest_enemy_info[4],  # fraction threatened by enemy in range
        # Local densities
        ally_density_norm,
        enemy_density_norm,
        # Terrain context
        ally_move_cost_norm,
        enemy_move_cost_norm,
        ally_def_bonus,
        enemy_def_bonus,
        # Formation
        acx,
        acy,
        ecx,
        ecy,
        center_distance,
        ally_dispersion,
        enemy_dispersion,
        # Best attack opportunity
        best_damage_norm,
        best_target_hp_norm,
        best_target_dist_norm,
        can_kill,
    ]

    return np.array(features, dtype=np.float32)


def encode_state1(game_state: dict[str, Any], team_id: int) -> np.ndarray:
    units = game_state["units"]
    tiles = game_state["tiles"]

    ally = [u for u in units if u["team_id"] == team_id]
    enemy = [u for u in units if u["team_id"] != team_id]

    # ---------------------------
    # Basic counts & health
    # ---------------------------
    ally_hp = sum(u["health"] for u in ally)
    enemy_hp = sum(u["health"] for u in enemy)
    total_hp = ally_hp + enemy_hp if (ally_hp + enemy_hp) > 0 else 1

    ally_hp_ratio = ally_hp / total_hp
    enemy_hp_ratio = enemy_hp / total_hp

    # HP distribution
    ally_hp_mean = np.mean([u["health"] for u in ally])
    enemy_hp_mean = np.mean([u["health"] for u in enemy])

    ally_hp_pct_mean = np.mean([u["health"] / u["max_hp"] for u in ally])
    enemy_hp_pct_mean = np.mean([u["health"] / u["max_hp"] for u in enemy])

    # ---------------------------
    # Composition (counts by type)
    # ---------------------------
    def count_type(units, typename):
        return sum(1 for u in units if typename in u["name"].lower())

    ally_sword = count_type(ally, "sword")
    ally_arch = count_type(ally, "arch")
    ally_horse = count_type(ally, "horse")
    ally_spear = count_type(ally, "spear")

    enemy_sword = count_type(enemy, "sword")
    enemy_arch = count_type(enemy, "arch")
    enemy_horse = count_type(enemy, "horse")
    enemy_spear = count_type(enemy, "spear")

    # ---------------------------
    # Combat stats
    # ---------------------------
    ally_attack = sum(u["attack_power"] for u in ally)
    enemy_attack = sum(u["attack_power"] for u in enemy)

    ally_range_avg = np.mean([u["attack_range"] for u in ally])
    enemy_range_avg = np.mean([u["attack_range"] for u in enemy])

    ally_armor_avg = np.mean([u["armor"] for u in ally])
    enemy_armor_avg = np.mean([u["armor"] for u in enemy])

    # ---------------------------
    # Mobility
    # ---------------------------
    ally_mp_total = sum(u["move_points"] for u in ally)
    enemy_mp_total = sum(u["move_points"] for u in enemy)

    # ---------------------------
    # Spatial – army positions & spread
    # ---------------------------
    def avg_xy(us):
        if not us:
            return (0.0, 0.0)
        return (
            float(np.mean([u["x"] for u in us])),
            float(np.mean([u["y"] for u in us])),
        )

    ax, ay = avg_xy(ally)
    ex, ey = avg_xy(enemy)

    dist_centers = float(np.hypot(ax - ex, ay - ey))

    # Spread = average distance from center of mass
    def avg_spread(us, cx, cy):
        return np.mean([float(np.hypot(u["x"] - cx, u["y"] - cy)) for u in us])

    ally_spread = avg_spread(ally, ax, ay)
    enemy_spread = avg_spread(enemy, ex, ey)

    # ---------------------------
    # Tactical status
    # ---------------------------
    frac_ally_can_attack = np.mean([0 if u["has_attacked"] else 1 for u in ally])
    frac_enemy_can_attack = np.mean([0 if u["has_attacked"] else 1 for u in enemy])

    # ---------------------------
    # Threat: % of allies in range of an enemy (and vice versa)
    # ---------------------------
    def in_attack_range(att, def_):
        return (abs(att["x"] - def_["x"]) + abs(att["y"] - def_["y"])) <= att[
            "attack_range"
        ]

    ally_threatened = (
        np.mean([1 if any(in_attack_range(e, a) for e in enemy) else 0 for a in ally])
        if ally
        else 0.0
    )

    enemy_threatened = (
        np.mean([1 if any(in_attack_range(a, e) for a in ally) else 0 for e in enemy])
        if enemy
        else 0.0
    )

    # ---------------------------
    # Terrain control (better terrain under units)
    # ---------------------------
    def terrain_value(u):
        t = tiles[u["y"]][u["x"]]
        if str(t).lower().endswith("hill"):
            return 1.0
        if str(t).lower().endswith("mountain"):
            return 1.5
        if str(t).lower().endswith("water"):
            return -0.5
        return 0.0

    ally_terrain = np.mean([terrain_value(u) for u in ally])
    enemy_terrain = np.mean([terrain_value(u) for u in enemy])

    # ---------------------------
    # Final vector (normalize everything)
    # ---------------------------
    return np.array(
        [
            float(team_id),
            # Health & survivability
            ally_hp_ratio,
            enemy_hp_ratio,
            ally_hp_mean / 100.0,
            enemy_hp_mean / 100.0,
            ally_hp_pct_mean,
            enemy_hp_pct_mean,
            # Composition
            ally_sword / 10,
            ally_arch / 10,
            ally_horse / 10,
            ally_spear / 10,
            enemy_sword / 10,
            enemy_arch / 10,
            enemy_horse / 10,
            enemy_spear / 10,
            # Combat
            ally_attack / 100.0,
            enemy_attack / 100.0,
            ally_range_avg / 10.0,
            enemy_range_avg / 10.0,
            ally_armor_avg / 10.0,
            enemy_armor_avg / 10.0,
            # Mobility
            ally_mp_total / 20.0,
            enemy_mp_total / 20.0,
            # Spatial
            dist_centers / 20.0,
            ally_spread / 10.0,
            enemy_spread / 10.0,
            # Tactical
            frac_ally_can_attack,
            frac_enemy_can_attack,
            ally_threatened,
            enemy_threatened,
            # Terrain control
            ally_terrain,
            enemy_terrain,
        ],
        dtype=np.float32,
    )

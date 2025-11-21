# /ai/utils/nn_utils.py

# /ai/utils/nn_utils.py

from math import hypot
from typing import Any

import numpy as np

from utils.constants import UnitType


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

    # ----------------------------
    # 1. Health
    # ----------------------------
    ally_hp = sum(u["health"] for u in ally)
    enemy_hp = sum(u["health"] for u in enemy)

    ally_max_hp = sum(u["max_hp"] for u in ally)
    enemy_max_hp = sum(u["max_hp"] for u in enemy)

    ally_hp_pct = _safe_div(ally_hp, ally_max_hp)
    enemy_hp_pct = _safe_div(enemy_hp, enemy_max_hp)

    hp_advantage = ally_hp_pct - enemy_hp_pct

    avg_hp_pct_ally = _safe_mean([u["health"] / u["max_hp"] for u in ally])
    avg_hp_pct_enemy = _safe_mean([u["health"] / u["max_hp"] for u in enemy])

    # ----------------------------
    # 2. Composition
    # ----------------------------
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

    # ----------------------------
    # 3. Mobility / Action state
    # ----------------------------
    avg_move_pts_ally = _safe_mean([u["move_points"] for u in ally])
    avg_move_pts_enemy = _safe_mean([u["move_points"] for u in enemy])

    frac_ally_can_attack = _safe_mean([1 - u["has_attacked"] for u in ally])
    frac_enemy_can_attack = _safe_mean([1 - u["has_attacked"] for u in enemy])

    # ----------------------------
    # 4. Spatial
    # ----------------------------
    ax = _safe_mean([u["x"] for u in ally])
    ay = _safe_mean([u["y"] for u in ally])
    ex = _safe_mean([u["x"] for u in enemy])
    ey = _safe_mean([u["y"] for u in enemy])

    center_distance = hypot(ax - ex, ay - ey) / 20.0

    ally_dispersion = _safe_mean([hypot(u["x"] - ax, u["y"] - ay) for u in ally]) / 10.0
    enemy_dispersion = (
        _safe_mean([hypot(u["x"] - ex, u["y"] - ey) for u in enemy]) / 10.0
    )

    # Pressure: enemy proximity
    nearest_enemy = []
    for a in ally:
        if enemy:
            nearest_enemy.append(min(_unit_dist(a, e) for e in enemy))
    avg_nearest_enemy = _safe_mean(nearest_enemy) / 10.0

    # ----------------------------
    # 5. Terrain influence
    # ----------------------------
    def terrain_defense_bonus(u):
        tile = tiles[u["y"]][u["x"]]
        name = tile.name
        if name == "HILL" or name == "FOREST":
            return 1.0
        return 0.0

    ally_def = _safe_mean([terrain_defense_bonus(u) for u in ally])
    enemy_def = _safe_mean([terrain_defense_bonus(u) for u in enemy])

    # ----------------------------
    # FINAL VECTOR
    # ----------------------------
    features = [
        float(team_id),
        # HP
        ally_hp_pct,
        enemy_hp_pct,
        hp_advantage,
        avg_hp_pct_ally,
        avg_hp_pct_enemy,
        # Composition
        *comp,
        # Mobility
        avg_move_pts_ally / 10.0,
        avg_move_pts_enemy / 10.0,
        # Action state
        frac_ally_can_attack,
        frac_enemy_can_attack,
        # Spatial
        center_distance,
        ally_dispersion,
        enemy_dispersion,
        avg_nearest_enemy,
        # Terrain
        ally_def,
        enemy_def,
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

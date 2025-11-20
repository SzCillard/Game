# /ai/planning/nn_utils.py

from typing import Any, Dict, List

import numpy as np


def _safe_mean(values: List[float]) -> float:
    return float(np.mean(values)) if values else 0.0


def _avg_xy(unit_list: List[Dict[str, Any]]) -> tuple[float, float]:
    if not unit_list:
        return 0.0, 0.0
    xs = [u["x"] for u in unit_list]
    ys = [u["y"] for u in unit_list]
    return float(np.mean(xs)), float(np.mean(ys))


def encode_state(game_state: Dict[str, Any], team_id: int) -> np.ndarray:
    units = game_state["units"]
    ally_units = [u for u in units if int(u["team_id"]) == int(team_id)]
    enemy_units = [u for u in units if int(u["team_id"]) != int(team_id)]

    # --- Health ---
    ally_hp = sum(u["health"] for u in ally_units)
    enemy_hp = sum(u["health"] for u in enemy_units)
    ally_hp_ratio = ally_hp / (ally_hp + enemy_hp) if (ally_hp + enemy_hp) > 0 else 0.5
    avg_hp_pct_ally = _safe_mean([u["health"] / u["max_hp"] for u in ally_units])
    avg_hp_pct_enemy = _safe_mean([u["health"] / u["max_hp"] for u in enemy_units])

    # --- Combat Power ---
    ally_attack = sum(u["attack_power"] for u in ally_units)
    enemy_attack = sum(u["attack_power"] for u in enemy_units)
    avg_range_ally = _safe_mean([u["attack_range"] for u in ally_units])
    avg_range_enemy = _safe_mean([u["attack_range"] for u in enemy_units])
    avg_armor_ally = _safe_mean([u["armor"] for u in ally_units])
    avg_armor_enemy = _safe_mean([u["armor"] for u in enemy_units])

    # --- Mobility ---
    total_move_points_ally = sum(u["move_points"] for u in ally_units)
    total_move_points_enemy = sum(u["move_points"] for u in enemy_units)
    avg_move_range_ally = _safe_mean([u["move_range"] for u in ally_units])
    avg_move_range_enemy = _safe_mean([u["move_range"] for u in enemy_units])

    # --- Spatial ---
    avg_x_ally, avg_y_ally = _avg_xy(ally_units)
    avg_x_enemy, avg_y_enemy = _avg_xy(enemy_units)
    dist_centers = float(np.hypot(avg_x_ally - avg_x_enemy, avg_y_ally - avg_y_enemy))

    # --- Status ---
    frac_ally_can_attack = _safe_mean(
        [0 if u["has_attacked"] else 1 for u in ally_units]
    )
    frac_enemy_can_attack = _safe_mean(
        [0 if u["has_attacked"] else 1 for u in enemy_units]
    )

    return np.array(
        [
            float(team_id),
            ally_hp_ratio,
            avg_hp_pct_ally,
            avg_hp_pct_enemy,
            ally_attack / 100.0,
            enemy_attack / 100.0,
            avg_range_ally / 10.0,
            avg_range_enemy / 10.0,
            avg_armor_ally / 10.0,
            avg_armor_enemy / 10.0,
            total_move_points_ally / 10.0,
            total_move_points_enemy / 10.0,
            avg_move_range_ally / 10.0,
            avg_move_range_enemy / 10.0,
            dist_centers / 20.0,
            frac_ally_can_attack,
            frac_enemy_can_attack,
        ],
        dtype=np.float32,
    )


def encode_state_old1(game_state: Dict[str, Any], team_id: int) -> np.ndarray:
    """
    Extract numerical features for the neural network from a board snapshot.

    game_state: dict returned by GameState.get_snapshot()
    team_id: 1 or 2 (player side)
    """
    units = game_state["units"]

    # Separate allies and enemies
    ally_units = [u for u in units if int(u["team_id"]) == int(team_id)]
    enemy_units = [u for u in units if int(u["team_id"]) != int(team_id)]

    # Counts
    ally_count = len(ally_units)
    enemy_count = len(enemy_units)

    # Total HP (sum([]) = 0, so no need for guard)
    ally_hp = sum(u["health"] for u in ally_units)
    enemy_hp = sum(u["health"] for u in enemy_units)

    # Helper for average positions
    def _avg_xy(unit_list: List[Dict[str, Any]]) -> tuple[float, float]:
        if not unit_list:
            return 0.0, 0.0
        xs = [u["x"] for u in unit_list]
        ys = [u["y"] for u in unit_list]
        return float(np.mean(xs)), float(np.mean(ys))

    avg_x_ally, avg_y_ally = _avg_xy(ally_units)
    avg_x_enemy, avg_y_enemy = _avg_xy(enemy_units)

    # Distance between centers of mass
    dist = float(np.hypot(avg_x_ally - avg_x_enemy, avg_y_ally - avg_y_enemy))

    # Normalized feature vector (float32 for ML efficiency)
    return np.array(
        [
            float(team_id),
            ally_hp / 1000.0,
            enemy_hp / 1000.0,
            ally_count / 10.0,
            enemy_count / 10.0,
            dist / 20.0,
        ],
        dtype=np.float32,
    )


def encode_state_old2(game_state: dict[str, Any], team_id: int) -> np.ndarray:
    """
    Extract numerical features for the neural network from a board snapshot.

    game_state: dict returned by GameState.get_snapshot()
    team_id: 1 or 2 (player side)
    """
    units = game_state["units"]
    ally_units = [u for u in units if int(u["team_id"]) == int(team_id)]
    enemy_units = [u for u in units if int(u["team_id"]) != int(team_id)]

    ally_count = len(ally_units)
    enemy_count = len(enemy_units)

    # Total HP
    ally_hp = sum(u["health"] for u in ally_units) if ally_units else 0
    enemy_hp = sum(u["health"] for u in enemy_units) if enemy_units else 0

    # Average positions
    def _avg_xy(unit_list: list[dict[str, Any]]) -> tuple[float, float]:
        if not unit_list:
            return 0.0, 0.0
        xs = [u["x"] for u in unit_list]
        ys = [u["y"] for u in unit_list]
        return float(np.mean(xs)), float(np.mean(ys))

    avg_x_ally, avg_y_ally = _avg_xy(ally_units)
    avg_x_enemy, avg_y_enemy = _avg_xy(enemy_units)

    # Distance between "centers of mass"
    dist = np.hypot(avg_x_ally - avg_x_enemy, avg_y_ally - avg_y_enemy)

    # Very simple normalization; you can tune later
    return np.array(
        [
            float(team_id),
            ally_hp / 1000.0,
            enemy_hp / 1000.0,
            ally_count / 10.0,
            enemy_count / 10.0,
            dist / 20.0,
        ],
        dtype=float,
    )

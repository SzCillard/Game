import random
from typing import Dict, List

from utils.constants import UNIT_STATS
from utils.logging import logger

ProbMap = Dict[str, float]
StrategyMap = Dict[str, ProbMap]
UnitInfoMap = Dict[str, Dict[str, int]]  # e.g. {"Swordsman": {"cost": 30}, ...}

probabilities: StrategyMap = {
    "balanced": {"Swordsman": 0.25, "Archer": 0.25, "Horseman": 0.25, "Spearman": 0.25},
    "rush": {"Horseman": 0.5, "Swordsman": 0.3, "Archer": 0.1, "Spearman": 0.1},
    "defense": {"Spearman": 0.4, "Swordsman": 0.25, "Archer": 0.35, "Horseman": 0.0},
    "ranged": {"Archer": 0.5, "Spearman": 0.3, "Swordsman": 0.1, "Horseman": 0.1},
}


def ai_draft_basic(
    funds: int,
    available_units: UnitInfoMap,
    probabilities: StrategyMap,
    max_picks: int,
) -> List[str]:
    strategies: List[str] = ["balanced", "rush", "defense", "ranged"]
    choice: str = random.choice(strategies)

    logger(f"AI draft strategy chosen: {choice}")

    selected: List[str] = []
    funds_left: int = funds  # for example 100

    picks_done: int = 0
    while picks_done < max_picks:
        # filter units that exist, have non-zero probability and are affordable
        affordable: ProbMap = {
            unit: prob
            for unit, prob in probabilities[choice].items()
            if prob > 0
            and unit in available_units
            and available_units[unit]["cost"] <= funds_left
        }

        if not affordable:
            break

        # normalize weights
        total: float = sum(affordable.values())
        weights: List[float] = [prob / total for prob in affordable.values()]
        units: List[str] = list(affordable.keys())

        # choose one unit by weighted probability
        chosen: str = random.choices(units, weights=weights, k=1)[0]
        cost: int = available_units[chosen]["cost"]

        # safety: if cost is zero, append once then remove it from
        # future picks to avoid infinite loop
        selected.append(chosen)
        funds_left -= cost
        picks_done += 1

        if cost == 0:
            # remove chosen unit from probabilities for
            # this draft loop to avoid infinite picks
            # make a shallow copy of the top-level map and the chosen strategy
            probabilities = {k: dict(v) for k, v in probabilities.items()}  # type: ignore[assignment]
            probabilities[choice].pop(chosen, None)

    logger(f"AI draft completed. Units selected: {selected}")

    return selected


def get_ai_draft_units(
    funds: int,
    available_units: UnitInfoMap = UNIT_STATS,
    probabilities: StrategyMap = probabilities,
    max_picks: int = 100,
) -> List[str]:
    selected_units: List[str] = ai_draft_basic(
        funds, available_units, probabilities, max_picks
    )
    return selected_units

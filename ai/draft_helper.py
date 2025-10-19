import random

probabilities = {
    "balanced": {"Swordsman": 0.25, "Archer": 0.25, "Horseman": 0.25, "Spearman": 0.25},
    "rush": {"Horseman": 0.5, "Swordsman": 0.3, "Archer": 0.1, "Spearman": 0.1},
    "defense": {"Spearman": 0.4, "Swordsman": 0.25, "Archer": 0.35, "Horseman": 0.0},
    "ranged": {"Archer": 0.5, "Spearman": 0.3, "Swordsman": 0.1, "Horseman": 0.1},
}


def ai_draft_basic(funds, available_units, probabilities=probabilities, max_picks=100):
    strategies = ["balanced", "rush", "defense", "ranged"]
    choice = random.choice(strategies)
    selected = []
    funds_left = funds  # for example 100

    picks_done = 0
    while picks_done < max_picks:
        # filter units that exist, have non-zero probability and are affordable
        affordable = {
            unit: prob
            for unit, prob in probabilities[choice].items()
            if prob > 0
            and unit in available_units
            and available_units[unit]["cost"] <= funds_left
        }

        if not affordable:
            break

        # normalize weights
        total = sum(affordable.values())
        weights = [prob / total for prob in affordable.values()]
        units = list(affordable.keys())

        # choose one unit by weighted probability
        chosen = random.choices(units, weights=weights, k=1)[0]
        cost = available_units[chosen]["cost"]

        # safety: if cost is zero, append once then remove it from
        # future picks to avoid infinite loop
        selected.append(chosen)
        funds_left -= cost
        picks_done += 1

        if cost == 0:
            # remove chosen unit from probabilities for
            # this draft loop to avoid infinite picks
            probabilities = {k: dict(v) for k, v in probabilities.items()}
            probabilities[choice].pop(chosen, None)

    return (
        choice,
        selected,
    )

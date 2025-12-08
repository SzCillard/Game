"""
Presets for agents used in benchmarking.

Each preset becomes a separate "agent" entry in the round robin.
"""

# -------------------------
# MCTS presets
# -------------------------
MCTS_PRESETS = {
    "MCTS_default": {
        "max_sets": 200,
        "max_branching": 20,
        "max_root_children": 8,
        "iterations": 80,
        "rollout_turns": 2,
        "c_puct": 1.4,
    },
    "MCTS_fast": {
        "max_sets": 100,
        "max_branching": 10,
        "max_root_children": 4,
        "iterations": 30,
        "rollout_turns": 1,
        "c_puct": 1.2,
    },
    "MCTS_deep": {
        "max_sets": 300,
        "max_branching": 30,
        "max_root_children": 12,
        "iterations": 150,
        "rollout_turns": 3,
        "c_puct": 1.6,
    },
}

# -------------------------
# Minimax presets
# -------------------------
MINIMAX_PRESETS = {
    "Minimax_default": {
        "depth": 2,
        "branching_limit": 6,
    },
    "Minimax_deep": {
        "depth": 3,
        "branching_limit": 8,
    },
    "Minimax_wide": {
        "depth": 2,
        "branching_limit": 16,
    },
}


# Map agent_type → preset definitions
AGENT_PRESET_MAP = {
    "MCTSAgent": MCTS_PRESETS,
    "MinimaxAgent": MINIMAX_PRESETS,
}

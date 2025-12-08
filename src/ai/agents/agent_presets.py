"""
Presets for agents used in benchmarking.

Each preset becomes a separate "agent" entry in the round robin.
"""

# -------------------------
# MCTS presets
# -------------------------
MCTS_PRESETS = {
    "MCTS_default": {
        "dfs_action_sets_limit": 300,
        "dfs_branching_limit": 20,
        "max_root_children": 10,
        "iterations": 100,
        "rollout_turns": 3,
        "c_puct": 1.4,
    },
    "MCTS_fast": {
        "dfs_action_sets_limit": 100,
        "dfs_branching_limit": 10,
        "max_root_children": 4,
        "iterations": 30,
        "rollout_turns": 1,
        "c_puct": 1.2,
    },
    "MCTS_deep": {
        "dfs_action_sets_limit": 500,
        "dfs_branching_limit": 30,
        "max_root_children": 20,
        "iterations": 150,
        "rollout_turns": 4,
        "c_puct": 1.6,
    },
}

# -------------------------
# Minimax presets
# -------------------------
MINIMAX_PRESETS = {
    "Minimax_default": {
        "depth": 2,
        "child_limit": 2,
    },
    "Minimax_deep": {
        "depth": 3,
        "child_limit": 3,
    },
    "Minimax_wide": {
        "depth": 2,
        "child_limit": 4,
    },
}


# Map agent_type → preset definitions
AGENT_PRESET_MAP = {
    "MCTSAgent": MCTS_PRESETS,
    "MinimaxAgent": MINIMAX_PRESETS,
}

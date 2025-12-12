"""
Presets for agents used in benchmarking.

Each preset becomes a separate "agent" entry in the round robin.
"""

# -------------------------
# MCTS presets
# -------------------------
MCTS_PRESETS = {
    "MCTS_default": {
        "dfs_action_sets_limit": 800,
        "dfs_branching_limit": 16,
        "max_root_children": 12,
        "iterations": 800,
        "rollout_turns": 2,
        "c_puct": 1.4,
    },
    "MCTS_fast": {
        "dfs_action_sets_limit": 500,
        "dfs_branching_limit": 10,
        "max_root_children": 8,
        "iterations": 300,
        "rollout_turns": 2,
        "c_puct": 1.4,
    },
    "MCTS_deep": {
        "dfs_action_sets_limit": 1000,
        "dfs_branching_limit": 20,
        "max_root_children": 16,
        "iterations": 1500,
        "rollout_turns": 3,
        "c_puct": 1.2,
    },
}

# -------------------------
# Minimax presets
# -------------------------
MINIMAX_PRESETS = {
    "Minimax_default": {
        "dfs_action_sets_limit": 800,
        "dfs_branching_limit": 12,
        "depth": 3,
        "child_limit": 3,
    },
    "Minimax_deep": {
        "dfs_action_sets_limit": 1000,
        "dfs_branching_limit": 12,
        "depth": 4,
        "child_limit": 3,
    },
    "Minimax_wide": {
        "dfs_action_sets_limit": 1000,
        "dfs_branching_limit": 20,
        "depth": 3,
        "child_limit": 4,
    },
}


# Map agent_type → preset definitions
AGENT_PRESET_MAP = {
    "MCTSAgent": MCTS_PRESETS,
    "MinimaxAgent": MINIMAX_PRESETS,
}

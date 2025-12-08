# statistics/benchmark_round_robin.py
from __future__ import annotations

import csv
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from ai.agents.agent_factory import AgentFactory
from ai.neat.neat_network import NeatNetwork
from ai.utils.draft_helper import get_ai_draft_units
from api.simulation_api import SimulationAPI
from backend.board import GameState, create_random_map
from utils.constants import UNIT_STATS, TeamType
from utils.path_utils import get_asset_path


# ======================================================================
# 🔍 Compute NEAT-style training stats
# ======================================================================
def _compute_neat_stats(sim: SimulationAPI, team1_names, team2_names):
    snapshot = sim.get_board_snapshot()
    units = snapshot["units"]

    team1 = [u for u in units if u["team_id"] == 1]
    team2 = [u for u in units if u["team_id"] == 2]

    hp1 = sum(u["health"] for u in team1) or 1
    hp2 = sum(u["health"] for u in team2) or 1

    alive1 = len(team1) if len(team1) > 0 else 0.1
    alive2 = len(team2) if len(team2) > 0 else 0.1

    max_hp_team1 = sum(UNIT_STATS[n]["health"] for n in team1_names)
    max_hp_team2 = sum(UNIT_STATS[n]["health"] for n in team2_names)

    return {
        "initial_unit_count_team1": len(team1_names),
        "initial_unit_count_team2": len(team2_names),
        "alive1": alive1,
        "alive2": alive2,
        "max_hp_team1": max_hp_team1,
        "max_hp_team2": max_hp_team2,
        "hp1": hp1,
        "hp2": hp2,
    }


# ======================================================================
# 🧪 Worker: Run a single match between two agents
# ======================================================================
def _run_match_worker(args):
    agentA_info, agentB_info, max_turns, config_path = args
    (nameA, brainA_path, agentA_type, paramsA) = agentA_info
    (nameB, brainB_path, agentB_type, paramsB) = agentB_info

    brainA = NeatNetwork(genome_path=str(brainA_path), config_path=str(config_path))
    brainB = NeatNetwork(genome_path=str(brainB_path), config_path=str(config_path))

    agentA = AgentFactory.create(agentA_type, brainA, **paramsA)
    agentB = AgentFactory.create(agentB_type, brainB, **paramsB)

    # Build board
    board = GameState(
        width=8,
        height=8,
        cell_size=64,
        tile_map=create_random_map(8, 8),
    )
    sim = SimulationAPI(board)

    # Draft units
    team1_names = get_ai_draft_units(100)
    team2_names = get_ai_draft_units(100)

    sim.add_units(team1_names, 1, TeamType.AI)
    sim.add_units(team2_names, 2, TeamType.AI)

    # Play match
    turns = 0
    for t in range(max_turns):
        sim.start_turn(1)
        agentA.play_turn(sim, 1)
        if sim.is_game_over():
            turns = t + 1
            break

        sim.start_turn(2)
        agentB.play_turn(sim, 2)
        if sim.is_game_over():
            turns = t + 1
            break

        turns = t + 1

    winner = sim.get_winner()

    # Compute NEAT-style stats
    stats = _compute_neat_stats(sim, team1_names, team2_names)

    return {
        "agentA": nameA,
        "agentB": nameB,
        "winner": winner,
        "turns": turns,
        **stats,
    }


# ======================================================================
# 🧪 Round Robin Benchmark Controller
# ======================================================================
class RoundRobinBenchmark:
    def __init__(self, agents, max_turns=30, workers=4, config_path=None):
        self.config_path = config_path or get_asset_path(
            "assets/neat/configs/neat_config.txt"
        )
        self.agents = agents
        self.max_turns = max_turns
        self.workers = workers

    # -------------------------------------------------------------
    # Create all matchups (A vs B AND B vs A)
    # -------------------------------------------------------------
    def _build_match_list(self):
        tasks = []
        for i, A in enumerate(self.agents):
            for j, B in enumerate(self.agents):
                if i == j:
                    continue
                tasks.append(
                    (
                        (A["name"], A["brain"], A["type"], A["params"]),
                        (B["name"], B["brain"], B["type"], B["params"]),
                        self.max_turns,
                        self.config_path,
                    )
                )
        return tasks

    # -------------------------------------------------------------
    # Run benchmark
    # -------------------------------------------------------------
    def run(self):
        match_list = self._build_match_list()
        results = []

        start = time.time()
        with ProcessPoolExecutor(max_workers=self.workers) as ex:
            futures = [ex.submit(_run_match_worker, m) for m in match_list]

            for f in as_completed(futures):
                results.append(f.result())

        print(f"\n🏁 Round Robin Completed in {time.time() - start:.2f}s\n")
        return results

    # -------------------------------------------------------------
    # Save CSV with timestamp
    # -------------------------------------------------------------
    @staticmethod
    def save_csv(results, path=None):
        # --- Determine project root (src/ai/statistics/...) ---
        project_root = Path(__file__).resolve().parents[3]
        # /home/cillard/projects/Game/

        results_dir = project_root / "src/ai/statistics/round_robin_results"
        results_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"round_robin_{timestamp}.csv"

        final_path = results_dir / filename

        fieldnames = [
            "agentA",
            "agentB",
            "winner",
            "turns",
            "initial_unit_count_team1",
            "initial_unit_count_team2",
            "alive1",
            "alive2",
            "max_hp_team1",
            "max_hp_team2",
            "hp1",
            "hp2",
        ]

        with open(final_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                writer.writerow(r)

        print(f"📄 Saved CSV → {final_path}")
        return str(final_path)

    # -------------------------------------------------------------
    # Winrate summary
    # -------------------------------------------------------------
    @staticmethod
    def summarize(results):
        table = {}

        for r in results:
            A = r["agentA"]
            B = r["agentB"]

            table.setdefault(A, {"wins": 0, "games": 0})
            table.setdefault(B, {"wins": 0, "games": 0})

            table[A]["games"] += 1
            table[B]["games"] += 1

            if r["winner"] == 1:
                table[A]["wins"] += 1
            elif r["winner"] == 2:
                table[B]["wins"] += 1

        return {
            agent: {
                "winrate": v["wins"] / max(1, v["games"]),
                "games": v["games"],
            }
            for agent, v in table.items()
        }

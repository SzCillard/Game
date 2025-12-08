import argparse
from pathlib import Path

from ai.agents.agent_presets import AGENT_PRESET_MAP
from ai.statistics.benchmark_round_robin import RoundRobinBenchmark
from utils.path_utils import get_asset_path


# ---------------------------------------------------------
# Command-line arguments
# ---------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Run round-robin AI benchmark.")

    parser.add_argument(
        "-g",
        "--genome",
        type=str,
        default=None,
        help="Path to a NEAT genome. "
        "If only a filename is given, it's resolved inside assets/neat/genomes/",
    )

    parser.add_argument(
        "--agents",
        nargs="+",
        required=True,
        choices=["NEATAgent", "MinimaxAgent", "MCTSAgent"],
        help="List of agents to benchmark. Example: --agents NEATAgent MCTSAgent",
    )

    parser.add_argument(
        "--config",
        type=str,
        default=get_asset_path("assets/neat/configs/neat_config.txt"),
        help="Path to NEAT config file.",
    )

    parser.add_argument("--max_workers", type=int, default=4)
    parser.add_argument("--max_turns", type=int, default=30)

    return parser.parse_args()


# ---------------------------------------------------------
# Resolve genome path (same logic as main.py)
# ---------------------------------------------------------
def resolve_genome_path(genome_override: str | None) -> Path:
    """
    Behaves exactly like load_neat_agent() from main.py.
    """
    default_path = Path(get_asset_path("assets/neat/genomes/best_genome.pkl"))

    if not genome_override:
        print(f"Using DEFAULT genome: {default_path}")
        return default_path

    override = Path(genome_override)

    # Case 1 — only filename → look inside assets/neat/genomes/
    if not override.is_absolute() and len(override.parts) == 1:
        final = Path(get_asset_path("assets/neat/genomes")) / override
        print(f"Using genome filename → resolved to: {final}")
        return final

    # Case 2 — full path
    print(f"Using absolute genome path: {override}")
    return override


# ---------------------------------------------------------
# Build agents list
# ---------------------------------------------------------
def build_agents(agent_types, genome_path):
    agents = []

    for agent_type in agent_types:
        # If the agent has presets, expand them
        if agent_type in AGENT_PRESET_MAP:
            presets = AGENT_PRESET_MAP[agent_type]
            for preset_name, preset_params in presets.items():
                agents.append(
                    {
                        "name": preset_name,
                        "brain": str(genome_path),
                        "type": agent_type,
                        "params": preset_params,  # << attach hyperparameters
                    }
                )
        else:
            # Otherwise treat as single config (NEATAgent only)
            agents.append(
                {
                    "name": agent_type,
                    "brain": str(genome_path),
                    "type": agent_type,
                    "params": {},  # no params
                }
            )

    return agents


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():
    args = parse_args()

    genome_path = resolve_genome_path(args.genome)

    agents = build_agents(args.agents, genome_path)

    bench = RoundRobinBenchmark(
        agents=agents,
        max_turns=args.max_turns,
        workers=args.max_workers,
        config_path=args.config,
    )

    results = bench.run()
    bench.save_csv(results)

    summary = bench.summarize(results)

    print("\n=== SUMMARY ===")
    for agent, stats in summary.items():
        print(f"{agent}: {stats['winrate'] * 100:.1f}% over {stats['games']} games")


if __name__ == "__main__":
    main()

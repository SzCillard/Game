# ai/neat/train_neat.py
import argparse

from ai.neat.neat_trainer import NeatTrainer
from api.simulation_api import SimulationAPI
from backend.board import GameState, create_random_map


def parse_args():
    parser = argparse.ArgumentParser(description="Train NEAT via self-play.")

    parser.add_argument(
        "--config",
        type=str,
        default="ai/neat/neat_config.txt",
        help="Path to NEAT config file.",
    )

    parser.add_argument(
        "--generations", type=int, default=15, help="Number of generations to train."
    )

    parser.add_argument(
        "--population_size",
        type=int,
        default=10,
        help="Override NEAT config population size.",
    )

    parser.add_argument("--max_workers", type=int, default=4, help="Process pool size.")

    parser.add_argument(
        "--opponents", type=int, default=5, help="Opponents per genome per generation."
    )

    parser.add_argument(
        "--max_turns", type=int, default=30, help="Max turns per match."
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # Create fresh game environment
    game_board = GameState(
        width=8,
        height=8,
        cell_size=64,
        tile_map=create_random_map(8, 8),
    )
    headless_api = SimulationAPI(game_board)

    # Inject population override into config file if requested
    if args.population_size is not None:
        print(f"⚙️ Overriding population size → {args.population_size}")
        override_population_size(args.config, args.population_size)

    # Create trainer with CLI parameters
    trainer = NeatTrainer(
        config_path=args.config,
        game_api=headless_api,
        max_workers=args.max_workers,
        opponents_per_genome=args.opponents,
        max_turns=args.max_turns,
    )

    trainer.max_turns = args.max_turns

    trainer.run(generations=args.generations)
    print("Training complete. Best genome saved to best_genome.pkl")


def override_population_size(config_path: str, size: int):
    """Modify NEAT config file's population size dynamically."""
    lines = []
    with open(config_path, "r") as f:
        for line in f.readlines():
            if line.startswith("pop_size"):
                lines.append(f"pop_size = {size}\n")
            else:
                lines.append(line)

    with open(config_path, "w") as f:
        f.writelines(lines)


if __name__ == "__main__":
    main()

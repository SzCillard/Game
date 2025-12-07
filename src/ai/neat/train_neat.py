# ai/neat/train_neat.py
from __future__ import annotations

import argparse
import pickle
from datetime import datetime
from pathlib import Path

from ai.neat.neat_trainer import NeatTrainer
from api.simulation_api import SimulationAPI
from backend.board import GameState, create_random_map
from utils.path_utils import get_asset_path


# ---------------------------------------------------------
# Command-line arguments
# ---------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Train NEAT via self-play.")

    parser.add_argument(
        "--config",
        type=str,
        default=get_asset_path("assets/neat/configs/neat_config.txt"),
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

    parser.add_argument(
        "--max_workers", type=int, default=4, help="Parallel worker processes."
    )

    parser.add_argument(
        "--opponents", type=int, default=5, help="Opponents per genome per generation."
    )

    parser.add_argument(
        "--max_turns", type=int, default=30, help="Max turns per match."
    )

    return parser.parse_args()


# ---------------------------------------------------------
# Utility: override NEAT config population dynamically
# ---------------------------------------------------------
def override_population_size(config_path: str, new_size: int):
    """Modify NEAT config file's population size on the fly."""
    updated = []
    with open(config_path, "r") as f:
        for line in f.readlines():
            if line.strip().startswith("pop_size"):
                updated.append(f"pop_size = {new_size}\n")
            else:
                updated.append(line)

    with open(config_path, "w") as f:
        f.writelines(updated)

    print(f"✔ Updated pop_size in {config_path} → {new_size}")


# ---------------------------------------------------------
# Utility: Save best genome to assets/neat/
# ---------------------------------------------------------
def save_best_genome(genome, gen, pop, opp):
    """
    Saves:
    - assets/neat/genomes/best_genome.pkl       (stable file used by the game)
    - assets/neat/genomes/best_genome_G{gen}_P{pop}_O{opp}_{stamp}.pkl
    """

    # Resolve path correctly for dev + EXE
    asset_dir = Path(get_asset_path("assets/neat/genomes"))

    asset_dir.mkdir(parents=True, exist_ok=True)

    # Main file used by runtime game
    final_path = asset_dir / "best_genome.pkl"

    # Timestamped archive
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    backup_name = f"best_genome_G{gen}_P{pop}_O{opp}_{stamp}.pkl"
    backup_path = asset_dir / backup_name

    # Write primary file
    with open(final_path, "wb") as f:
        pickle.dump(genome, f)

    # Write backup version
    with open(backup_path, "wb") as f:
        pickle.dump(genome, f)

    print(f"🎉 Saved best genome → {final_path}")
    print(f"🗂  Backup created → {backup_path}")


# ---------------------------------------------------------
# Main training function
# ---------------------------------------------------------
def main():
    args = parse_args()

    print("🚀 Starting NEAT training...")

    # Prepare initial simulation environment
    game_board = GameState(
        width=8,
        height=8,
        cell_size=64,
        tile_map=create_random_map(8, 8),
    )
    headless = SimulationAPI(game_board)

    # Override pop size if requested
    if args.population_size:
        override_population_size(args.config, args.population_size)

    # Create trainer
    trainer = NeatTrainer(
        config_path=args.config,
        game_api=headless,
        max_workers=args.max_workers,
        opponents_per_genome=args.opponents,
        max_turns=args.max_turns,
    )

    # Run training
    best = trainer.run(generations=args.generations)

    # Save the result
    save_best_genome(
        genome=best,
        gen=args.generations,
        pop=args.population_size,
        opp=args.opponents,
    )

    print("🏁 Training complete!")


if __name__ == "__main__":
    main()

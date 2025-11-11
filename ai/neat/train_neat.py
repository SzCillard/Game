# ai/neat/train_neat.py
import os

from ai.neat.neat_trainer import NeatTrainer
from api.headless_api import HeadlessGameAPI
from backend.board import GameState, create_random_map
from backend.logic import GameLogic


def main():
    # Paths
    config_path = os.path.join("ai", "neat", "neat_config.txt")

    # local_dir = os.path.dirname(__file__)
    # config_path = os.path.join(local_dir, "sample_neat_config.txt")

    # Create a fresh game environment for headless simulation
    game_board = GameState(
        width=8,
        height=8,
        cell_size=64,
        tile_map=create_random_map(8, 8),
    )
    game_logic = GameLogic(game_board)  # logic tied to that board
    headless_api = HeadlessGameAPI(game_board, game_logic)

    # Create trainer
    trainer = NeatTrainer(config_path, headless_api)

    # Run NEAT evolution
    # winner = trainer.run(generations=10)

    trainer.run(generations=10)

    print("Training complete. Best genome saved to best_genome.pkl")


if __name__ == "__main__":
    main()

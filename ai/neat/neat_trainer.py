# ai/neat/neat_trainer.py
import pickle

import neat

from ai.neat.neat_selfplay import SelfPlaySimulator
from api.headless_api import HeadlessGameAPI


class NeatTrainer:
    def __init__(self, config_path: str, game_api: "HeadlessGameAPI"):
        self.config = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            config_path,
        )
        self.game_api = game_api
        self.sim = SelfPlaySimulator(self.config, game_api)

    def eval_genomes(self, genomes, config):
        """Evaluate all genomes via pairwise self-play."""
        for i, (gid_a, genome_a) in enumerate(genomes):
            genome_a.fitness = 0
            for j, (gid_b, genome_b) in enumerate(genomes):
                if i == j:
                    continue
                f_a, f_b = self.sim.play_match(genome_a, genome_b)
                genome_a.fitness += f_a
                genome_b.fitness += f_b

        # Optionally normalize by number of matches
        for _, genome in genomes:
            genome.fitness /= len(genomes) - 1

    def run(self, generations: int = 50):
        """Run evolution for N generations."""
        pop = neat.Population(self.config)
        pop.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        pop.add_reporter(stats)

        winner = pop.run(self.eval_genomes, generations)
        print("\n🏆 Winner:", winner)

        with open("best_genome.pkl", "wb") as f:
            pickle.dump(winner, f)
        return winner

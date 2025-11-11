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
        self.max_turns = 30

    def compute_fitness(self, winner: int | None, played_turns: int, max_turns: int):
        """
        Compute per-match fitness for both genomes.

        Args:
            winner: 1 if team1 wins, 2 if team2 wins, or None for draw.
            played_turns: Number of turns the match lasted.
            max_turns: Maximum possible turns.

        Returns:
            Tuple (team1_fitness, team2_fitness)
        """
        turn_component = 1 - (played_turns / max_turns)
        team1_score = 0
        team2_score = 0

        if winner == 1:
            team1_score = 1
        elif winner == 2:
            team2_score = 1
        else:
            team1_score = 0.3
            team2_score = 0.3

        team1_fitness = 0
        team2_fitness = 0
        team1_fitness += team1_score * turn_component
        team2_fitness += team2_score * turn_component

        return team1_fitness, team2_fitness

    def eval_genomes(self, genomes, config):
        """Evaluate all genomes via pairwise self-play."""
        for i, (gid_a, genome_a) in enumerate(genomes):
            genome_a.fitness = 0
            for j, (gid_b, genome_b) in enumerate(genomes):
                if i == j:
                    continue
                winner, played_turns = self.sim.play_match(genome_a, genome_b)
                f_a, f_b = self.compute_fitness(winner, played_turns, self.max_turns)

                genome_a.fitness += f_a
                genome_b.fitness += f_b

        # Optionally normalize by number of matches
        genomes_count = len(genomes) - 1
        for _, genome in genomes:
            genome.fitness /= genomes_count

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

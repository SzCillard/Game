# ai/neat/neat_trainer.py
import pickle
from concurrent.futures import ProcessPoolExecutor, as_completed

import neat

from ai.neat.neat_selfplay import SelfPlaySimulator
from api.headless_api import HeadlessGameAPI


class NeatTrainer:
    def __init__(
        self, config_path: str, game_api: "HeadlessGameAPI", max_workers: int = 4
    ):
        """
        Parallelized NEAT trainer using match-level concurrency.

        Args:
            config_path (str): Path to NEAT configuration file.
            game_api (HeadlessGameAPI): Pickle-safe game environment.
            max_workers (int): Number of worker processes for parallel matches.
        """
        self.config_path = config_path  # ✅ store path manually
        self.config = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            config_path,
        )
        self.base_game_api = game_api
        self.max_turns = 30
        self.max_workers = max_workers

    # ============================================================
    # 🎯 Fitness Function
    # ============================================================

    def compute_fitness(self, winner: int | None, played_turns: int, max_turns: int):
        """
        Compute per-match fitness for both genomes.
        """
        turn_component = 1 - (played_turns / max_turns)
        if winner == 1:
            team1_score, team2_score = 1, 0
        elif winner == 2:
            team1_score, team2_score = 0, 1
        else:
            team1_score = team2_score = 0.3

        return team1_score * turn_component, team2_score * turn_component

    # ============================================================
    # ⚔️ Parallel Match Evaluation
    # ============================================================

    @staticmethod
    def _run_match(
        config_path: str,
        game_api: "HeadlessGameAPI",
        genome_a_data,
        genome_b_data,
        max_turns: int,
    ):
        """Runs a single self-play match in an isolated process."""
        gid_a, g_a_bytes = genome_a_data
        gid_b, g_b_bytes = genome_b_data

        # Recreate config and genomes
        config = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            config_path,
        )
        genome_a = neat.DefaultGenome(gid_a)
        genome_b = neat.DefaultGenome(gid_b)
        genome_a.__dict__.update(pickle.loads(g_a_bytes))
        genome_b.__dict__.update(pickle.loads(g_b_bytes))

        sim = SelfPlaySimulator(config, game_api)
        winner, played_turns = sim.play_match(genome_a, genome_b)

        return gid_a, gid_b, winner, played_turns

    def eval_genomes(self, genomes, config):
        """Evaluate genomes via parallel self-play matches."""
        for _, genome in genomes:
            genome.fitness = 0.0

        genome_data = [(gid, pickle.dumps(genome.__dict__)) for gid, genome in genomes]
        matches = [
            (genome_data[i], genome_data[j])
            for i in range(len(genomes))
            for j in range(i + 1, len(genomes))
        ]

        futures = []
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            for g_a, g_b in matches:
                game_clone = self.base_game_api.clone()
                futures.append(
                    executor.submit(
                        NeatTrainer._run_match,
                        self.config_path,  # ✅ use our stored path
                        game_clone,
                        g_a,
                        g_b,
                        self.max_turns,
                    )
                )

            for f in as_completed(futures):
                gid_a, gid_b, winner, played_turns = f.result()
                f_a, f_b = self.compute_fitness(winner, played_turns, self.max_turns)
                for gid, fitness in [(gid_a, f_a), (gid_b, f_b)]:
                    genome = next(g for g_id, g in genomes if g_id == gid)
                    genome.fitness += fitness

        # Normalize
        for _, genome in genomes:
            genome.fitness /= max(1, len(genomes) - 1)

    # ============================================================
    # 🚀 Evolution Loop
    # ============================================================

    def run(self, generations: int = 50):
        """Run NEAT evolution for N generations."""
        pop = neat.Population(self.config)
        pop.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        pop.add_reporter(stats)

        winner = pop.run(self.eval_genomes, generations)
        print("\n🏆 Winner genome:", getattr(winner, "key", None))  # ✅ safe access

        with open("best_genome.pkl", "wb") as f:
            pickle.dump(winner, f)

        return winner

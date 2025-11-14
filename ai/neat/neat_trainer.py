# ai/neat/neat_trainer.py
import pickle
import random
from concurrent.futures import ProcessPoolExecutor, as_completed

import neat

from ai.neat.neat_selfplay import SelfPlaySimulator
from api.headless_api import HeadlessGameAPI


class NeatTrainer:
    """
    Parallel NEAT self-play trainer with opponent pool evolution.
    """

    def __init__(
        self,
        config_path: str,
        game_api: "HeadlessGameAPI",
        max_workers: int = 4,
        opponents_per_genome: int = 5,
        carryover_elite_count: int = 5,
    ):
        self.config_path = config_path
        self.config = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            config_path,
        )
        self.base_game_api = game_api
        self.max_turns = 40
        self.max_workers = max_workers
        self.opponents_per_genome = opponents_per_genome
        self.carryover_elite_count = carryover_elite_count
        self.previous_elites = []  # opponent pool

    # ============================================================
    # 🎯 Fitness Function
    # ============================================================

    def compute_fitness(self, winner: int | None, played_turns: int, max_turns: int):
        """Compute fitness contribution from a match result."""
        turn_component = 1 - (played_turns / max_turns)
        if winner == 1:
            return 1.0 * turn_component, 0.0
        elif winner == 2:
            return 0.0, 1.0 * turn_component
        else:
            return 0.3 * turn_component, 0.3 * turn_component

    # ============================================================
    # ⚔️ Match Execution
    # ============================================================

    @staticmethod
    def _run_match(config_path, game_api, genome_a_data, genome_b_data, max_turns):
        """Runs a single match in isolation."""
        gid_a, g_a_bytes = genome_a_data
        gid_b, g_b_bytes = genome_b_data

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

    # ============================================================
    # 🧮 Genome Evaluation
    # ============================================================

    def eval_genomes(self, genomes, config):
        """Evaluate genomes using sampled opponents and previous elites."""
        for _, genome in genomes:
            genome.fitness = 0.0

        genome_data = [(gid, pickle.dumps(genome.__dict__)) for gid, genome in genomes]
        matches = []

        # Build matches per genome
        for i, g_a in enumerate(genome_data):
            opponents = random.sample(
                genome_data, min(self.opponents_per_genome, len(genome_data) - 1)
            )
            for g_b in opponents:
                if g_a == g_b:
                    continue
                matches.append((g_a, g_b))

            # Add 1–2 elite opponents for long-term pressure
            if self.previous_elites:
                elite_sample = random.sample(
                    self.previous_elites, min(2, len(self.previous_elites))
                )
                for elite_data in elite_sample:
                    matches.append((g_a, elite_data))

        # Parallel run
        futures = []
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            for g_a, g_b in matches:
                game_clone = self.base_game_api.clone()
                futures.append(
                    executor.submit(
                        NeatTrainer._run_match,
                        self.config_path,
                        game_clone,
                        g_a,
                        g_b,
                        self.max_turns,
                    )
                )

            for f in as_completed(futures):
                gid_a, gid_b, winner, turns = f.result()
                f_a, f_b = self.compute_fitness(winner, turns, self.max_turns)

                for gid, fitness in [(gid_a, f_a), (gid_b, f_b)]:
                    if gid < 0:
                        continue  # skip elite opponents
                    genome = next(g for g_id, g in genomes if g_id == gid)
                    genome.fitness += fitness

        # Normalize by number of matches
        for _, genome in genomes:
            genome.fitness /= max(1, self.opponents_per_genome + 2)

        # Store elites for next generation
        top_elites = sorted(
            [g for _, g in genomes], key=lambda g: g.fitness, reverse=True
        )[: self.carryover_elite_count]

        self.previous_elites = [
            (-(i + 1), pickle.dumps(g.__dict__))  # give them negative fake IDs
            for i, g in enumerate(top_elites)
        ]

    # ============================================================
    # 🚀 Evolution Loop
    # ============================================================

    def run(self, generations: int = 50):
        """Run NEAT evolution with opponent pool self-play."""
        pop = neat.Population(self.config)
        pop.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        pop.add_reporter(stats)

        winner = pop.run(self.eval_genomes, generations)
        if winner is None:
            print("\nNo winner genome produced.")
        else:
            print(
                f"""\n🏆 Winner genome:
                {getattr(winner, "key", None)} ({winner.fitness:.4f})"""
            )

            with open("best_genome.pkl", "wb") as f:
                pickle.dump(winner, f)

        return winner

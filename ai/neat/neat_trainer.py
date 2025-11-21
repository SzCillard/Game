from __future__ import annotations

import pickle
import random
from concurrent.futures import ProcessPoolExecutor, as_completed

import neat
import numpy as np

from ai.neat.neat_selfplay import SelfPlaySimulator
from api.headless_api import HeadlessGameAPI


class NeatTrainer:
    """
    Parallel NEAT self-play trainer.

    Responsibilities:
      - Create a NEAT population.
      - For each generation, evaluate genomes via self-play:
          * each genome plays several matches vs random opponents
          * matches are symmetric: A vs B and B vs A
      - Compute fitness from final board stats:
          * HP advantage
          * unit count advantage
          * win/loss with speed bonus
      - Let NEAT handle species, reproduction, and elitism.
    """

    def __init__(
        self,
        config_path: str,
        game_api: "HeadlessGameAPI",
        opponents_per_genome: int,
        max_workers: int,
        max_turns: int,
    ) -> None:
        self.config_path = config_path
        self.config = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            config_path,
        )

        self.base_game_api = game_api
        self.max_workers = max_workers
        self.opponents_per_genome = opponents_per_genome
        self.max_turns = max_turns

    # ============================================================
    # 🎯 Fitness Function
    # ============================================================

    # --- 3. Sigmoid scaling ---
    def sigmoid(self, x, k=1.0) -> float:
        return 1.0 / (1.0 + np.exp(-k * x))

    def softplus(self, x, beta=1.0):
        # numerically stable softplus
        return np.log1p(np.exp(-abs(beta * x))) + max(beta * x, 0)

    def compute_fitness(self, winner, played_turns, max_turns, stats):
        # --- 1. HP preservation & damage dealt ---
        curr_init_hp_ratio_1 = stats["hp1"] / stats["max_hp_team1"]
        curr_init_hp_ratio_2 = stats["hp2"] / stats["max_hp_team2"]

        # Damage inflicted (0–1)
        dmg_inflicted_1 = 1.0 - curr_init_hp_ratio_2
        dmg_inflicted_2 = 1.0 - curr_init_hp_ratio_1

        # --- 2. Unit preservation ---
        survived_initial_ratio_1 = stats["alive1"] / stats["initial_unit_count_team1"]
        survived_initial_ratio_2 = stats["alive2"] / stats["initial_unit_count_team2"]

        fitness1 = (
            curr_init_hp_ratio_1 + dmg_inflicted_1 * 10 + survived_initial_ratio_1
        )
        fitness2 = (
            curr_init_hp_ratio_2 + dmg_inflicted_2 * 10 + survived_initial_ratio_2
        )

        return self.softplus(fitness1), self.softplus(fitness2)

    # ============================================================
    # ⚔️ Match Execution (worker-side)
    # ============================================================
    @staticmethod
    def _run_match(
        config_path: str,
        game_api: "HeadlessGameAPI",
        genome_a_data: tuple[int, bytes],
        genome_b_data: tuple[int, bytes],
        max_turns: int,
    ) -> tuple[int, int, int | None, int, dict[str, float]]:
        """
        Runs a single match in an isolated process.

        Returns:
          (gid_a, gid_b, winner, played_turns, stats)
        """
        gid_a, g_a_bytes = genome_a_data
        gid_b, g_b_bytes = genome_b_data

        config = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            config_path,
        )

        # Rebuild genomes from pickled dicts
        genome_a = neat.DefaultGenome(gid_a)
        genome_b = neat.DefaultGenome(gid_b)
        genome_a.__dict__.update(pickle.loads(g_a_bytes))
        genome_b.__dict__.update(pickle.loads(g_b_bytes))

        sim = SelfPlaySimulator(config, game_api, max_turns=max_turns)
        # print(f"Match between: {gid_a} and {gid_b} starts.")
        winner, played_turns, stats = sim.play_match(genome_a, genome_b)

        return gid_a, gid_b, winner, played_turns, stats

    # ============================================================
    # 🧮 Genome Evaluation
    # ============================================================
    def eval_genomes(self, genomes, config) -> None:
        """
        Evaluate genomes via self-play.

        Strategy:
          - For each genome, pick up to `opponents_per_genome` random opponents.
          - Play 2 matches per opponent:
              A vs B   (A is team 1)
              B vs A   (B is team 1)
          - Accumulate zero-sum fitness contributions.
          - Normalize each genome's fitness by the number of matches played.
        """
        # Reset NEAT's fitness for this generation
        fitness_sums: dict[int, float] = {}
        match_counts: dict[int, int] = {}
        genome_data: dict[int, bytes] = {}

        for gid, genome in genomes:
            genome.fitness = 0.0
            fitness_sums[gid] = 0.0
            match_counts[gid] = 0
            # Store the internal dict of each genome
            genome_data[gid] = pickle.dumps(genome.__dict__)

        genome_ids = list(genome_data.keys())
        matches: list[tuple[tuple[int, bytes], tuple[int, bytes]]] = []

        # Build symmetric matches
        for gid_a in genome_ids:
            # All other genomes are potential opponents
            candidates = [gid for gid in genome_ids if gid != gid_a]
            if not candidates:
                continue

            k = min(self.opponents_per_genome, len(candidates))
            opponents = random.sample(candidates, k=k)

            for gid_b in opponents:
                g_a_data = (gid_a, genome_data[gid_a])
                g_b_data = (gid_b, genome_data[gid_b])

                # A as team 1 vs B as team 2
                matches.append((g_a_data, g_b_data))
                # B as team 1 vs A as team 2
                matches.append((g_b_data, g_a_data))

        # Parallel execution of matches
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for g_a_data, g_b_data in matches:
                game_clone = self.base_game_api.clone()
                futures.append(
                    executor.submit(
                        NeatTrainer._run_match,
                        self.config_path,
                        game_clone,
                        g_a_data,
                        g_b_data,
                        self.max_turns,
                    )
                )

            for f in as_completed(futures):
                gid_a, gid_b, winner, turns, stats = f.result()
                f_a, f_b = self.compute_fitness(winner, turns, self.max_turns, stats)

                fitness_sums[gid_a] += f_a
                fitness_sums[gid_b] += f_b
                match_counts[gid_a] += 1
                match_counts[gid_b] += 1

        # Normalize fitness by number of matches per genome
        for gid, genome in genomes:
            m = max(1, match_counts.get(gid, 0))
            genome.fitness = fitness_sums.get(gid, 0.0) / float(m)

    # ============================================================
    # 🚀 Evolution Loop
    # ============================================================
    def run(self, generations: int):
        """Run NEAT evolution with self-play."""
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

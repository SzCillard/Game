import pickle

import neat


class NEATTrainer:
    def __init__(self, config_path: str):
        self.config = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            config_path,
        )

    def eval_genomes(self, genomes, config):
        """Evaluate all genomes in one generation."""
        for genome_id, genome in genomes:
            net = neat.nn.FeedForwardNetwork.create(genome, config)
            fitness = self.simulate_game(net)
            genome.fitness = fitness

    def simulate_game(self, net):
        """
        Simulate a game round using the neural net as the decision policy.
        Replace with actual API interactions (GameAPI simulation).
        """
        total_score = 0
        # Example: call your simulation API to run AI vs random agent
        # and compute fitness based on survival, damage, or wins
        # total_score = simulate_match(net)
        return total_score

    def run(self, generations=50):
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

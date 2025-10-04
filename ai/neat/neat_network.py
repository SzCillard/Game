import pickle

import neat


class NEATNetwork:
    def __init__(self, genome_path: str, config_path: str):
        with open(genome_path, "rb") as f:
            genome = pickle.load(f)
        self.config = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            config_path,
        )
        self.net = neat.nn.FeedForwardNetwork.create(genome, self.config)

    def predict(self, inputs):
        """Feed game state features to the neural net, return action vector."""
        return self.net.activate(inputs)

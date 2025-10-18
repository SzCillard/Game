# ai/neat/neat_network.py
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

    @classmethod
    def from_genome(cls, genome, config):
        obj = cls.__new__(cls)
        obj.config = config
        obj.net = neat.nn.FeedForwardNetwork.create(genome, config)
        return obj

    def predict(self, inputs):
        """Feed game state features to the neural net, return action vector."""
        return self.net.activate(inputs)

# ai/neat/neat_network.py
import pickle

import neat


class NeatNetwork:
    """
    Wrapper for NEAT neural networks, now with multiprocessing-safe
    serialization and restoration.
    """

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

        self.genome = genome
        self.net = neat.nn.FeedForwardNetwork.create(genome, self.config)

    @classmethod
    def from_genome(cls, genome, config):
        obj = cls.__new__(cls)
        obj.config = config
        obj.genome = genome
        obj.net = neat.nn.FeedForwardNetwork.create(genome, config)
        return obj

    # -------------------------------------------------------------
    # Predict normally
    # -------------------------------------------------------------
    def predict(self, inputs):
        return self.net.activate(inputs)

    # -------------------------------------------------------------
    # SERIALIZE   (genome + genome_config only)
    # -------------------------------------------------------------
    def serialize(self) -> bytes:
        """
        Prepare minimal data needed to rebuild the NEAT network.

        We store:
        - genome internal dictionary
        - genome_config internal dictionary

        This is fully safe and NEAT-compatible.
        """
        payload = {
            "genome": self.genome.__dict__,
            "genome_config": self.config.genome_config.__dict__,
        }
        return pickle.dumps(payload)

    # -------------------------------------------------------------
    # RESTORE inside rollout workers
    # -------------------------------------------------------------
    @staticmethod
    def restore(data: bytes) -> "NeatNetwork":
        payload = pickle.loads(data)

        genome_dict = payload["genome"]
        genome_config_dict = payload["genome_config"]

        # Build dummy config
        dummy_config = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            None,
        )

        # Restore genome_config internals
        dummy_config.genome_config.__dict__.update(genome_config_dict)

        # Rebuild genome
        genome = neat.DefaultGenome(0)
        genome.__dict__.update(genome_dict)

        # Recreate NN
        net = neat.nn.FeedForwardNetwork.create(genome, dummy_config)

        # Wrap into NeatNetwork
        obj = NeatNetwork.__new__(NeatNetwork)
        obj.config = dummy_config
        obj.genome = genome
        obj.net = net

        return obj

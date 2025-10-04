from ai.base_agent import BaseAgent
from ai.neat.neat_network import NEATNetwork


class NEATAgent(BaseAgent):
    def __init__(self, genome_path: str, config_path: str):
        super().__init__()
        self.brain = NEATNetwork(genome_path, config_path)

    def choose_action(self, game_state):
        """
        Convert the current game state into neural net inputs,
        then interpret the outputs as an action (move/attack/etc.).
        """
        inputs = self.encode_state(game_state)
        outputs = self.brain.predict(inputs)

        # Example: interpret outputs
        # outputs = [move_up, move_down, attack, wait]
        action_idx = outputs.index(max(outputs))
        return self.decode_action(action_idx, game_state)

    def encode_state(self, game_state):
        """Extract numerical features for the neural network."""
        # Example features: unit HP, distance to enemy, terrain bonuses...
        return [0.5, 0.2, 1.0, 0.0]  # placeholder

    def decode_action(self, action_idx, game_state):
        """Convert output index back into a valid action."""
        actions = ["move_up", "move_down", "attack", "wait"]
        return {"type": actions[action_idx]}

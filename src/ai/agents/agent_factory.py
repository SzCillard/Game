from ai.agents.mcts_agent import MCTSAgent
from ai.agents.minimax_agent import MinimaxAgent
from ai.agents.neat_agent import NeatAgent
from ai.neat.neat_network import NeatNetwork
from utils.constants import AgentType


class AgentFactory:
    @staticmethod
    def create(agent_type: str, brain: NeatNetwork, **kwargs):
        """
        Creates agent instance based on name.
        """
        agent_type = agent_type.strip()

        if agent_type == AgentType.NEATAgent.value:
            return NeatAgent(brain)

        if agent_type == AgentType.MinimaxAgent.value:
            return MinimaxAgent(brain, **kwargs)

        if agent_type == AgentType.MCTSAgent.value:
            return MCTSAgent(brain, **kwargs)

        raise ValueError(f"Unknown agent type: {agent_type}")

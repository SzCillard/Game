from ai.agents.neat_agent import NeatAgent
from utils.constants import AgentType


class AgentFactory:
    @staticmethod
    def create(agent_type: str):
        """
        Creates agent instance based on name.
        """
        agent_type = agent_type.strip()

        if agent_type == AgentType.NEATAgent.value:
            return NeatAgent()
        """
        if agent_type == AgentType.MinimaxAgent.value:
            return MinimaxAgent()

        if agent_type == AgentType.MCTSAgent.value:
            return MCTSAgent()
        """
        raise ValueError(f"Unknown agent type: {agent_type}")

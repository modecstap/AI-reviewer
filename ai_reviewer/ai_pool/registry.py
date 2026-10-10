from ai_reviewer.properties import AgentDefinition

from .errors import DuplicateAgentError


class AgentRegistry:
    """Registered review agents in registration order."""

    def __init__(self) -> None:
        """Set up an empty registry."""
        self._agents: list[AgentDefinition] = []

    @property
    def agents(self) -> tuple[AgentDefinition, ...]:
        """
        Registered agents.

        :return: agents in registration order
        """
        return tuple(self._agents)

    def add(self, agent: AgentDefinition) -> None:
        """
        Register an agent.

        :param agent: agent to register

        :raises DuplicateAgentError: when ``agent.id`` is already registered
        """
        if any(known.id == agent.id for known in self._agents):
            raise DuplicateAgentError(
                f"agent {agent.id!r} is already registered"
            )
        self._agents.append(agent)

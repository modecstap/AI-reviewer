from pathlib import Path

from .entities import AgentDefinition
from .errors import DuplicateAgentError, OutputDirMismatchError


class AgentRegistry:
    """Registered review agents in registration order and their output dir."""

    def __init__(self) -> None:
        """Set up an empty registry."""
        self._agents: list[AgentDefinition] = []
        self._output_dir: Path | None = None

    @property
    def agents(self) -> tuple[AgentDefinition, ...]:
        """
        Registered agents.

        :return: agents in registration order
        """
        return tuple(self._agents)

    @property
    def output_dir(self) -> Path | None:
        """
        Output dir shared by all agents.

        :return: output dir; ``None`` while no agents are registered
        """
        return self._output_dir

    def add(self, agent: AgentDefinition, output_dir: Path) -> None:
        """
        Register an agent that writes into ``output_dir``.

        :param agent: agent to register
        :param output_dir: dir of numbered run dirs, shared by all agents

        :raises DuplicateAgentError: when ``agent.name`` is already registered
        :raises OutputDirMismatchError: when ``output_dir`` differs from the
            output dir of the agents added before
        """
        if any(known.name == agent.name for known in self._agents):
            raise DuplicateAgentError(
                f"agent {agent.name!r} is already registered"
            )
        if self._output_dir is None:
            self._output_dir = output_dir
        elif output_dir.resolve() != self._output_dir.resolve():
            raise OutputDirMismatchError(
                f"output_dir {str(output_dir)!r} differs from "
                f"{str(self._output_dir)!r}"
            )
        self._agents.append(agent)
